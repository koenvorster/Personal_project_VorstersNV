"""
VorstersNV Recommendation Engine — W8-03

Genereert next-best-action aanbevelingen voor klantprojecten op basis van
KnowledgeGraph analyse, sector-benchmarks en rule-based logica voor de
Belgische KMO-markt.

Aanbevelingstypen: refactor, security, modernize, process, training,
                   architecture, compliance (GDPR / NIS2 / EU AI Act).

Gebruik:
    engine = get_recommendation_engine()
    rapport = engine.genereer_recommendations(
        project_id="PRJ-2024-001",
        context={
            "sector": "RETAIL",
            "talen": ["php", "javascript"],
            "bevindingen": ["geen CI/CD", "rest api aanwezig"],
            "technologieen": ["PHP 5.6", "jQuery"],
            "schuldscore": 7.5,
        },
    )
    print(rapport.to_markdown())
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ─── Optionele imports ────────────────────────────────────────────────────────

try:
    from ..content.knowledge_graph import (  # type: ignore[import]
        EdgeType,
        GraphNode,
        KnowledgeGraph,
        NodeType,
        get_graph_builder,
    )
    _GRAPH_AVAILABLE = True
    logger.debug("knowledge_graph module beschikbaar")
except ImportError:
    KnowledgeGraph = None  # type: ignore[assignment,misc]
    GraphNode = None  # type: ignore[assignment,misc]
    NodeType = None  # type: ignore[assignment,misc]
    EdgeType = None  # type: ignore[assignment,misc]
    get_graph_builder = None  # type: ignore[assignment]
    _GRAPH_AVAILABLE = False
    logger.info("knowledge_graph niet beschikbaar — graph-analyse uitgeschakeld")

try:
    from .sector_benchmarks import (
        Sector,
    )
    from .sector_benchmarks import (  # type: ignore[import]
        SectorBenchmarkEngine as SectorBenchmarks,
    )
    from .sector_benchmarks import (
        get_benchmark_engine as get_sector_benchmarks,
    )
    _BENCHMARKS_AVAILABLE = True
    logger.debug("sector_benchmarks module beschikbaar")
except ImportError:
    SectorBenchmarks = None  # type: ignore[assignment,misc]
    Sector = None  # type: ignore[assignment,misc]
    get_sector_benchmarks = None  # type: ignore[assignment]
    _BENCHMARKS_AVAILABLE = False
    logger.info("sector_benchmarks niet beschikbaar — benchmark-vergelijking uitgeschakeld")

try:
    from ..content.rag_engine import RAGEngine, get_rag_engine  # type: ignore[import]
    _RAG_AVAILABLE = True
    logger.debug("rag_engine module beschikbaar")
except ImportError:
    RAGEngine = None  # type: ignore[assignment,misc]
    get_rag_engine = None  # type: ignore[assignment]
    _RAG_AVAILABLE = False
    logger.info("rag_engine niet beschikbaar — RAG context uitgeschakeld")


# ─── Enums ────────────────────────────────────────────────────────────────────

class RecommendationType(str, Enum):
    """Type van een aanbeveling — welke categorie actie is vereist."""
    REFACTOR     = "refactor"      # technische schuld wegwerken
    SECURITY     = "security"      # beveiligingsproblemen oplossen
    MODERNIZE    = "modernize"     # legacy tech updaten naar huidige standaard
    PROCESS      = "process"       # procesverbetering (CI/CD, testing, ...)
    TRAINING     = "training"      # teamtraining / kennisopbouw
    ARCHITECTURE = "architecture"  # architectuurwijziging (bijv. microservices)
    COMPLIANCE   = "compliance"    # GDPR / NIS2 / EU AI Act verplichtingen


class RecommendationPriority(str, Enum):
    """Urgentie van een aanbeveling — bepaalt de actietermijn."""
    KRITIEK = "kritiek"  # direct actie vereist — beveiligings- of juridisch risico
    HOOG    = "hoog"     # actie binnen 1 maand
    MEDIUM  = "medium"   # actie binnen 3 maanden
    LAAG    = "laag"     # in de backlog opnemen


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class Recommendation:
    """
    Één concrete aanbeveling voor een klantproject.

    Bevat alle informatie die nodig is voor directe actie: beschrijving,
    impact/effort scores, sector-context en concrete actiestappen.
    """
    recommendation_id: str                   # UUID4
    project_id: str
    type: RecommendationType
    prioriteit: RecommendationPriority
    titel: str                               # kort label voor in tabellen/koppen
    beschrijving: str                        # uitgebreide uitleg voor de klant
    impact_score: float                      # 0.0–1.0, hoger = meer business impact
    effort_score: float                      # 0.0–1.0, hoger = meer werk / investering
    roi_score: float                         # impact / max(effort, 0.01) — berekend
    sector_benchmark_ref: str | None         # benchmark-tekst indien beschikbaar
    gerelateerde_nodes: list[str]            # node-namen uit de KnowledgeGraph
    actie_stappen: list[str]                 # concrete to-do's (3–5 items)
    aangemaakt_op: str                       # ISO 8601 UTC datetime string

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSON-compatibel dict voor opslag of API-response."""
        return {
            "recommendation_id":  self.recommendation_id,
            "project_id":         self.project_id,
            "type":               self.type.value,
            "prioriteit":         self.prioriteit.value,
            "titel":              self.titel,
            "beschrijving":       self.beschrijving,
            "impact_score":       round(self.impact_score, 4),
            "effort_score":       round(self.effort_score, 4),
            "roi_score":          round(self.roi_score, 4),
            "sector_benchmark_ref": self.sector_benchmark_ref,
            "gerelateerde_nodes": self.gerelateerde_nodes,
            "actie_stappen":      self.actie_stappen,
            "aangemaakt_op":      self.aangemaakt_op,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Recommendation:
        """Deserialiseer vanuit een dict (bijv. uit database of API-response)."""
        return cls(
            recommendation_id=d["recommendation_id"],
            project_id=d["project_id"],
            type=RecommendationType(d["type"]),
            prioriteit=RecommendationPriority(d["prioriteit"]),
            titel=d["titel"],
            beschrijving=d["beschrijving"],
            impact_score=float(d["impact_score"]),
            effort_score=float(d["effort_score"]),
            roi_score=float(d["roi_score"]),
            sector_benchmark_ref=d.get("sector_benchmark_ref"),
            gerelateerde_nodes=list(d.get("gerelateerde_nodes", [])),
            actie_stappen=list(d.get("actie_stappen", [])),
            aangemaakt_op=d["aangemaakt_op"],
        )


@dataclass
class RecommendationReport:
    """
    Volledig aanbevelingsrapport voor één project.

    Bevat samenvatting, top-3 en alle aanbevelingen gesorteerd op ROI,
    plus optionele sector-vergelijkingstekst voor klant-levering.
    """
    report_id: str
    project_id: str
    sector: str | None
    totaal_aanbevelingen: int
    kritieke_aanbevelingen: int
    top_3: list[Recommendation]              # gesorteerd op roi_score DESC
    alle_aanbevelingen: list[Recommendation] # gesorteerd op roi_score DESC
    sector_vergelijking: str | None          # tekst uit genereer_samenvatting()
    aangemaakt_op: str

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSON-compatibel dict."""
        return {
            "report_id":             self.report_id,
            "project_id":            self.project_id,
            "sector":                self.sector,
            "totaal_aanbevelingen":  self.totaal_aanbevelingen,
            "kritieke_aanbevelingen": self.kritieke_aanbevelingen,
            "top_3":                 [r.to_dict() for r in self.top_3],
            "alle_aanbevelingen":    [r.to_dict() for r in self.alle_aanbevelingen],
            "sector_vergelijking":   self.sector_vergelijking,
            "aangemaakt_op":         self.aangemaakt_op,
        }

    def to_markdown(self) -> str:
        """
        Exporteer het rapport als Markdown-document klaar voor directe klant-levering.

        Het rapport bevat:
        - Samenvatting met KPIs
        - Top-3 prioriteiten met actiestappen
        - Sector-vergelijking indien beschikbaar
        - Volledige aanbevelingstabel gesorteerd op ROI

        Returns:
            Multi-line Markdown string.
        """
        nu = self.aangemaakt_op
        sector_label = self.sector or "Onbekend"

        # Gemiddelde ROI over alle aanbevelingen
        if self.alle_aanbevelingen:
            gem_roi = sum(r.roi_score for r in self.alle_aanbevelingen) / len(self.alle_aanbevelingen)
        else:
            gem_roi = 0.0

        # ── Koptekst ──────────────────────────────────────────────
        regels: list[str] = [
            f"# Aanbevelingsrapport — {self.project_id}",
            "",
            f"**Sector:** {sector_label} | **Datum:** {nu}  ",
            f"**Rapport ID:** {self.report_id}",
            "",
            "---",
            "",
        ]

        # ── Samenvatting ──────────────────────────────────────────
        regels += [
            "## 📊 Samenvatting",
            "",
            f"- Totaal aanbevelingen: **{self.totaal_aanbevelingen}**",
            f"- Kritieke aanbevelingen: **{self.kritieke_aanbevelingen}**",
            f"- Gemiddelde ROI-score: **{gem_roi:.2f}**",
            "",
        ]

        # ── Top 3 prioriteiten ────────────────────────────────────
        if self.top_3:
            regels += [
                "## 🔴 Top 3 Prioriteiten",
                "",
            ]
            for idx, rec in enumerate(self.top_3, start=1):
                prioriteit_emoji = {
                    "kritiek": "🔴",
                    "hoog":    "🟠",
                    "medium":  "🟡",
                    "laag":    "🟢",
                }.get(rec.prioriteit.value, "⚪")
                regels += [
                    f"### {idx}. {rec.titel} [{rec.prioriteit.value.upper()}] {prioriteit_emoji}",
                    "",
                    f"**Type:** {rec.type.value} | **Impact:** {rec.impact_score:.2f} | "
                    f"**Effort:** {rec.effort_score:.2f} | **ROI-score:** {rec.roi_score:.2f}",
                    "",
                    rec.beschrijving,
                    "",
                    "**Actiestappen:**",
                ]
                for stap in rec.actie_stappen:
                    regels.append(f"- {stap}")
                if rec.sector_benchmark_ref:
                    regels += ["", f"> 📈 *{rec.sector_benchmark_ref}*"]
                regels.append("")

        # ── Sector vergelijking ───────────────────────────────────
        if self.sector_vergelijking:
            regels += [
                "## 📈 Sector Vergelijking",
                "",
                self.sector_vergelijking,
                "",
            ]

        # ── Alle aanbevelingen tabel ──────────────────────────────
        if self.alle_aanbevelingen:
            regels += [
                "## 📋 Alle Aanbevelingen",
                "",
                "| # | Titel | Type | Prioriteit | Impact | Effort | ROI |",
                "|---|-------|------|-----------|--------|--------|-----|",
            ]
            for idx, rec in enumerate(self.alle_aanbevelingen, start=1):
                regels.append(
                    f"| {idx} | {rec.titel} | {rec.type.value} | "
                    f"{rec.prioriteit.value} | {rec.impact_score:.2f} | "
                    f"{rec.effort_score:.2f} | {rec.roi_score:.2f} |"
                )
            regels.append("")

        # ── Footer ────────────────────────────────────────────────
        regels += [
            "---",
            "",
            "*Gegenereerd door VorstersNV Recommendation Engine. "
            "Dit rapport is bedoeld als strategisch advies voor het management.*",
            "",
        ]

        return "\n".join(regels)


# ─── RecommendationEngine ─────────────────────────────────────────────────────

# NIS2-plichtige sectoren (Belgische context, oct 2024)
_NIS2_SECTOREN: frozenset[str] = frozenset({
    "ZORG", "FINANCE", "OVERHEID", "LOGISTIEK",
    "zorg", "finance", "overheid", "logistiek",
})

# Mapping sector string → Sector enum (indien beschikbaar)
def _parse_sector(sector_str: str | None) -> Any | None:
    """Zet een sector-string om naar Sector enum-waarde (als module beschikbaar)."""
    if not sector_str or not _BENCHMARKS_AVAILABLE or Sector is None:
        return None
    try:
        return Sector(sector_str.lower())
    except ValueError:
        logger.debug("Sector '%s' niet herkend in Sector enum", sector_str)
        return None


def _nu_utc() -> str:
    """Return huidige UTC datetime als ISO 8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


def _maak_recommendation(
    project_id: str,
    type_: RecommendationType,
    prioriteit: RecommendationPriority,
    titel: str,
    beschrijving: str,
    impact_score: float,
    effort_score: float,
    actie_stappen: list[str],
    gerelateerde_nodes: list[str] | None = None,
    sector_benchmark_ref: str | None = None,
) -> Recommendation:
    """
    Factory-functie die een Recommendation aanmaakt met berekende roi_score.

    roi_score = impact_score / max(effort_score, 0.01) — voorkomt deling door nul.
    """
    roi = round(impact_score / max(effort_score, 0.01), 4)
    return Recommendation(
        recommendation_id=str(uuid.uuid4()),
        project_id=project_id,
        type=type_,
        prioriteit=prioriteit,
        titel=titel,
        beschrijving=beschrijving,
        impact_score=round(impact_score, 4),
        effort_score=round(effort_score, 4),
        roi_score=roi,
        sector_benchmark_ref=sector_benchmark_ref,
        gerelateerde_nodes=gerelateerde_nodes or [],
        actie_stappen=actie_stappen,
        aangemaakt_op=_nu_utc(),
    )


class RecommendationEngine:
    """
    Next-best-action aanbevelingsengine voor VorstersNV klantprojecten.

    Combineert drie bronnen voor aanbevelingen:
    1. KnowledgeGraph — structurele bevindingen uit de codebase
    2. Rule-based logica — technologie, security, process en compliance regels
    3. Sector benchmarks — vergelijking met Belgische KMO-sector-gemiddelden

    Typisch gebruik:
        engine = get_recommendation_engine()
        rapport = engine.genereer_recommendations("PRJ-001", context)
        print(rapport.to_markdown())
    """

    def __init__(
        self,
        graph: Any | None = None,
        sector_benchmarks: Any | None = None,
        rag_engine: Any | None = None,
    ) -> None:
        """
        Initialiseer de engine met optionele afhankelijkheden.

        Alle parameters zijn optioneel — de engine degradeert gracefully
        wanneer een module niet beschikbaar is.

        Args:
            graph:            KnowledgeGraph instantie voor code-analyse.
            sector_benchmarks: SectorBenchmarkEngine voor benchmark-vergelijkingen.
            rag_engine:       RAGEngine voor RAG-context (toekomstig gebruik).
        """
        self._graph: Any | None = graph
        self._sector_benchmarks: Any | None = sector_benchmarks
        self._rag_engine: Any | None = rag_engine

        logger.info(
            "RecommendationEngine geïnitialiseerd — graph=%s, benchmarks=%s, rag=%s",
            self._graph is not None,
            self._sector_benchmarks is not None,
            self._rag_engine is not None,
        )

    # ── Publieke API ──────────────────────────────────────────────────────────

    def genereer_recommendations(
        self,
        project_id: str,
        context: dict[str, Any] | None = None,
    ) -> RecommendationReport:
        """
        Hoofdmethode — genereert een volledig aanbevelingsrapport voor een project.

        Doorloopt een gestructureerde pipeline:
        1. Graph-analyse voor structurele bevindingen
        2. Tech-aanbevelingen (MODERNIZE / REFACTOR)
        3. Security-aanbevelingen
        4. Process-aanbevelingen (CI/CD, testing)
        5. Compliance-aanbevelingen (GDPR / NIS2)
        6. Sector-benchmarks toevoegen aan elke aanbeveling
        7. Sortering op roi_score DESC en rapport-opbouw

        Args:
            project_id: Unieke identifier van het klantproject.
            context:    Dict met optionele analyse-context:
                          - "sector": str (bijv. "RETAIL")
                          - "talen": list[str]
                          - "bevindingen": list[str]
                          - "technologieen": list[str]
                          - "schuldscore": float (0–10)

        Returns:
            Volledig gevuld RecommendationReport gesorteerd op roi_score DESC.
        """
        ctx = context or {}
        sector_str: str | None = ctx.get("sector")

        logger.info(
            "Genereer aanbevelingen voor project '%s' (sector=%s)",
            project_id, sector_str or "onbekend",
        )

        # ── Stap 1: graph-analyse ─────────────────────────────────
        graph_findings = self._analyseer_graph(project_id)
        if graph_findings:
            bestaande = list(ctx.get("bevindingen") or [])
            ctx = {**ctx, "bevindingen": bestaande + graph_findings}
            logger.debug(
                "Graph analyse toegevoegd: %d findings voor project '%s'",
                len(graph_findings), project_id,
            )

        # ── Stap 2–5: rule-based aanbevelingen ────────────────────
        aanbevelingen: list[Recommendation] = []
        aanbevelingen.extend(self._genereer_tech_aanbevelingen(project_id, ctx))
        aanbevelingen.extend(self._genereer_security_aanbevelingen(project_id, ctx))
        aanbevelingen.extend(self._genereer_process_aanbevelingen(project_id, ctx))
        aanbevelingen.extend(self._genereer_compliance_aanbevelingen(project_id, ctx))

        logger.debug(
            "Rule-based pipeline: %d aanbevelingen gegenereerd voor project '%s'",
            len(aanbevelingen), project_id,
        )

        # ── Stap 6: sector-benchmarks koppelen ────────────────────
        aanbevelingen = self._voeg_sector_benchmarks_toe(aanbevelingen, ctx)

        # ── Stap 7: sorteren op roi_score DESC ────────────────────
        aanbevelingen.sort(key=lambda r: r.roi_score, reverse=True)

        # ── Sector-vergelijkingstekst ──────────────────────────────
        sector_vergelijking = self._genereer_sector_vergelijking(project_id, ctx)

        # ── Rapport samenstellen ──────────────────────────────────
        kritieke_count = sum(
            1 for r in aanbevelingen
            if r.prioriteit == RecommendationPriority.KRITIEK
        )
        top_3 = aanbevelingen[:3]

        rapport = RecommendationReport(
            report_id=str(uuid.uuid4()),
            project_id=project_id,
            sector=sector_str,
            totaal_aanbevelingen=len(aanbevelingen),
            kritieke_aanbevelingen=kritieke_count,
            top_3=top_3,
            alle_aanbevelingen=aanbevelingen,
            sector_vergelijking=sector_vergelijking,
            aangemaakt_op=_nu_utc(),
        )

        logger.info(
            "Rapport klaar: project='%s', %d aanbevelingen (%d kritiek), top-ROI=%.2f",
            project_id,
            rapport.totaal_aanbevelingen,
            rapport.kritieke_aanbevelingen,
            top_3[0].roi_score if top_3 else 0.0,
        )
        return rapport

    # ── Private: graph analyse ────────────────────────────────────────────────

    def _analyseer_graph(self, project_id: str) -> list[str]:
        """
        Query de KnowledgeGraph voor dit project en extraheer findings.

        Zoekt naar structurele patronen:
        - Hoge koppelingsdichtheid → tight coupling melding
        - Cyclische afhankelijkheden → dependency cycle melding
        - Nodes met metadata 'complexiteit: HOOG' → refactor kandidaten
        - Modules met > 10 edges → God Class / God Module patroon

        Args:
            project_id: Unieke identifier van het project.

        Returns:
            Lijst van finding-strings. Leeg als graph niet beschikbaar.
        """
        if not _GRAPH_AVAILABLE or self._graph is None:
            logger.debug("_analyseer_graph: graph niet beschikbaar voor project '%s'", project_id)
            return []

        try:
            graph = self._graph

            # Controleer of dit de juiste graaf is
            if hasattr(graph, "project_id") and graph.project_id != project_id:
                logger.debug(
                    "_analyseer_graph: graph project_id '%s' != gevraagd '%s'",
                    graph.project_id, project_id,
                )
                return []

            findings: list[str] = []
            stats = graph.get_statistieken()

            # Koppelingsdichtheid check
            if stats.koppelingsdichtheid > 0.3:
                findings.append(
                    f"hoge koppelingsdichtheid ({stats.koppelingsdichtheid:.3f}) — "
                    "architectuur is sterk verweven (tight coupling)"
                )

            # Cyclische afhankelijkheden
            if stats.cyclische_afhankelijkheden:
                n_cycli = len(stats.cyclische_afhankelijkheden)
                findings.append(
                    f"{n_cycli} cyclische afhankelijkhe{'id' if n_cycli == 1 else 'den'} "
                    "gedetecteerd — herschikking van modules vereist"
                )

            # God Class / God Module (nodes met hoge degree)
            for naam, degree in stats.meest_gekoppelde_nodes[:3]:
                if degree > 10:
                    findings.append(
                        f"God Class/Module patroon: '{naam}' heeft {degree} koppelingen — "
                        "refactoring aanbevolen"
                    )

            # Nodes met expliciete complexiteitsmarkering
            for node in graph._nodes.values():  # noqa: SLF001
                meta = node.metadata or {}
                if str(meta.get("complexiteit", "")).upper() == "HOOG":
                    findings.append(
                        f"complexe node '{node.naam}' gedetecteerd — refactoring kandidaat"
                    )

            logger.info(
                "_analyseer_graph: %d findings voor project '%s'",
                len(findings), project_id,
            )
            return findings

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "_analyseer_graph: fout bij analyse van project '%s': %s",
                project_id, exc,
            )
            return []

    # ── Private: tech aanbevelingen ───────────────────────────────────────────

    def _genereer_tech_aanbevelingen(
        self,
        project_id: str,
        context: dict[str, Any],
    ) -> list[Recommendation]:
        """
        Genereer MODERNIZE en REFACTOR aanbevelingen op basis van technologiestapel
        en technische schuldscore in de context.

        Regels:
        - PHP 5.x → MODERNIZE KRITIEK
        - Java 8 of lager → MODERNIZE HOOG
        - Spring Boot 2.x → MODERNIZE MEDIUM
        - schuldscore > 7 → REFACTOR KRITIEK
        - schuldscore > 5 → REFACTOR HOOG
        """
        recs: list[Recommendation] = []
        technologieen: list[str] = [t.lower() for t in context.get("technologieen", [])]
        schuldscore: float = float(context.get("schuldscore", 0.0))
        talen: list[str] = [t.lower() for t in context.get("talen", [])]

        # ── PHP 5.x ───────────────────────────────────────────────
        php5_gevonden = any(
            ("php 5" in t or "php5" in t) for t in technologieen
        ) or any(("php 5" in t or "php5" in t) for t in talen)

        if php5_gevonden:
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.MODERNIZE,
                prioriteit=RecommendationPriority.KRITIEK,
                titel="PHP 5.x EOL — kritiek beveiligingsrisico",
                beschrijving=(
                    "PHP 5.x heeft End-of-Life bereikt in december 2018 en ontvangt geen "
                    "beveiligingsupdates meer. Dit vormt een kritiek risico voor de veiligheid "
                    "en stabiliteit van de applicatie. Migratie naar PHP 8.2 (LTS tot 2026-12) "
                    "is dringend vereist."
                ),
                impact_score=0.9,
                effort_score=0.7,
                actie_stappen=[
                    "Inventariseer alle PHP 5.x dependencies en incompatibele code",
                    "Migreer naar PHP 8.2 (LTS tot 2026-12) via gefaseerde aanpak",
                    "Test volledige regressiesuite met PHPUnit na elke migratiestap",
                    "Update composer.json en alle pakketversies naar PHP 8-compatibele varianten",
                    "Plan phased rollout per module met rollback-strategie",
                ],
            ))
            logger.debug("Tech rec toegevoegd: PHP 5.x EOL voor project '%s'", project_id)

        # ── Java 8 of lager ───────────────────────────────────────
        java_oud = any(
            ("java 8" in t or "java8" in t or "java 7" in t or "java 6" in t or
             "jdk 8" in t or "jdk8" in t)
            for t in technologieen
        )
        if java_oud:
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.MODERNIZE,
                prioriteit=RecommendationPriority.HOOG,
                titel="Java 8 EOL — migreer naar Java 21 LTS",
                beschrijving=(
                    "Java 8 (Oracle) is EOL; alleen nog commercial support beschikbaar. "
                    "Java 21 LTS (sept 2023) biedt betere performance, virtual threads "
                    "(Project Loom), pattern matching en langdurige support tot sept 2031. "
                    "Migratie vermindert security-risico en ontgrendelt moderne JVM-features."
                ),
                impact_score=0.8,
                effort_score=0.6,
                actie_stappen=[
                    "Analyseer API-wijzigingen tussen Java 8 en 21 met jdeprscan",
                    "Update build tool (Maven/Gradle) naar Java 21-compatibele versie",
                    "Vervang deprecated API-gebruik (sun.*, com.sun.*)",
                    "Voer integratie- en load tests uit op Java 21",
                    "Deploy via canary release — 10% productieverkeer eerst",
                ],
            ))

        # ── Spring Boot 2.x ───────────────────────────────────────
        spring2 = any(
            ("spring boot 2" in t or "spring-boot 2" in t or "springboot 2" in t)
            for t in technologieen
        )
        if spring2:
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.MODERNIZE,
                prioriteit=RecommendationPriority.MEDIUM,
                titel="Spring Boot 2.x EOL — upgrade naar Spring Boot 3.x",
                beschrijving=(
                    "Spring Boot 2.x heeft End-of-Life bereikt in november 2023. "
                    "Spring Boot 3.x vereist Java 17+ maar biedt native AOT-compilatie, "
                    "verbeterde observability en GraalVM-ondersteuning voor betere performance."
                ),
                impact_score=0.7,
                effort_score=0.5,
                actie_stappen=[
                    "Upgrade Java naar minimaal versie 17 (vereiste voor Spring Boot 3)",
                    "Vervang javax.* imports door jakarta.* (Jakarta EE 9+ namespace)",
                    "Update Spring Security configuratie naar de nieuwe lambda DSL",
                    "Valideer alle auto-configuratie via de Spring Boot 3 migratieguide",
                    "Test met Spring Boot Test slices na de upgrade",
                ],
            ))

        # ── Technische schuld: score > 7 → KRITIEK ────────────────
        if schuldscore > 7.0:
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.REFACTOR,
                prioriteit=RecommendationPriority.KRITIEK,
                titel=f"Hoge technische schuld (score {schuldscore:.1f}/10) — kritiek",
                beschrijving=(
                    f"De technische schuldscore van {schuldscore:.1f}/10 wijst op kritieke "
                    "problemen die de onderhoudbaarheid, betrouwbaarheid en uitbreidbaarheid "
                    "van de applicatie ernstig belemmeren. Onmiddellijke refactoring is vereist "
                    "om verdere kostenstijging en risico's te beperken."
                ),
                impact_score=0.85,
                effort_score=0.8,
                actie_stappen=[
                    "Voer een volledige statische code-analyse uit (SonarQube, CodeClimate)",
                    "Identificeer de top-10 'hotspot' bestanden met hoogste complexiteit",
                    "Plan een gerichte refactoring sprint van 2 weken per hotspot-module",
                    "Schrijf karakteriseringstests voor kritieke code vóór refactoring",
                    "Stel een technische schuld-budget in: max. 20% van elke sprint",
                ],
            ))
        elif schuldscore > 5.0:
            # ── Technische schuld: score > 5 → HOOG ──────────────
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.REFACTOR,
                prioriteit=RecommendationPriority.HOOG,
                titel=f"Verhoogde technische schuld (score {schuldscore:.1f}/10)",
                beschrijving=(
                    f"Een technische schuldscore van {schuldscore:.1f}/10 overstijgt het "
                    "risicodrempel van 5/10. Dit vertraagt nieuwe feature-ontwikkeling "
                    "aanzienlijk en verhoogt het risico op regressies. Structurele aanpak "
                    "binnen één maand aanbevolen."
                ),
                impact_score=0.7,
                effort_score=0.6,
                actie_stappen=[
                    "Meet huidige technische schuld kwantitatief met SonarQube of equivalente tool",
                    "Stel een refactoring-backlog op gesorteerd op business impact",
                    "Wijs 15–20% van elke sprint toe aan schuld-reductie",
                    "Introduceer code review-checklist om nieuwe schuld te voorkomen",
                    "Track de schuldscore maandelijks als kwaliteits-KPI",
                ],
            ))

        return recs

    # ── Private: security aanbevelingen ──────────────────────────────────────

    def _genereer_security_aanbevelingen(
        self,
        project_id: str,
        context: dict[str, Any],
    ) -> list[Recommendation]:
        """
        Genereer SECURITY aanbevelingen passend bij de Belgische KMO-context.

        Standaard:
        - Dependency vulnerability scanning (altijd)

        Conditioneel:
        - SQL injection risico (bij PHP in talen)
        - API authenticatie audit (bij 'api' of 'rest' in bevindingen)
        """
        recs: list[Recommendation] = []
        talen: list[str] = [t.lower() for t in context.get("talen", [])]
        bevindingen: list[str] = [b.lower() for b in context.get("bevindingen", [])]

        # ── Dependency scanning (altijd) ──────────────────────────
        recs.append(_maak_recommendation(
            project_id=project_id,
            type_=RecommendationType.SECURITY,
            prioriteit=RecommendationPriority.MEDIUM,
            titel="Implementeer dependency vulnerability scanning",
            beschrijving=(
                "Bekende kwetsbaarheden in third-party libraries zijn een van de meest "
                "voorkomende aanvalsvectoren (OWASP Top 10 #6). Geautomatiseerde scanning "
                "via Dependabot (GitHub) of Snyk detecteert kwetsbaarheden direct bij elke "
                "commit en PR, zonder manuele opvolging."
            ),
            impact_score=0.75,
            effort_score=0.2,
            actie_stappen=[
                "Activeer Dependabot alerts in de GitHub/GitLab repository settings",
                "Configureer Snyk of OWASP Dependency-Check in de CI/CD pipeline",
                "Stel een beleid in: KRITIEKE CVEs worden binnen 48u gepatcht",
                "Voeg een wekelijkse dependency-update PR-workflow toe",
                "Documenteer het vulnerability management proces in de security policy",
            ],
        ))

        # ── SQL injection bij PHP ─────────────────────────────────
        php_aanwezig = any(("php" in t) for t in talen)
        if php_aanwezig:
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.SECURITY,
                prioriteit=RecommendationPriority.HOOG,
                titel="SQL injection risico-evaluatie vereist — PHP legacy code",
                beschrijving=(
                    "PHP legacy code bevat frequent directe database-aanroepen zonder "
                    "prepared statements of ORM-bescherming. SQL injection blijft de "
                    "meest kritieke kwetsbaarheid voor dataverlies en diefstal "
                    "(OWASP Top 10 #3). Een gerichte code-audit is noodzakelijk."
                ),
                impact_score=0.9,
                effort_score=0.4,
                actie_stappen=[
                    "Scan alle PHP-bestanden op directe string-interpolatie in SQL queries",
                    "Vervang alle variabele SQL-concatenaties door PDO prepared statements",
                    "Voer een geautomatiseerde DAST-scan uit met OWASP ZAP of sqlmap",
                    "Voeg parameterized queries toe als coderings-standaard in code review",
                    "Test alle input-formulieren manueel op injection-patronen",
                ],
            ))

        # ── API authenticatie audit ───────────────────────────────
        api_aanwezig = any(("api" in b or "rest" in b or "graphql" in b) for b in bevindingen)
        if api_aanwezig:
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.SECURITY,
                prioriteit=RecommendationPriority.HOOG,
                titel="API authenticatie audit — controleer JWT/OAuth2 implementatie",
                beschrijving=(
                    "Bij REST/GraphQL APIs zijn veelvoorkomende kwetsbaarheden: ontbrekende "
                    "autorisatiecontroles (IDOR), zwakke JWT-configuratie (alg:none), en "
                    "afwezigheid van rate limiting. Een systematische audit verkleint het "
                    "aanvalsoppervlak significant."
                ),
                impact_score=0.8,
                effort_score=0.3,
                actie_stappen=[
                    "Auditeer alle API endpoints op aanwezigheid van authenticatie-middleware",
                    "Valideer JWT-configuratie: gebruik RS256, stel exp/iss/aud in",
                    "Test alle resource-endpoints op IDOR kwetsbaarheden via boundary testing",
                    "Implementeer rate limiting (bijv. 100 req/min per IP) op publieke endpoints",
                    "Voeg API security headers toe: CORS, CSP, HSTS",
                ],
            ))

        return recs

    # ── Private: process aanbevelingen ───────────────────────────────────────

    def _genereer_process_aanbevelingen(
        self,
        project_id: str,
        context: dict[str, Any],  # noqa: ARG002
    ) -> list[Recommendation]:
        """
        Genereer PROCESS aanbevelingen voor softwareontwikkelingskwaliteit.

        Altijd toegevoegd:
        - CI/CD pipeline implementatie
        - Geautomatiseerde tests (>70% coverage)
        """
        recs: list[Recommendation] = []

        # ── CI/CD pipeline ────────────────────────────────────────
        recs.append(_maak_recommendation(
            project_id=project_id,
            type_=RecommendationType.PROCESS,
            prioriteit=RecommendationPriority.MEDIUM,
            titel="Implementeer CI/CD pipeline voor kwaliteitscontrole",
            beschrijving=(
                "Zonder geautomatiseerde CI/CD worden kwaliteitsproblemen laat ontdekt, "
                "deployments zijn foutgevoelig en releases langzamer. Een CI/CD pipeline "
                "met geautomatiseerde tests, linting en deployment vermindert regressies "
                "en versnelt de time-to-market significant."
            ),
            impact_score=0.7,
            effort_score=0.4,
            actie_stappen=[
                "Kies een CI/CD platform: GitHub Actions, GitLab CI of Azure DevOps",
                "Configureer een build-pipeline: lint → test → build → deploy-to-staging",
                "Voeg branch protection rules toe: PR vereist passing CI + code review",
                "Implementeer automatische deployment naar staging bij merge naar main",
                "Voeg rollback-mechanisme toe via blue/green of canary deployment",
            ],
        ))

        # ── Geautomatiseerde tests ─────────────────────────────────
        recs.append(_maak_recommendation(
            project_id=project_id,
            type_=RecommendationType.PROCESS,
            prioriteit=RecommendationPriority.MEDIUM,
            titel="Voeg geautomatiseerde tests toe (streef naar >70% coverage)",
            beschrijving=(
                "Lage of ontbrekende testdekking maakt refactoring risicovol en "
                "vertraagt feature-ontwikkeling door angst voor regressies. "
                "Een testpiramide (unit > integratie > E2E) met >70% coverage "
                "is de industriestandaard voor KMO-softwareprojecten."
            ),
            impact_score=0.75,
            effort_score=0.5,
            actie_stappen=[
                "Meet de huidige testdekking met JaCoCo (Java) of Coverage.py (Python)",
                "Schrijf unit tests voor alle nieuwe code (test-first bij voorkeur)",
                "Voeg integratietests toe voor kritieke business flows (betalingen, orders)",
                "Configureer een minimum coverage drempel van 70% in de CI-pipeline",
                "Plan een 'test debt sprint' om kritieke ongeteste code te coderen",
            ],
        ))

        return recs

    # ── Private: compliance aanbevelingen ────────────────────────────────────

    def _genereer_compliance_aanbevelingen(
        self,
        project_id: str,
        context: dict[str, Any],
    ) -> list[Recommendation]:
        """
        Genereer COMPLIANCE aanbevelingen voor de Belgische juridische context.

        Altijd:
        - GDPR data flow audit (verplicht voor alle Belgische KMOs)

        Conditioneel:
        - NIS2 compliance check (verplicht voor ZORG, FINANCE, OVERHEID, LOGISTIEK)
        """
        recs: list[Recommendation] = []
        sector_str: str | None = context.get("sector")
        sector_upper = (sector_str or "").upper()

        # ── GDPR (altijd) ─────────────────────────────────────────
        recs.append(_maak_recommendation(
            project_id=project_id,
            type_=RecommendationType.COMPLIANCE,
            prioriteit=RecommendationPriority.MEDIUM,
            titel="GDPR data flow audit — verplicht voor Belgische KMOs",
            beschrijving=(
                "De GDPR/AVG is van toepassing op elke Belgische organisatie die "
                "persoonsgegevens verwerkt. Een data flow audit identificeert welke "
                "gegevens verwerkt worden, op welke rechtsgrond, en of de technische "
                "en organisatorische maatregelen voldoen aan de vereisten. "
                "Niet-naleving riskeert boetes tot 4% van de jaarlijkse omzet."
            ),
            impact_score=0.8,
            effort_score=0.3,
            actie_stappen=[
                "Stel een register van verwerkingsactiviteiten (RVA) op conform art. 30 GDPR",
                "Identificeer alle persoonsgegevens in de codebase en databases",
                "Controleer of er een rechtsgeldige verwerkingsgrondslag is per verwerking",
                "Implementeer technische maatregelen: encryptie at rest, pseudonimisering",
                "Stel een privacyverklaring en cookie-beleid op en publiceer op de website",
            ],
        ))

        # ── NIS2 (sectorspecifiek) ────────────────────────────────
        nis2_vereist = sector_upper in _NIS2_SECTOREN
        if nis2_vereist:
            sector_label = sector_str or sector_upper
            recs.append(_maak_recommendation(
                project_id=project_id,
                type_=RecommendationType.COMPLIANCE,
                prioriteit=RecommendationPriority.HOOG,
                titel=f"NIS2 compliance verplicht voor sector {sector_label}",
                beschrijving=(
                    f"De NIS2-richtlijn (omgezet in Belgisch recht per okt 2024) is "
                    f"verplicht van toepassing voor organisaties in de {sector_label}-sector. "
                    "NIS2 vereist maatregelen voor cybersecurity-risicobeheer, "
                    "incidentmeldingsplicht (binnen 24u aan CCB) en leveranciersketenbeheer. "
                    "Niet-naleving riskeert boetes tot €10 miljoen of 2% van de omzet."
                ),
                impact_score=0.9,
                effort_score=0.5,
                actie_stappen=[
                    "Laat een NIS2-gap analyse uitvoeren door een gecertificeerd auditor",
                    "Stel een Information Security Management System (ISMS) op (ISO 27001 als basis)",
                    "Implementeer een incidentresponse procedure met meldplicht naar CCB",
                    "Voer een leveranciersrisicobeoordeling uit voor alle kritieke IT-leveranciers",
                    "Train het management en IT-team op NIS2-verplichtingen en meldprocedures",
                ],
            ))

        return recs

    # ── Private: sector benchmarks koppelen ──────────────────────────────────

    def _voeg_sector_benchmarks_toe(
        self,
        aanbevelingen: list[Recommendation],
        context: dict[str, Any],
    ) -> list[Recommendation]:
        """
        Verrijkt elke aanbeveling met een sector_benchmark_ref string.

        Roept SectorBenchmarkEngine.vergelijk_met_benchmark() aan voor de
        gedetecteerde sector en koppelt de samenvatting aan relevante aanbevelingen.

        Args:
            aanbevelingen: Lijst van reeds gegenereerde Recommendations.
            context:       Project-context dict met optionele 'sector' en 'talen'.

        Returns:
            Dezelfde lijst, waarbij sector_benchmark_ref ingevuld is waar van toepassing.
        """
        if not _BENCHMARKS_AVAILABLE or self._sector_benchmarks is None:
            logger.debug("_voeg_sector_benchmarks_toe: sector_benchmarks niet beschikbaar")
            return aanbevelingen

        sector_str: str | None = context.get("sector")
        if not sector_str:
            return aanbevelingen

        sector_enum = _parse_sector(sector_str)
        if sector_enum is None:
            return aanbevelingen

        project_id = aanbevelingen[0].project_id if aanbevelingen else "onbekend"
        bevindingen: list[str] = list(context.get("bevindingen") or [])
        talen: list[str] = list(context.get("talen") or [])

        try:
            vergelijking = self._sector_benchmarks.vergelijk_met_benchmark(
                project_id=project_id,
                sector=sector_enum,
                gevonden_issues=bevindingen,
                gevonden_talen=talen,
            )
            self._sector_benchmarks.genereer_samenvatting(vergelijking)
            benchmark = vergelijking.benchmark
            sector_naam = benchmark.naam_nl

            # Korte benchmark-referentie per aanbeveling
            for rec in aanbevelingen:
                rec.sector_benchmark_ref = (
                    f"Vergelijkbare {sector_naam}-klanten scoren gemiddeld "
                    f"{benchmark.technische_schuld.gemiddelde_score:.1f}/10 technische schuld. "
                    f"Urgentie modernisatie: {vergelijking.prioriteit_score:.1f}/10."
                )

            logger.info(
                "_voeg_sector_benchmarks_toe: benchmark '%s' gekoppeld aan %d aanbevelingen",
                sector_naam, len(aanbevelingen),
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "_voeg_sector_benchmarks_toe: benchmark-koppeling mislukt voor sector '%s': %s",
                sector_str, exc,
            )

        return aanbevelingen

    # ── Private: sector vergelijkingstekst ───────────────────────────────────

    def _genereer_sector_vergelijking(
        self,
        project_id: str,
        context: dict[str, Any],
    ) -> str | None:
        """
        Genereer de volledige sector-vergelijkingstekst voor het rapport.

        Gebruikt SectorBenchmarkEngine.genereer_samenvatting() om een uitgebreide
        Markdown-tekst te produceren die het project vergelijkt met sectorgemiddelden.

        Args:
            project_id: Unieke identifier van het project.
            context:    Context dict met 'sector', 'talen' en 'bevindingen'.

        Returns:
            Markdown-string of None als benchmarks niet beschikbaar zijn.
        """
        if not _BENCHMARKS_AVAILABLE or self._sector_benchmarks is None:
            return None

        sector_str: str | None = context.get("sector")
        if not sector_str:
            return None

        sector_enum = _parse_sector(sector_str)
        if sector_enum is None:
            return None

        try:
            vergelijking = self._sector_benchmarks.vergelijk_met_benchmark(
                project_id=project_id,
                sector=sector_enum,
                gevonden_issues=list(context.get("bevindingen") or []),
                gevonden_talen=list(context.get("talen") or []),
            )
            return self._sector_benchmarks.genereer_samenvatting(vergelijking)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "_genereer_sector_vergelijking: fout voor sector '%s': %s",
                sector_str, exc,
            )
            return None

    # ── Publieke hulpmethoden ─────────────────────────────────────────────────

    def filter_op_prioriteit(
        self,
        rapport: RecommendationReport,
        prioriteit: RecommendationPriority,
    ) -> list[Recommendation]:
        """
        Filter alle aanbevelingen in een rapport op een specifieke prioriteit.

        Args:
            rapport:    Het rapport om te filteren.
            prioriteit: De gewenste RecommendationPriority.

        Returns:
            Gefilterde lijst van Recommendations, volgorde behouden.
        """
        return [r for r in rapport.alle_aanbevelingen if r.prioriteit == prioriteit]

    def bereken_totale_roi(self, rapport: RecommendationReport) -> float:
        """
        Bereken de gecumuleerde ROI-score van kritieke en hoge aanbevelingen.

        Dit is een indicatieve maatstaf voor het totale verbeterpotentieel bij
        aanpak van de meest urgente issues.

        Args:
            rapport: Het aanbevelingsrapport.

        Returns:
            Som van roi_score voor alle KRITIEK + HOOG aanbevelingen (afgerond op 4 decimalen).
        """
        totaal = sum(
            r.roi_score
            for r in rapport.alle_aanbevelingen
            if r.prioriteit in (RecommendationPriority.KRITIEK, RecommendationPriority.HOOG)
        )
        return round(totaal, 4)


