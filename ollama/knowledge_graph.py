"""
VorstersNV KnowledgeGraph — W7-02

Legt de structuur van een klant-codebase vast als gerichte graaf van code-entiteiten
(nodes) en hun onderlinge relaties (edges). Dient als kennisrepresentatie voor
architectuurinzichten, kwaliteitsbeoordelingen en visuele rapporten.

Use case:
    Tijdens een code-analyse sessie bouwt CodeGraphBuilder automatisch een
    KnowledgeGraph op via regex-analyse van Python- en Java-bronbestanden.
    De graaf vormt de basis voor:
      - Architectuurinzichten (koppelingen, afhankelijkheden, hotspots)
      - Cyclische afhankelijkheidsdetectie via iteratieve DFS
      - Mermaid-diagrammen in klant-rapporten
      - Koppelingsstatistieken voor kwaliteitsbeoordeling (ISO 25010)

JSONB serialisatie strategie:
    - Alle dataclass-velden worden omgezet naar JSON-primitieven
      (str, int, float, dict, list) — geen custom types in de output.
    - Enum-waarden worden opgeslagen als hun .value (string) voor
      leesbaarheid in de database en eenvoudige filtering via JSONB-operators.
    - UUID's worden als plain string opgeslagen; PostgreSQL kan deze later
      casten naar het uuid-type indien gewenst.
    - KnowledgeGraph.to_dict() produceert een dict die direct als JSONB-kolom
      opgeslagen kan worden via SQLAlchemy's JSONB type of json.dumps().
    - KnowledgeGraph.from_dict() reconstrueert alle Enum-types, dataclasses
      en de adjacency-structuur volledig correct vanuit het geserialiseerde dict.

Gebruik:
    graph = create_graph("project-uuid-hier")
    builder = get_graph_builder()
    bestanden = list(Path("src/").rglob("*.java")) + list(Path("src/").rglob("*.py"))
    graph = builder.bouw_graph("project-uuid-hier", bestanden)
    stats = graph.get_statistieken()
    mermaid = graph.exporteer_mermaid()
    data = graph.to_dict()                    # → opslaan als JSONB
    herlaad = KnowledgeGraph.from_dict(data)  # → laden vanuit JSONB
"""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Taal detectie ────────────────────────────────────────────────

_EXTENSIE_TAAL: dict[str, str] = {
    ".py":   "python",
    ".java": "java",
}


# ─── Enums ────────────────────────────────────────────────────────

class NodeType(str, Enum):
    """Type van een graph node — soort code-entiteit in de kennisgraaf."""

    KLASSE    = "klasse"
    FUNCTIE   = "functie"
    MODULE    = "module"
    PAKKET    = "pakket"
    INTERFACE = "interface"
    ENUM      = "enum"


class EdgeType(str, Enum):
    """Type van een graph edge — soort relatie tussen code-entiteiten."""

    ROEPT_AAN       = "roept_aan"
    IMPORTEERT      = "importeert"
    ERFT_VAN        = "erft_van"
    IMPLEMENTEERT   = "implementeert"
    BEVAT           = "bevat"
    AFHANKELIJK_VAN = "afhankelijk_van"


# ─── Dataclasses ──────────────────────────────────────────────────

@dataclass
class GraphNode:
    """Één node in de kennisgraaf — vertegenwoordigt een code-entiteit."""

    node_id:  str               # UUID-string
    naam:     str               # bijv. "OrderService"
    type:     NodeType
    bestand:  str               # relatief bestandspad als string
    lijn:     int               # regelnummer van de definitie (1-based)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSONB-compatibel dict."""
        return {
            "node_id":  self.node_id,
            "naam":     self.naam,
            "type":     self.type.value,
            "bestand":  self.bestand,
            "lijn":     self.lijn,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        """
        Deserialiseer vanuit een dict (bijv. uit JSONB).

        Args:
            data: Dict eerder geproduceerd door to_dict().

        Returns:
            Gereconstrueerde GraphNode met correct NodeType enum.

        Raises:
            ValueError: Als het type-veld een onbekende waarde bevat.
        """
        return cls(
            node_id=data["node_id"],
            naam=data["naam"],
            type=NodeType(data["type"]),
            bestand=data["bestand"],
            lijn=int(data["lijn"]),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class GraphEdge:
    """Één gerichte edge in de kennisgraaf — vertegenwoordigt een relatie."""

    edge_id:   str          # UUID-string
    van_node:  str          # node_id van het bronknooppunt
    naar_node: str          # node_id van het doelknooppunt
    type:      EdgeType
    gewicht:   float = 1.0  # koppelingssterkte 0.0–1.0
    metadata:  dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSONB-compatibel dict."""
        return {
            "edge_id":   self.edge_id,
            "van_node":  self.van_node,
            "naar_node": self.naar_node,
            "type":      self.type.value,
            "gewicht":   self.gewicht,
            "metadata":  self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphEdge:
        """
        Deserialiseer vanuit een dict (bijv. uit JSONB).

        Args:
            data: Dict eerder geproduceerd door to_dict().

        Returns:
            Gereconstrueerde GraphEdge met correct EdgeType enum.

        Raises:
            ValueError: Als het type-veld een onbekende waarde bevat.
        """
        return cls(
            edge_id=data["edge_id"],
            van_node=data["van_node"],
            naar_node=data["naar_node"],
            type=EdgeType(data["type"]),
            gewicht=float(data.get("gewicht", 1.0)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class KnowledgeGraphStats:
    """Statistische samenvatting van een KnowledgeGraph."""

    totaal_nodes:               int
    totaal_edges:               int
    nodes_per_type:             dict[str, int]
    edges_per_type:             dict[str, int]
    meest_gekoppelde_nodes:     list[tuple[str, int]]  # (naam, degree) top 10
    cyclische_afhankelijkheden: list[list[str]]         # gedetecteerde cycli (max 20)
    koppelingsdichtheid:        float                   # edges / (nodes*(nodes-1))

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSONB-compatibel dict."""
        return {
            "totaal_nodes":               self.totaal_nodes,
            "totaal_edges":               self.totaal_edges,
            "nodes_per_type":             self.nodes_per_type,
            "edges_per_type":             self.edges_per_type,
            "meest_gekoppelde_nodes": [
                {"naam": naam, "degree": degree}
                for naam, degree in self.meest_gekoppelde_nodes
            ],
            "cyclische_afhankelijkheden": self.cyclische_afhankelijkheden,
            "koppelingsdichtheid":        round(self.koppelingsdichtheid, 6),
        }


# ─── KnowledgeGraph ───────────────────────────────────────────────

class KnowledgeGraph:
    """
    Gerichte graaf die de structuur van een klant-codebase vastlegt.

    Nodes vertegenwoordigen code-entiteiten (klassen, functies, modules).
    Edges vertegenwoordigen gerichte relaties (imports, overerving, aanroepen).

    Attributen:
        project_id: UUID-string die deze graaf koppelt aan een ClientProjectSpace.
        _nodes:     Intern woordenboek node_id → GraphNode.
        _edges:     Intern woordenboek edge_id → GraphEdge.
        _adjacency: Ongerichte burenlijst node_id → set van buur node_ids.
                    Wordt gebruikt voor graad-berekeningen; voor DFS cycle
                    detection wordt een gerichte adjacency on-the-fly gebouwd.
    """

    def __init__(self, project_id: str) -> None:
        self.project_id: str                    = project_id
        self._nodes:     dict[str, GraphNode]   = {}
        self._edges:     dict[str, GraphEdge]   = {}
        self._adjacency: dict[str, set[str]]    = {}

    # ── Node beheer ───────────────────────────────────────────────

    def add_node(
        self,
        naam:     str,
        type:     NodeType,
        bestand:  str,
        lijn:     int,
        metadata: dict[str, Any] | None = None,
    ) -> GraphNode:
        """
        Voeg een nieuwe node toe aan de graaf.

        Args:
            naam:     Weergavenaam van de entiteit (bijv. "OrderService").
            type:     NodeType enum waarde.
            bestand:  Relatief bestandspad waar de entiteit gedefinieerd is.
            lijn:     Regelnummer van de definitie (1-based).
            metadata: Optioneel woordenboek met extra context
                      (bijv. {"methoden": 12, "complexiteit": "HOOG"}).

        Returns:
            De nieuw aangemaakte GraphNode.
        """
        node = GraphNode(
            node_id=str(uuid.uuid4()),
            naam=naam,
            type=type,
            bestand=bestand,
            lijn=lijn,
            metadata=metadata or {},
        )
        self._nodes[node.node_id] = node
        self._adjacency.setdefault(node.node_id, set())
        logger.debug(
            "Node toegevoegd: %s (%s) in %s:%d",
            naam, type.value, bestand, lijn,
        )
        return node

    def get_node(self, node_id: str) -> GraphNode | None:
        """
        Haal een node op via zijn UUID.

        Args:
            node_id: UUID-string van de node.

        Returns:
            GraphNode als gevonden, anders None.
        """
        return self._nodes.get(node_id)

    def find_nodes(self, naam_patroon: str) -> list[GraphNode]:
        """
        Zoek nodes op naam (case-insensitive contains).

        Args:
            naam_patroon: Zoekstring — elk deel van de naam is voldoende.
                          Bijv. "service" vindt "OrderService" en "PaymentService".

        Returns:
            Lijst van GraphNode objecten waarvan de naam het patroon bevat.
            Lege lijst als niets gevonden.
        """
        patroon_lower = naam_patroon.lower()
        return [
            node for node in self._nodes.values()
            if patroon_lower in node.naam.lower()
        ]

    # ── Edge beheer ───────────────────────────────────────────────

    def add_edge(
        self,
        van_node_id:  str,
        naar_node_id: str,
        type:         EdgeType,
        gewicht:      float = 1.0,
        metadata:     dict[str, Any] | None = None,
    ) -> GraphEdge:
        """
        Voeg een nieuwe gerichte edge toe aan de graaf.

        Beide node_ids hoeven niet te bestaan (externe entiteiten zoals
        third-party imports worden ondersteund). Het gewicht wordt geclamped
        naar het interval [0.0, 1.0].

        Args:
            van_node_id:  node_id van het bronknooppunt.
            naar_node_id: node_id van het doelknooppunt.
            type:         EdgeType enum waarde.
            gewicht:      Koppelingssterkte 0.0–1.0 (standaard 1.0).
            metadata:     Optioneel woordenboek met extra context.

        Returns:
            De nieuw aangemaakte GraphEdge.
        """
        edge = GraphEdge(
            edge_id=str(uuid.uuid4()),
            van_node=van_node_id,
            naar_node=naar_node_id,
            type=type,
            gewicht=max(0.0, min(1.0, gewicht)),
            metadata=metadata or {},
        )
        self._edges[edge.edge_id] = edge

        # Ongerichte adjacency bijhouden voor graad-berekeningen
        self._adjacency.setdefault(van_node_id, set()).add(naar_node_id)
        self._adjacency.setdefault(naar_node_id, set()).add(van_node_id)

        logger.debug(
            "Edge toegevoegd: %s →[%s]→ %s (gewicht=%.2f)",
            van_node_id[:8], type.value, naar_node_id[:8], edge.gewicht,
        )
        return edge

    def get_edges_for_node(self, node_id: str) -> list[GraphEdge]:
        """
        Haal alle edges op die bij een node betrokken zijn (in- én uitgaand).

        Args:
            node_id: UUID-string van de node.

        Returns:
            Lijst van GraphEdge objecten. Leeg als node niet bestaat of
            geen edges heeft.
        """
        return [
            edge for edge in self._edges.values()
            if edge.van_node == node_id or edge.naar_node == node_id
        ]

    # ── Statistieken ──────────────────────────────────────────────

    def _detecteer_cycli(self) -> list[list[str]]:
        """
        Detecteer cyclische afhankelijkheden via iteratieve DFS (three-color marking).

        Algoritme (Tarjan-stijl three-color DFS):
          - WHITE (0): node nog niet bezocht
          - GRAY  (1): node in verwerking — op het huidige DFS-pad
          - BLACK (2): node volledig afgerond — alle buren verwerkt

        Een cyclus wordt gevonden wanneer we vanuit een GRAY node een andere
        GRAY node bereiken (die dus een voorouder is op het huidige pad).

        De iteratieve implementatie gebruikt twee stack-elementen per node:
          (True,  node_id) → pre-order:  node betreden, kleur GRAY, pad uitbreiden
          (False, node_id) → post-order: node verlaten, kleur BLACK, pad inkorten

        Duplicate pushes (mogelijk bij meerdere inkomende edges) worden
        afgevangen door de kleur-check bij het poppen van (True, node_id).

        Args: Geen — werkt op self._nodes en self._edges.

        Returns:
            Lijst van cycli (max 20). Elke cyclus is een lijst van node-namen
            waarbij de eerste naam ook als laatste herhaald wordt voor duidelijkheid
            (bijv. ["A", "B", "C", "A"]).
        """
        MAX_CYCLI = 20
        WHITE, GRAY, BLACK = 0, 1, 2

        # Gerichte adjacency vanuit edges (alleen bestaande nodes)
        gerichte_adj: dict[str, list[str]] = {nid: [] for nid in self._nodes}
        for edge in self._edges.values():
            if edge.van_node in self._nodes and edge.naar_node in self._nodes:
                gerichte_adj[edge.van_node].append(edge.naar_node)

        color: dict[str, int] = {nid: WHITE for nid in self._nodes}
        cycli: list[list[str]] = []

        for start_node in list(self._nodes.keys()):
            if color[start_node] != WHITE or len(cycli) >= MAX_CYCLI:
                continue

            # Iteratieve DFS met expliciet pad
            pad: list[str] = []
            # Stack: (entering: bool, node_id: str)
            stack: list[tuple[bool, str]] = [(True, start_node)]

            while stack and len(cycli) < MAX_CYCLI:
                entering, node = stack.pop()

                if not entering:
                    # Post-order: node volledig verwerkt → kleur BLACK, pad inkorten
                    color[node] = BLACK
                    if pad and pad[-1] == node:
                        pad.pop()
                    continue

                if color[node] != WHITE:
                    # Duplicate push (meerdere ouders) of al verwerkt — overslaan
                    # Geen (False, node) pushen want dat staat al in de stack
                    continue

                # Pre-order: node betreden → kleur GRAY, voeg toe aan pad
                color[node] = GRAY
                pad.append(node)
                # Registreer de post-order cleanup
                stack.append((False, node))

                # Verwerk buren in omgekeerde volgorde voor consistente DFS-volgorde
                for buur in reversed(gerichte_adj.get(node, [])):
                    if color[buur] == GRAY:
                        # Cyclus gevonden: buur is een voorouder op het huidige pad
                        if buur in pad:
                            idx = pad.index(buur)
                            cyclus_ids = pad[idx:] + [buur]
                            cyclus_namen = [
                                self._nodes[n].naam
                                for n in cyclus_ids
                                if n in self._nodes
                            ]
                            if cyclus_namen and cyclus_namen not in cycli:
                                cycli.append(cyclus_namen)
                    elif color[buur] == WHITE:
                        stack.append((True, buur))
                    # BLACK: al volledig afgerond — geen nieuwe cyclus mogelijk

        logger.debug(
            "Cycle detection afgerond voor project %s: %d cycli gevonden",
            self.project_id, len(cycli),
        )
        return cycli

    def get_statistieken(self) -> KnowledgeGraphStats:
        """
        Bereken en retourneer een statistische samenvatting van de graaf.

        Berekeningen:
        - nodes_per_type / edges_per_type: telling per enum-waarde
        - meest_gekoppelde_nodes: top 10 op totale graad (inkomend + uitgaand),
          waarbij elke edge apart geteld wordt (niet via adjacency-set-grootte)
        - cyclische_afhankelijkheden: DFS cycle detection, max 20 cycli
        - koppelingsdichtheid: edges / (nodes * (nodes-1)) voor gerichte graaf;
          0.0 als er ≤ 1 node is

        Returns:
            KnowledgeGraphStats dataclass met alle statistieken.
        """
        totaal_nodes = len(self._nodes)
        totaal_edges = len(self._edges)

        # Nodes per type
        nodes_per_type: dict[str, int] = {}
        for node in self._nodes.values():
            key = node.type.value
            nodes_per_type[key] = nodes_per_type.get(key, 0) + 1

        # Edges per type
        edges_per_type: dict[str, int] = {}
        for edge in self._edges.values():
            key = edge.type.value
            edges_per_type[key] = edges_per_type.get(key, 0) + 1

        # Graad per node: tel elke edge apart (in + out afzonderlijk)
        graad: dict[str, int] = {nid: 0 for nid in self._nodes}
        for edge in self._edges.values():
            if edge.van_node in graad:
                graad[edge.van_node] += 1
            if edge.naar_node in graad:
                graad[edge.naar_node] += 1

        # Top 10 meest gekoppelde nodes (alleen nodes met minstens 1 edge)
        gesorteerd = sorted(
            [
                (self._nodes[nid].naam, deg)
                for nid, deg in graad.items()
                if deg > 0
            ],
            key=lambda x: x[1],
            reverse=True,
        )
        meest_gekoppeld: list[tuple[str, int]] = gesorteerd[:10]

        # Cyclische afhankelijkheden via DFS
        cycli = self._detecteer_cycli()

        # Koppelingsdichtheid voor een gerichte graaf: edges / (n * (n-1))
        if totaal_nodes > 1:
            dichtheid = round(totaal_edges / (totaal_nodes * (totaal_nodes - 1)), 6)
        else:
            dichtheid = 0.0

        stats = KnowledgeGraphStats(
            totaal_nodes=totaal_nodes,
            totaal_edges=totaal_edges,
            nodes_per_type=nodes_per_type,
            edges_per_type=edges_per_type,
            meest_gekoppelde_nodes=meest_gekoppeld,
            cyclische_afhankelijkheden=cycli,
            koppelingsdichtheid=dichtheid,
        )
        logger.info(
            "Statistieken berekend: project=%s, nodes=%d, edges=%d, "
            "cycli=%d, dichtheid=%.4f",
            self.project_id, totaal_nodes, totaal_edges, len(cycli), dichtheid,
        )
        return stats

    # ── Serialisatie ──────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """
        Serialiseer de volledige graaf naar een JSONB-compatibel woordenboek.

        Alle nodes en edges worden als geneste dicts opgenomen. Enum-waarden
        als strings, UUIDs als strings. Het resultaat is direct opslaan-baar
        in een PostgreSQL JSONB-kolom.

        Returns:
            dict met sleutels: project_id (str), nodes (dict), edges (dict).
        """
        return {
            "project_id": self.project_id,
            "nodes": {nid: node.to_dict() for nid, node in self._nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self._edges.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraph:
        """
        Deserialiseer een KnowledgeGraph vanuit een dict (bijv. uit JSONB).

        Reconstrueert alle NodeType- en EdgeType-enums en herstelt de volledige
        adjacency-structuur vanuit de edges zodat de graaf direct bruikbaar is.

        Args:
            data: Dict eerder geproduceerd door to_dict().

        Returns:
            Volledig gereconstrueerde KnowledgeGraph.

        Raises:
            KeyError:   Als verplichte velden (project_id, nodes, edges) ontbreken.
            ValueError: Als een enum-waarde in nodes of edges onbekend is.
        """
        graph = cls(project_id=data["project_id"])

        for node_data in data.get("nodes", {}).values():
            node = GraphNode.from_dict(node_data)
            graph._nodes[node.node_id] = node
            graph._adjacency.setdefault(node.node_id, set())

        for edge_data in data.get("edges", {}).values():
            edge = GraphEdge.from_dict(edge_data)
            graph._edges[edge.edge_id] = edge
            # Herstel ongerichte adjacency
            graph._adjacency.setdefault(edge.van_node, set()).add(edge.naar_node)
            graph._adjacency.setdefault(edge.naar_node, set()).add(edge.van_node)

        logger.debug(
            "KnowledgeGraph herladen: project=%s, %d nodes, %d edges",
            graph.project_id, len(graph._nodes), len(graph._edges),
        )
        return graph

    # ── Mermaid export ────────────────────────────────────────────

    def exporteer_mermaid(self) -> str:
        """
        Genereer een Mermaid-diagramstring van de graaf.

        Formaat:
            graph TD
                nABCD1234EF56["OrderService\\n(klasse)"]
                nABCD1234EF56 -->|roept_aan| nEF567890ABCD

        Beperkt tot de 50 zwaarste edges (op gewicht descending) om grote
        diagrammen leesbaar te houden. Alleen nodes die bij die edges
        betrokken zijn, worden opgenomen in de node-declaraties. Als er
        geen edges zijn, worden de eerste 50 nodes getoond.

        Returns:
            Mermaid-compatibele multi-line string klaar voor rendering
            in een Markdown-codeblok of Mermaid Live Editor.
        """
        # Selecteer de 50 zwaarste edges
        gesorteerde_edges = sorted(
            self._edges.values(),
            key=lambda e: e.gewicht,
            reverse=True,
        )[:50]

        # Verzamel betrokken node-IDs
        betrokken_ids: set[str] = set()
        for edge in gesorteerde_edges:
            betrokken_ids.add(edge.van_node)
            betrokken_ids.add(edge.naar_node)

        # Als er geen edges zijn: toon de eerste 50 nodes
        if not betrokken_ids:
            betrokken_ids = set(list(self._nodes.keys())[:50])

        def _mermaid_id(node_id: str) -> str:
            """Maak een veilig alfanumeriek Mermaid-ID van een UUID."""
            # Prefix 'n' zodat ID niet met cijfer begint; 12 hex-tekens na prefix
            return "n" + node_id.replace("-", "")[:12]

        def _mermaid_label(node: GraphNode) -> str:
            """Genereer node-declaratie met naam en type op twee regels."""
            naam_veilig = node.naam.replace('"', "'")
            mid = _mermaid_id(node.node_id)
            return f'{mid}["{naam_veilig}\\n({node.type.value})"]'

        regels: list[str] = ["graph TD"]

        # Node declaraties (gesorteerd voor deterministische output)
        for node_id in sorted(betrokken_ids):
            node = self._nodes.get(node_id)
            if node:
                regels.append(f"    {_mermaid_label(node)}")

        # Edge declaraties
        for edge in gesorteerde_edges:
            van_node  = self._nodes.get(edge.van_node)
            naar_node = self._nodes.get(edge.naar_node)
            if van_node and naar_node:
                van_mid  = _mermaid_id(edge.van_node)
                naar_mid = _mermaid_id(edge.naar_node)
                regels.append(f"    {van_mid} -->|{edge.type.value}| {naar_mid}")

        mermaid_str = "\n".join(regels)
        logger.debug(
            "Mermaid export: project=%s, %d nodes, %d edges in diagram",
            self.project_id, len(betrokken_ids), len(gesorteerde_edges),
        )
        return mermaid_str


# ─── CodeGraphBuilder ─────────────────────────────────────────────

class CodeGraphBuilder:
    """
    Bouwt automatisch een KnowledgeGraph op basis van broncodebestanden.

    Analyseert Python- en Java-bestanden via reguliere expressies (geen AST
    parser vereist). Andere bestandsextensies worden overgeslagen.

    Werkwijze per bestand:
      1. Maak een MODULE-node aan voor het bestand zelf
      2. Extraheer klassen, functies, interfaces en enums via regex
      3. Voeg BEVAT-edges toe van module naar elke gevonden entiteit
      4. Extraheer import-statements → IMPORTEERT-edges
      5. Extraheer overerving/implementatie → ERFT_VAN / IMPLEMENTEERT edges

    Duplicate-preventie:
      - _zoek_of_maak_node() hergebruikt bestaande nodes op naam+type
      - _voeg_edge_toe_indien_nieuw() slaat identieke edges (van/naar/type) over
    """

    # ─── Python regex patronen ────────────────────────────────────

    # Top-level klassen (geen inspringing vóór 'class')
    _PY_KLASSE = re.compile(r"^class\s+(\w+)", re.MULTILINE)

    # Top-level functies (geen inspringing, ook async def)
    _PY_FUNCTIE = re.compile(r"^(?:async\s+)?def\s+(\w+)", re.MULTILINE)

    # import os.path  →  module "os.path"
    _PY_IMPORT = re.compile(r"^import\s+([\w\.]+)", re.MULTILINE)

    # from X import Y  →  module "X"
    _PY_FROM_IMPORT = re.compile(r"^from\s+([\w\.]+)\s+import", re.MULTILINE)

    # ─── Java regex patronen ──────────────────────────────────────

    # class Naam [extends X] [implements A, B] {
    # Ondersteunt ook generics in implements via [<>] in de tekenklasse
    _JAVA_KLASSE = re.compile(
        r"\bclass\s+(\w+)"
        r"(?:\s+extends\s+(\w+))?"
        r"(?:\s+implements\s+([\w\s,<>]+?))?(?=\s*\{)",
        re.MULTILINE,
    )

    # interface Naam
    _JAVA_INTERFACE = re.compile(r"\binterface\s+(\w+)", re.MULTILINE)

    # enum Naam
    _JAVA_ENUM = re.compile(r"\benum\s+(\w+)", re.MULTILINE)

    # import [static] com.example.ClassName[.*];
    _JAVA_IMPORT = re.compile(
        r"^import\s+(?:static\s+)?([\w\.]+)(?:\.\*)?;",
        re.MULTILINE,
    )

    # ─── Hulpmethoden ─────────────────────────────────────────────

    @staticmethod
    def _lijn_voor_pos(tekst: str, pos: int) -> int:
        """
        Bereken het regelnummer (1-based) voor een tekst-positie.

        Args:
            tekst: De volledige bestandstekst.
            pos:   Teken-positie in de tekst (0-based, van re.Match.start()).

        Returns:
            Regelnummer (1-based).
        """
        return tekst.count("\n", 0, pos) + 1

    def _zoek_of_maak_node(
        self,
        naam:     str,
        type_:    NodeType,
        bestand:  str,
        lijn:     int,
        graph:    KnowledgeGraph,
        metadata: dict[str, Any] | None = None,
    ) -> GraphNode:
        """
        Vind een bestaande node op exacte naam + type, of maak een nieuwe aan.

        Voorkomt duplicate nodes bij herhaalde analyse van dezelfde entiteiten
        (bijv. een klasse die in meerdere bestanden wordt geïmporteerd).

        Args:
            naam:     Exacte naam van de entiteit.
            type_:    NodeType van de entiteit.
            bestand:  Bestandspad voor een nieuwe node.
            lijn:     Regelnummer voor een nieuwe node.
            graph:    De KnowledgeGraph om in te zoeken / aan toe te voegen.
            metadata: Optionele metadata voor een nieuwe node.

        Returns:
            Bestaande of nieuw aangemaakte GraphNode.
        """
        for node in graph.find_nodes(naam):
            if node.naam == naam and node.type == type_:
                return node
        return graph.add_node(naam, type_, bestand, lijn, metadata or {})

    def _voeg_edge_toe_indien_nieuw(
        self,
        van_node_id:  str,
        naar_node_id: str,
        type_:        EdgeType,
        graph:        KnowledgeGraph,
        gewicht:      float = 1.0,
        metadata:     dict[str, Any] | None = None,
    ) -> GraphEdge | None:
        """
        Voeg een edge toe als er nog geen identieke edge bestaat (van/naar/type).

        Vermijdt duplicate edges bij herhaalde import-statements of wanneer
        meerdere bestanden dezelfde afhankelijkheid declareren.

        Args:
            van_node_id:  Bron-node UUID.
            naar_node_id: Doel-node UUID.
            type_:        EdgeType van de relatie.
            graph:        De KnowledgeGraph.
            gewicht:      Koppelingssterkte (standaard 1.0).
            metadata:     Optionele metadata.

        Returns:
            Nieuw aangemaakte GraphEdge, of None als het een duplicaat is.
        """
        for edge in graph._edges.values():
            if (
                edge.van_node == van_node_id
                and edge.naar_node == naar_node_id
                and edge.type == type_
            ):
                return None  # Duplicaat — overgeslagen
        return graph.add_edge(van_node_id, naar_node_id, type_, gewicht, metadata)

    # ─── Taal-specifieke analysers ────────────────────────────────

    def analyseer_python_bestand(
        self,
        bestand: Path,
        graph:   KnowledgeGraph,
    ) -> None:
        """
        Analyseer een Python-bestand en voeg nodes en edges toe aan de graaf.

        Extraheert:
          - MODULE node voor het bestand (stem van de bestandsnaam)
          - KLASSE nodes voor top-level class-definities + BEVAT edges
          - FUNCTIE nodes voor top-level def-definities + BEVAT edges
            (async def inbegrepen; ingesprongen methodes worden overgeslagen)
          - MODULE nodes voor geïmporteerde modules (import X) + IMPORTEERT edges
          - MODULE nodes voor from-imports (from X import Y) + IMPORTEERT edges

        Args:
            bestand: Pad naar het .py bronbestand (moet leesbaar zijn).
            graph:   De KnowledgeGraph om nodes en edges aan toe te voegen.
        """
        try:
            tekst = bestand.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Kan Python-bestand niet lezen: %s — %s", bestand, exc)
            return

        bestand_str = str(bestand)
        module_naam = bestand.stem  # bijv. "order_service" voor order_service.py

        # MODULE node voor dit bestand
        module_node = self._zoek_of_maak_node(
            naam=module_naam,
            type_=NodeType.MODULE,
            bestand=bestand_str,
            lijn=1,
            graph=graph,
            metadata={"bestandsnaam": bestand.name, "taal": "python"},
        )

        # Top-level klassen (geen inspringing dankzij ^ in MULTILINE)
        for match in self._PY_KLASSE.finditer(tekst):
            klasse_naam = match.group(1)
            lijn = self._lijn_voor_pos(tekst, match.start())
            klasse_node = self._zoek_of_maak_node(
                naam=klasse_naam,
                type_=NodeType.KLASSE,
                bestand=bestand_str,
                lijn=lijn,
                graph=graph,
                metadata={"taal": "python"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=klasse_node.node_id,
                type_=EdgeType.BEVAT,
                graph=graph,
            )
            logger.debug(
                "Python klasse: %s in %s:%d", klasse_naam, bestand.name, lijn,
            )

        # Top-level functies (geen inspringing dankzij ^ in MULTILINE)
        for match in self._PY_FUNCTIE.finditer(tekst):
            func_naam = match.group(1)
            lijn = self._lijn_voor_pos(tekst, match.start())
            func_node = self._zoek_of_maak_node(
                naam=func_naam,
                type_=NodeType.FUNCTIE,
                bestand=bestand_str,
                lijn=lijn,
                graph=graph,
                metadata={"taal": "python"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=func_node.node_id,
                type_=EdgeType.BEVAT,
                graph=graph,
            )

        # import X.Y.Z  →  MODULE node voor "X.Y.Z"
        for match in self._PY_IMPORT.finditer(tekst):
            import_naam = match.group(1)
            import_node = self._zoek_of_maak_node(
                naam=import_naam,
                type_=NodeType.MODULE,
                bestand="<extern>",
                lijn=0,
                graph=graph,
                metadata={"extern": True, "taal": "python"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=import_node.node_id,
                type_=EdgeType.IMPORTEERT,
                graph=graph,
            )

        # from X.Y import Z  →  MODULE node voor "X.Y"
        for match in self._PY_FROM_IMPORT.finditer(tekst):
            from_naam = match.group(1)
            from_node = self._zoek_of_maak_node(
                naam=from_naam,
                type_=NodeType.MODULE,
                bestand="<extern>",
                lijn=0,
                graph=graph,
                metadata={"extern": True, "taal": "python"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=from_node.node_id,
                type_=EdgeType.IMPORTEERT,
                graph=graph,
            )

        logger.info(
            "Python-bestand geanalyseerd: %s → project %s",
            bestand.name, graph.project_id,
        )

    def analyseer_java_bestand(
        self,
        bestand: Path,
        graph:   KnowledgeGraph,
    ) -> None:
        """
        Analyseer een Java-bestand en voeg nodes en edges toe aan de graaf.

        Extraheert:
          - MODULE node voor het bestand (stem van de bestandsnaam)
          - KLASSE nodes voor class-definities + BEVAT edges
          - ERFT_VAN edges voor extends-relaties
          - IMPLEMENTEERT edges voor implements-relaties
            (generics zoals List<T> worden gestript)
          - INTERFACE nodes voor interface-definities + BEVAT edges
          - ENUM nodes voor enum-definities + BEVAT edges
          - PAKKET nodes voor import-statements + IMPORTEERT edges
            (volledig gekwalificeerd pad wordt als pakket-naam gebruikt)

        Args:
            bestand: Pad naar het .java bronbestand (moet leesbaar zijn).
            graph:   De KnowledgeGraph om nodes en edges aan toe te voegen.
        """
        try:
            tekst = bestand.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Kan Java-bestand niet lezen: %s — %s", bestand, exc)
            return

        bestand_str = str(bestand)
        module_naam = bestand.stem  # bijv. "OrderService" voor OrderService.java

        # MODULE node voor dit bestand
        module_node = self._zoek_of_maak_node(
            naam=module_naam,
            type_=NodeType.MODULE,
            bestand=bestand_str,
            lijn=1,
            graph=graph,
            metadata={"bestandsnaam": bestand.name, "taal": "java"},
        )

        # Klassen met optionele extends en implements
        for match in self._JAVA_KLASSE.finditer(tekst):
            klasse_naam   = match.group(1)
            extends_naam  = match.group(2)   # None als afwezig
            impl_str      = match.group(3)   # None als afwezig
            lijn = self._lijn_voor_pos(tekst, match.start())

            klasse_node = self._zoek_of_maak_node(
                naam=klasse_naam,
                type_=NodeType.KLASSE,
                bestand=bestand_str,
                lijn=lijn,
                graph=graph,
                metadata={"taal": "java"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=klasse_node.node_id,
                type_=EdgeType.BEVAT,
                graph=graph,
            )
            logger.debug(
                "Java klasse: %s in %s:%d", klasse_naam, bestand.name, lijn,
            )

            # extends X  →  ERFT_VAN
            if extends_naam:
                ouder_node = self._zoek_of_maak_node(
                    naam=extends_naam,
                    type_=NodeType.KLASSE,
                    bestand="<extern>",
                    lijn=0,
                    graph=graph,
                    metadata={"extern": True, "taal": "java"},
                )
                self._voeg_edge_toe_indien_nieuw(
                    van_node_id=klasse_node.node_id,
                    naar_node_id=ouder_node.node_id,
                    type_=EdgeType.ERFT_VAN,
                    graph=graph,
                )

            # implements A, B<T>, C  →  IMPLEMENTEERT (generics gestript)
            if impl_str:
                interfaces = [
                    naam.strip().split("<")[0].strip()
                    for naam in impl_str.split(",")
                    if naam.strip()
                ]
                for iface_naam in interfaces:
                    if not iface_naam:
                        continue
                    iface_node = self._zoek_of_maak_node(
                        naam=iface_naam,
                        type_=NodeType.INTERFACE,
                        bestand="<extern>",
                        lijn=0,
                        graph=graph,
                        metadata={"extern": True, "taal": "java"},
                    )
                    self._voeg_edge_toe_indien_nieuw(
                        van_node_id=klasse_node.node_id,
                        naar_node_id=iface_node.node_id,
                        type_=EdgeType.IMPLEMENTEERT,
                        graph=graph,
                    )

        # Interfaces
        for match in self._JAVA_INTERFACE.finditer(tekst):
            iface_naam = match.group(1)
            lijn = self._lijn_voor_pos(tekst, match.start())
            iface_node = self._zoek_of_maak_node(
                naam=iface_naam,
                type_=NodeType.INTERFACE,
                bestand=bestand_str,
                lijn=lijn,
                graph=graph,
                metadata={"taal": "java"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=iface_node.node_id,
                type_=EdgeType.BEVAT,
                graph=graph,
            )

        # Enums
        for match in self._JAVA_ENUM.finditer(tekst):
            enum_naam = match.group(1)
            lijn = self._lijn_voor_pos(tekst, match.start())
            enum_node = self._zoek_of_maak_node(
                naam=enum_naam,
                type_=NodeType.ENUM,
                bestand=bestand_str,
                lijn=lijn,
                graph=graph,
                metadata={"taal": "java"},
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=enum_node.node_id,
                type_=EdgeType.BEVAT,
                graph=graph,
            )

        # Import statements  →  PAKKET nodes + IMPORTEERT edges
        # Gebruik het volledig gekwalificeerde pad als pakket-naam
        # (bijv. "com.vorsters.order" voor "com.vorsters.order.OrderService")
        for match in self._JAVA_IMPORT.finditer(tekst):
            import_pad = match.group(1)
            # Pakket = alles vóór de laatste component
            if "." in import_pad:
                pakket_naam = import_pad.rsplit(".", 1)[0]
            else:
                pakket_naam = import_pad

            pakket_node = self._zoek_of_maak_node(
                naam=pakket_naam,
                type_=NodeType.PAKKET,
                bestand="<extern>",
                lijn=0,
                graph=graph,
                metadata={
                    "extern": True,
                    "taal": "java",
                    "volledig_pad": import_pad,
                },
            )
            self._voeg_edge_toe_indien_nieuw(
                van_node_id=module_node.node_id,
                naar_node_id=pakket_node.node_id,
                type_=EdgeType.IMPORTEERT,
                graph=graph,
            )

        logger.info(
            "Java-bestand geanalyseerd: %s → project %s",
            bestand.name, graph.project_id,
        )

    def bouw_graph(
        self,
        project_id: str,
        bestanden:  list[Path],
    ) -> KnowledgeGraph:
        """
        Bouw een KnowledgeGraph voor een project door alle opgegeven bestanden
        te analyseren.

        Detecteert de programmeertaal op basis van de bestandsextensie en roept
        de juiste analyseer-methode aan. Bestanden met niet-ondersteunde extensies
        worden overgeslagen (één debug-log per unieke extensie). De gemaakte graaf
        wordt geregistreerd in de module-level registry via create_graph().

        Args:
            project_id: UUID-string die de graaf koppelt aan een consultancy project.
            bestanden:  Lijst van Path-objecten naar te analyseren bronbestanden.

        Returns:
            Ingevulde KnowledgeGraph met alle gevonden nodes en edges.
            Een lege graaf (geen nodes/edges) als bestanden leeg is.
        """
        graph = create_graph(project_id)
        niet_ondersteund_gezien: set[str] = set()

        for bestand in bestanden:
            suffix = bestand.suffix.lower()
            if suffix == ".py":
                self.analyseer_python_bestand(bestand, graph)
            elif suffix == ".java":
                self.analyseer_java_bestand(bestand, graph)
            else:
                if suffix not in niet_ondersteund_gezien:
                    logger.debug(
                        "Extensie niet ondersteund voor graph-analyse: "
                        "%s (overgeslagen)",
                        suffix or "(geen extensie)",
                    )
                    niet_ondersteund_gezien.add(suffix)

        logger.info(
            "bouw_graph afgerond: project=%s, %d bestanden verwerkt, "
            "%d nodes, %d edges",
            project_id,
            len(bestanden),
            len(graph._nodes),
            len(graph._edges),
        )
        return graph


# ─── Module-level Registry ────────────────────────────────────────

_graphs:  dict[str, KnowledgeGraph]      = {}
_builder: Optional[CodeGraphBuilder]     = None


def create_graph(project_id: str) -> KnowledgeGraph:
    """
    Maak een nieuwe lege KnowledgeGraph aan en registreer hem.

    Als er al een graaf bestaat voor dit project_id, wordt deze overschreven.
    Dit is het verwachte gedrag bij het herbouwen van een graaf na codewijzigingen.

    Args:
        project_id: UUID-string die de graaf koppelt aan een ClientProjectSpace.

    Returns:
        Nieuwe, lege KnowledgeGraph voor het opgegeven project.
    """
    graph = KnowledgeGraph(project_id=project_id)
    _graphs[project_id] = graph
    logger.info("KnowledgeGraph aangemaakt voor project: %s", project_id)
    return graph


def get_graph(project_id: str) -> KnowledgeGraph | None:
    """
    Haal een bestaande KnowledgeGraph op via project_id.

    Args:
        project_id: UUID-string van het project.

    Returns:
        KnowledgeGraph als gevonden in de registry, anders None.
    """
    graph = _graphs.get(project_id)
    if graph is None:
        logger.debug("Geen KnowledgeGraph gevonden voor project: %s", project_id)
    return graph


def get_graph_builder() -> CodeGraphBuilder:
    """
    Singleton accessor voor CodeGraphBuilder.

    De builder heeft geen mutable state buiten methode-aanroepen en is
    thread-safe te hergebruiken over meerdere bouw_graph()-aanroepen.

    Returns:
        De gedeelde CodeGraphBuilder instantie.
    """
    global _builder
    if _builder is None:
        _builder = CodeGraphBuilder()
        logger.debug("CodeGraphBuilder singleton aangemaakt")
    return _builder