# ─── Singleton getter ─────────────────────────────────────────────────────────

_engine: RecommendationEngine | None = None


def get_recommendation_engine() -> RecommendationEngine:
    """
    Geef de singleton RecommendationEngine instantie terug.

    Lazy-initialiseert alle afhankelijkheden via try/except:
    - KnowledgeGraph: niet meegegeven (project-specifiek, per aanroep te injecteren)
    - SectorBenchmarkEngine: geladen via get_benchmark_engine()
    - RAGEngine: geladen via get_rag_engine()

    Returns:
        De gedeelde RecommendationEngine instantie.
    """
    global _engine
    if _engine is None:
        # Laad sector benchmarks
        benchmarks_instance = None
        if _BENCHMARKS_AVAILABLE and get_sector_benchmarks is not None:
            try:
                benchmarks_instance = get_sector_benchmarks()
                logger.info("get_recommendation_engine: SectorBenchmarkEngine geladen")
            except Exception as exc:  # noqa: BLE001
                logger.warning("get_recommendation_engine: sector_benchmarks laden mislukt: %s", exc)

        # Laad RAG engine
        rag_instance = None
        if _RAG_AVAILABLE and get_rag_engine is not None:
            try:
                rag_instance = get_rag_engine()
                logger.info("get_recommendation_engine: RAGEngine geladen")
            except Exception as exc:  # noqa: BLE001
                logger.warning("get_recommendation_engine: rag_engine laden mislukt: %s", exc)

        _engine = RecommendationEngine(
            graph=None,  # graph is project-specifiek — injecteren via constructor indien nodig
            sector_benchmarks=benchmarks_instance,
            rag_engine=rag_instance,
        )
        logger.info("get_recommendation_engine: singleton aangemaakt")

    return _engine
