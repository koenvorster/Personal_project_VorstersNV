"""
VorstersNV EU AI Act Compliance Module
=======================================

**Wettelijk kader — Verordening (EU) 2024/1689 (AI Act)**

De EU AI Act (in werking getreden augustus 2024, volledig van toepassing
vanaf 2 augustus 2026) legt risicogebaseerde verplichtingen op aan aanbieders
en gebruikers van AI-systemen. VorstersNV valt als "gebruiker" (deployer) van
Ollama-agents onder de verplichtingen van hoofdstuk III.

**Artikel 6 + Annex III — HIGH-RISK classificatie**

Een AI-systeem is HIGH-RISK indien het valt onder Annex III van de verordening.
Voor VorstersNV zijn twee agents HIGH-RISK geclassificeerd:

1. ``fraude_detectie_agent`` — Annex III, punt 5(b):
   AI-systemen die worden gebruikt voor het beoordelen van kredietwaardigheid
   of voor het vaststellen van de kredietscore van natuurlijke personen, dan wel
   voor het beoordelen van verzekeringsrisico's. Het blokkeren van betalingen
   op basis van een fraudescore heeft directe financiële impact op natuurlijke
   personen en valt daarmee onder deze categorie.

2. ``order_verwerking_agent`` — Annex III, punt 5(b):
   Geautomatiseerde besluitvorming over orderacceptatie en -verwerking met
   financiële gevolgen voor klanten kwalificeert als HIGH-RISK onder dezelfde
   categorie, wanneer de beslissing zonder tussenkomst van een mens tot stand
   komt.

**Toepasselijke artikelen voor HIGH-RISK systemen:**

- **Artikel 9** — Risicomanagement: identificatie, analyse en mitigatie van
  resterende risico's gedurende de volledige levenscyclus van het systeem.
- **Artikel 10** — Data governance: kwaliteits- en privacy-eisen voor
  trainings-, validatie- en testdata; PII-bescherming verplicht.
- **Artikel 13** — Transparantie: gebruikers moeten weten dat zij met een
  AI-systeem interageren; beslissingslogica moet begrijpelijk zijn.
- **Artikel 14** — Human-in-the-Loop (HITL): effectief menselijk toezicht
  bij beslissingen met aanzienlijke impact op personen.
- **Artikel 17** — Kwaliteitsbeheersysteem: gedocumenteerde processen voor
  risicobeheer, data governance, technische documentatie en audit.

**Officiële referentie:**
  https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX%3A32024R1689

Gebruik::

    from ollama.ai_act_compliance import (
        get_compliance_engine,
        ComplianceAuditEvent,
        eu_ai_act_log,
    )

    engine = get_compliance_engine()

    # Controleer HITL-verplichting vóór uitvoering
    if engine.check_hitl_vereist("fraude_detectie_agent", risicoscore=82.5):
        # stuur naar menselijk toezicht
        ...

    # Log een beslissing na afloop
    event = ComplianceAuditEvent(
        agent_naam="fraude_detectie_agent",
        timestamp=datetime.now(timezone.utc),
        beslissing="Betaling geblokkeerd o.b.v. fraudescore 82.5",
        trace_id="abc-123",
        risicoscore=82.5,
        hitl_toegepast=True,
        operator_id="operator@vorsters.be",
        outcome="afgewezen",
    )
    engine.log_beslissing(event)

    # Genereer compliance rapport over een periode
    rapport = engine.genereer_rapport(periode_start, periode_eind)

    # Exporteer Artikel 9 dossier
    dossier = engine.exporteer_artikel9_dossier("fraude_detectie_agent")
"""
from __future__ import annotations

import copy
import functools
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Type aliases
# ─────────────────────────────────────────────────────────────────────────────

_F = TypeVar("_F", bound=Callable[..., Any])

# Drempelwaarde voor automatische HITL-verplichting bij fraude_detectie_agent
_FRAUDE_HITL_DREMPEL: float = 70.0

# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────


class AIActRisicoKlasse(str, Enum):
    """
    Risicoklassificatie conform EU AI Act Artikel 6 en Annex III.

    - VERBODEN: Praktijken verboden onder Artikel 5 (social scoring, manipulatie
      van kwetsbare groepen, biometrische categorisering voor wetshandhaving).
      Niet gebruikt in VorstersNV.
    - HIGH_RISK: Annex III systemen met verplichte conformiteitsbeoordelingen.
    - BEPERKT: Systemen met transparantieverplichtingen (Artikel 50).
    - MINIMAAL: Geen extra wettelijke verplichtingen.
    """

    VERBODEN = "verboden"
    HIGH_RISK = "high_risk"
    BEPERKT = "beperkt"
    MINIMAAL = "minimaal"


class HITLVerplichting(str, Enum):
    """
    Niveau van Human-in-the-Loop verplichting conform Artikel 14.

    - VERPLICHT: Menselijk toezicht is wettelijk vereist vóór uitvoering van
      de beslissing (geldt voor alle HIGH-RISK agents in VorstersNV).
    - AANBEVOLEN: Geen wettelijke verplichting, maar sterk aanbevolen o.b.v.
      intern risicobeleid.
    - NIET_VEREIST: Volledig geautomatiseerde verwerking toegestaan.
    """

    VERPLICHT = "verplicht"
    AANBEVOLEN = "aanbevolen"
    NIET_VEREIST = "niet_vereist"


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class AgentCompliance:
    """
    Compliance-profiel van één Ollama-agent conform EU AI Act.

    Bevat de statische classificatie (risicoklasse, HITL-verplichting,
    artikel-naleving) én het groeiende auditlog van beslissingen.

    Attributes:
        agent_naam: Unieke naam van de agent (komt overeen met YAML-bestandsnaam).
        risicoklasse: EU AI Act risicoklassificatie.
        hitl_verplichting: Niveau van Human-in-the-Loop vereiste.
        artikel_9_gedocumenteerd: True als risicomanagement conform Artikel 9
            is gedocumenteerd (risicoregister aanwezig).
        artikel_13_transparant: True als gebruikersinformatie conform Artikel 13
            wordt verstrekt (agent identificeert zich als AI).
        data_governance_ok: True als PII-bescherming conform Artikel 10 is
            geïmplementeerd (geen onversleutelde persoonsgegevens in prompts).
        laatste_audit: Tijdstip van de meest recente formele audit, of None.
        auditlog: Chronologische lijst van ComplianceAuditEvent dicts.
    """

    agent_naam: str
    risicoklasse: AIActRisicoKlasse
    hitl_verplichting: HITLVerplichting
    artikel_9_gedocumenteerd: bool
    artikel_13_transparant: bool
    data_governance_ok: bool
    laatste_audit: datetime | None
    auditlog: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ComplianceAuditEvent:
    """
    Eén beslissingsrecord voor het EU AI Act auditlog.

    Elk event beschrijft een AI-beslissing: wat er beslist werd, wie er
    toezicht op hield (HITL), en wat de uitkomst was. Dit vormt de basis
    voor het Artikel 17 kwaliteitsbeheersysteem.

    Attributes:
        agent_naam: Naam van de verantwoordelijke agent.
        timestamp: UTC-tijdstip van de beslissing.
        beslissing: Mensleesbare beschrijving van de genomen beslissing.
        trace_id: Uniek correlatie-ID voor end-to-end traceerbaarheid.
        risicoscore: Berekende risicoscore (0–100), alleen relevant voor
            ``fraude_detectie_agent``.
        hitl_toegepast: True als een menselijke operator de beslissing heeft
            beoordeeld vóór uitvoering (Artikel 14).
        operator_id: Identificatie van de operator die HITL uitvoerde, of None
            als HITL niet van toepassing was.
        outcome: Eindresultaat van de beslissing. Geldige waarden:
            ``"goedgekeurd"``, ``"afgewezen"``, ``"geëscaleerd"``.
    """

    agent_naam: str
    timestamp: datetime
    beslissing: str
    trace_id: str
    risicoscore: float | None
    hitl_toegepast: bool
    operator_id: str | None
    outcome: str

    _GELDIGE_OUTCOMES: frozenset[str] = field(
        default=frozenset({"goedgekeurd", "afgewezen", "geëscaleerd"}),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if self.outcome not in self._GELDIGE_OUTCOMES:
            raise ValueError(
                f"Ongeldig outcome '{self.outcome}'. "
                f"Geldige waarden: {sorted(self._GELDIGE_OUTCOMES)}"
            )
        if self.risicoscore is not None and not (0.0 <= self.risicoscore <= 100.0):
            raise ValueError(
                f"risicoscore moet tussen 0.0 en 100.0 liggen, "
                f"maar was {self.risicoscore}"
            )


@dataclass
class ComplianceRapport:
    """
    Periodiek compliance-rapport conform Artikel 17 kwaliteitsbeheersysteem.

    Geeft een geaggregeerd beeld van compliance over een opgegeven periode:
    hoe vaak HITL werd toegepast, wat de compliance-score is, en welke
    verbeterpunten zijn geïdentificeerd.

    Attributes:
        aangemaakt_op: UTC-tijdstip van rapportgeneratie.
        periode_start: Begin van de geanalyseerde periode (inclusief).
        periode_eind: Einde van de geanalyseerde periode (inclusief).
        agents: Lijst van AgentCompliance-profielen die zijn meegenomen.
        totaal_besluiten: Totaal aantal AI-beslissingen in de periode.
        hitl_interventies: Aantal beslissingen waarbij HITL werd toegepast.
        hitl_interventie_percentage: Percentage HITL t.o.v. totaal (0.0–100.0).
        compliance_score: Gewogen nalevingsscore (0.0–1.0). Een score van 1.0
            betekent volledige naleving van alle artikelen voor alle HIGH-RISK
            agents; 0.0 betekent geen naleving.
        bevindingen: Lijst van geconstateerde compliance-issues.
        aanbevelingen: Lijst van concrete verbeteracties.
    """

    aangemaakt_op: datetime
    periode_start: datetime
    periode_eind: datetime
    agents: list[AgentCompliance]
    totaal_besluiten: int
    hitl_interventies: int
    hitl_interventie_percentage: float
    compliance_score: float
    bevindingen: list[str]
    aanbevelingen: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────


class AIActComplianceEngine:
    """
    Centrale EU AI Act compliance engine voor VorstersNV.

    Beheert de classificaties van alle Ollama-agents, registreert beslissingen
    in het auditlog en genereert compliance-rapporten en Artikel 9 dossiers.

    De engine werkt in-memory. Voor productie-gebruik dient het auditlog
    gepersisteerd te worden naar de ``compliance_audit_log`` PostgreSQL-tabel
    (TODO).

    Gebruik via de module-level singleton::

        from ollama.ai_act_compliance import get_compliance_engine
        engine = get_compliance_engine()
    """

    # ── Statische agent classificaties ──────────────────────────────────────

    #: Alle HIGH-RISK agents van VorstersNV met hun volledige compliance-profiel.
    #: Agents die hier niet zijn opgenomen worden als MINIMAAL geclassificeerd.
    AGENT_CLASSIFICATIES: dict[str, AgentCompliance] = {
        "fraude_detectie_agent": AgentCompliance(
            agent_naam="fraude_detectie_agent",
            risicoklasse=AIActRisicoKlasse.HIGH_RISK,
            hitl_verplichting=HITLVerplichting.VERPLICHT,
            artikel_9_gedocumenteerd=True,
            artikel_13_transparant=True,
            data_governance_ok=True,
            laatste_audit=None,
            auditlog=[],
        ),
        "order_verwerking_agent": AgentCompliance(
            agent_naam="order_verwerking_agent",
            risicoklasse=AIActRisicoKlasse.HIGH_RISK,
            hitl_verplichting=HITLVerplichting.VERPLICHT,
            artikel_9_gedocumenteerd=True,
            artikel_13_transparant=True,
            data_governance_ok=True,
            laatste_audit=None,
            auditlog=[],
        ),
        # Overige agents: BEPERKT risikoklasse — transparantieverplichting geldt
        "klantenservice_agent": AgentCompliance(
            agent_naam="klantenservice_agent",
            risicoklasse=AIActRisicoKlasse.BEPERKT,
            hitl_verplichting=HITLVerplichting.AANBEVOLEN,
            artikel_9_gedocumenteerd=False,
            artikel_13_transparant=True,
            data_governance_ok=True,
            laatste_audit=None,
            auditlog=[],
        ),
        "product_beschrijving_agent": AgentCompliance(
            agent_naam="product_beschrijving_agent",
            risicoklasse=AIActRisicoKlasse.MINIMAAL,
            hitl_verplichting=HITLVerplichting.NIET_VEREIST,
            artikel_9_gedocumenteerd=False,
            artikel_13_transparant=False,
            data_governance_ok=True,
            laatste_audit=None,
            auditlog=[],
        ),
    }

    def __init__(self) -> None:
        # Deep copy zodat de instantie-state niet de class-level dict muteert
        self._classificaties: dict[str, AgentCompliance] = {
            naam: copy.deepcopy(profiel)
            for naam, profiel in self.AGENT_CLASSIFICATIES.items()
        }

    # ── Publieke methoden ────────────────────────────────────────────────────

    def get_classificatie(self, agent_naam: str) -> AgentCompliance:
        """
        Geef het compliance-profiel voor een agent.

        Onbekende agents worden automatisch geclassificeerd als MINIMAAL met
        HITL_NIET_VEREIST. Dit profiel wordt gecached voor hergebruik.

        Args:
            agent_naam: Naam van de Ollama-agent.

        Returns:
            Het ``AgentCompliance``-profiel voor deze agent.
        """
        if agent_naam not in self._classificaties:
            logger.debug(
                "Agent '%s' niet in classificaties — standaard MINIMAAL toegewezen.",
                agent_naam,
            )
            standaard = AgentCompliance(
                agent_naam=agent_naam,
                risicoklasse=AIActRisicoKlasse.MINIMAAL,
                hitl_verplichting=HITLVerplichting.NIET_VEREIST,
                artikel_9_gedocumenteerd=False,
                artikel_13_transparant=False,
                data_governance_ok=True,
                laatste_audit=None,
                auditlog=[],
            )
            self._classificaties[agent_naam] = standaard

        return self._classificaties[agent_naam]

    def log_beslissing(self, event: ComplianceAuditEvent) -> None:
        """
        Registreer een AI-beslissing in het auditlog van de betrokken agent.

        Het event wordt als dict opgeslagen zodat het auditlog JSON-serialiseerbaar
        blijft. De ``laatste_audit`` van het agent-profiel wordt bijgewerkt.

        Args:
            event: Het te loggen ``ComplianceAuditEvent``.
        """
        profiel = self.get_classificatie(event.agent_naam)

        audit_entry: dict[str, Any] = {
            "trace_id": event.trace_id,
            "timestamp": event.timestamp.isoformat(),
            "beslissing": event.beslissing,
            "risicoscore": event.risicoscore,
            "hitl_toegepast": event.hitl_toegepast,
            "operator_id": event.operator_id,
            "outcome": event.outcome,
        }
        profiel.auditlog.append(audit_entry)
        profiel.laatste_audit = event.timestamp

        log_level = logging.WARNING if not event.hitl_toegepast and \
            profiel.hitl_verplichting == HITLVerplichting.VERPLICHT else logging.INFO

        logger.log(
            log_level,
            "Compliance beslissing gelogd: agent=%s trace_id=%s outcome=%s "
            "hitl=%s risicoscore=%s",
            event.agent_naam,
            event.trace_id,
            event.outcome,
            event.hitl_toegepast,
            event.risicoscore,
        )

        # Specifieke waarschuwing als HITL verplicht was maar niet toegepast
        if (
            profiel.hitl_verplichting == HITLVerplichting.VERPLICHT
            and not event.hitl_toegepast
        ):
            logger.warning(
                "EU AI Act Artikel 14 schending: agent '%s' vereist HITL maar "
                "beslissing (trace_id=%s) werd zonder menselijk toezicht genomen.",
                event.agent_naam,
                event.trace_id,
            )

    def check_hitl_vereist(
        self,
        agent_naam: str,
        risicoscore: float | None = None,
    ) -> bool:
        """
        Bepaal of Human-in-the-Loop toezicht vereist is voor deze agent/beslissing.

        Naast de statische HITL-verplichting uit het agent-profiel gelden extra
        drempelregels:
        - ``fraude_detectie_agent`` met ``risicoscore > 70`` → altijd HITL,
          ongeacht de statische classificatie.

        Args:
            agent_naam: Naam van de agent die een beslissing gaat nemen.
            risicoscore: Optionele risicoscore (0–100) uit het fraude-model.

        Returns:
            ``True`` als menselijk toezicht vereist is, anders ``False``.
        """
        profiel = self.get_classificatie(agent_naam)

        # Statische verplichting vanuit het compliance-profiel
        if profiel.hitl_verplichting == HITLVerplichting.VERPLICHT:
            logger.debug(
                "HITL verplicht voor agent '%s' (statische classificatie).",
                agent_naam,
            )
            return True

        # Dynamische drempelregel: fraude_detectie_agent met hoge score
        if (
            agent_naam == "fraude_detectie_agent"
            and risicoscore is not None
            and risicoscore > _FRAUDE_HITL_DREMPEL
        ):
            logger.warning(
                "HITL vereist voor '%s' — risicoscore %.1f overschrijdt drempel %.1f "
                "(EU AI Act Artikel 14).",
                agent_naam,
                risicoscore,
                _FRAUDE_HITL_DREMPEL,
            )
            return True

        return False

    def genereer_rapport(
        self,
        periode_start: datetime,
        periode_eind: datetime,
    ) -> ComplianceRapport:
        """
        Genereer een periodiek compliance-rapport conform Artikel 17.

        Analyseert alle gelogde beslissingen in de opgegeven periode voor alle
        agents. Berekent de compliance-score op basis van:
        - Naleving van artikel-vereisten per HIGH-RISK agent (60% gewicht)
        - HITL-toepassing bij verplichte beslissingen (40% gewicht)

        Args:
            periode_start: Begin van de te analyseren periode (UTC, inclusief).
            periode_eind: Einde van de te analyseren periode (UTC, inclusief).

        Returns:
            Een volledig ingevuld ``ComplianceRapport``.
        """
        bevindingen: list[str] = []
        aanbevelingen: list[str] = []
        totaal_besluiten = 0
        hitl_interventies = 0
        hitl_verplicht_maar_niet_toegepast = 0

        # Analyseer auditlog per agent
        for profiel in self._classificaties.values():
            events_in_periode = [
                e for e in profiel.auditlog
                if _parse_iso(e["timestamp"]) is not None
                and periode_start <= _parse_iso(e["timestamp"]) <= periode_eind  # type: ignore[operator]
            ]

            totaal_besluiten += len(events_in_periode)

            for event in events_in_periode:
                if event.get("hitl_toegepast"):
                    hitl_interventies += 1
                elif profiel.hitl_verplichting == HITLVerplichting.VERPLICHT:
                    hitl_verplicht_maar_niet_toegepast += 1

            # Bevindingen per agent
            if profiel.risicoklasse == AIActRisicoKlasse.HIGH_RISK:
                if not profiel.artikel_9_gedocumenteerd:
                    bevindingen.append(
                        f"Artikel 9: Risicodocumentatie ontbreekt voor '{profiel.agent_naam}'."
                    )
                    aanbevelingen.append(
                        f"Stel een risicoregister op voor '{profiel.agent_naam}' "
                        f"conform EU AI Act Artikel 9 §2."
                    )
                if not profiel.artikel_13_transparant:
                    bevindingen.append(
                        f"Artikel 13: Transparantie-informatie ontbreekt "
                        f"voor '{profiel.agent_naam}'."
                    )
                    aanbevelingen.append(
                        f"Voeg een AI-disclosure toe aan alle gebruikersinteracties "
                        f"van '{profiel.agent_naam}' (Artikel 13 §1)."
                    )
                if not profiel.data_governance_ok:
                    bevindingen.append(
                        f"Artikel 10: Data governance niet conform voor '{profiel.agent_naam}'."
                    )
                    aanbevelingen.append(
                        f"Implementeer PII-anonimisering in de datapijplijn van "
                        f"'{profiel.agent_naam}' (Artikel 10 §3)."
                    )
                if profiel.laatste_audit is None:
                    bevindingen.append(
                        f"Artikel 17: Geen formele audit geregistreerd voor "
                        f"'{profiel.agent_naam}'."
                    )
                    aanbevelingen.append(
                        f"Plan een initiële compliance-audit voor '{profiel.agent_naam}' "
                        f"en registreer deze in het kwaliteitsbeheersysteem."
                    )

        # HITL-analyse
        if hitl_verplicht_maar_niet_toegepast > 0:
            bevindingen.append(
                f"Artikel 14: {hitl_verplicht_maar_niet_toegepast} beslissing(en) "
                f"genomen zonder verplicht menselijk toezicht."
            )
            aanbevelingen.append(
                "Implementeer een HITL-gate in de agent-uitvoerpipeline die "
                "automatisch blokkeert tot een operator goedkeuring geeft "
                "voor HIGH-RISK beslissingen (Artikel 14 §1)."
            )

        # Bereken compliance-score
        compliance_score = _bereken_compliance_score(
            classificaties=list(self._classificaties.values()),
            totaal_besluiten=totaal_besluiten,
            hitl_verplicht_niet_toegepast=hitl_verplicht_maar_niet_toegepast,
        )

        hitl_pct = (
            (hitl_interventies / totaal_besluiten * 100.0)
            if totaal_besluiten > 0
            else 0.0
        )

        rapport = ComplianceRapport(
            aangemaakt_op=datetime.now(timezone.utc),
            periode_start=periode_start,
            periode_eind=periode_eind,
            agents=list(self._classificaties.values()),
            totaal_besluiten=totaal_besluiten,
            hitl_interventies=hitl_interventies,
            hitl_interventie_percentage=round(hitl_pct, 2),
            compliance_score=round(compliance_score, 4),
            bevindingen=bevindingen,
            aanbevelingen=aanbevelingen,
        )

        logger.info(
            "Compliance rapport gegenereerd: periode=%s–%s score=%.2f "
            "besluiten=%d hitl=%d bevindingen=%d",
            periode_start.date(),
            periode_eind.date(),
            compliance_score,
            totaal_besluiten,
            hitl_interventies,
            len(bevindingen),
        )
        return rapport

    def exporteer_artikel9_dossier(self, agent_naam: str) -> dict[str, Any]:
        """
        Exporteer het Artikel 9 risicomanagement-dossier voor een agent.

        Het dossier voldoet aan de structuurvereisten van EU AI Act Artikel 9 §9:
        identificatie van risico's, beschrijving van mitigerende maatregelen,
        en een audittrail van beslissingen.

        Args:
            agent_naam: Naam van de agent waarvoor het dossier wordt opgesteld.

        Returns:
            JSON-compatibel dict met het volledige Artikel 9 dossier.

        Raises:
            KeyError: Als de agent niet in de classificaties is opgenomen.
        """
        if agent_naam not in self._classificaties:
            raise KeyError(
                f"Agent '{agent_naam}' niet gevonden in compliance-classificaties. "
                f"Beschikbare agents: {sorted(self._classificaties.keys())}"
            )

        profiel = self._classificaties[agent_naam]

        # Risico-matrix conform Artikel 9 §2(a): identificatie en analyse
        risico_matrix: list[dict[str, str]] = []
        if profiel.risicoklasse == AIActRisicoKlasse.HIGH_RISK:
            risico_matrix = [
                {
                    "risico_id": "R-001",
                    "beschrijving": (
                        "Onjuiste of onterechte blokkering met financiële impact op gebruiker."
                    ),
                    "kans": "laag",
                    "impact": "hoog",
                    "restrisico": "aanvaardbaar",
                    "maatregel": "HITL-goedkeuring verplicht voor alle blokkeer-beslissingen.",
                },
                {
                    "risico_id": "R-002",
                    "beschrijving": "Discriminatie door biased trainingsdata (Artikel 10 §2).",
                    "kans": "middel",
                    "impact": "hoog",
                    "restrisico": "aanvaardbaar",
                    "maatregel": "Regelmatige bias-evaluatie; diverse en representatieve datasets.",
                },
                {
                    "risico_id": "R-003",
                    "beschrijving": "Datalekrisico: PII in agent-prompts of responses.",
                    "kans": "laag",
                    "impact": "hoog",
                    "restrisico": "aanvaardbaar",
                    "maatregel": "PII-anonimisering vóór invoer in model; geen PII in auditlogs.",
                },
                {
                    "risico_id": "R-004",
                    "beschrijving": "Model-drift: verslechterende beslissingsnauwkeurigheid.",
                    "kans": "middel",
                    "impact": "middel",
                    "restrisico": "aanvaardbaar",
                    "maatregel": "Maandelijkse kwaliteitsmonitoring via quality_gates.py.",
                },
            ]

        # Mitigerende maatregelen conform Artikel 9 §2(c)
        maatregelen: list[dict[str, str]] = [
            {
                "maatregel_id": "M-001",
                "artikel": "Artikel 9",
                "beschrijving": "Risicoregister bijgehouden in ai_act_compliance.py.",
                "status": "geïmplementeerd" if profiel.artikel_9_gedocumenteerd else "ontbreekt",
            },
            {
                "maatregel_id": "M-002",
                "artikel": "Artikel 10",
                "beschrijving": "PII-bescherming in datapijplijn voor modelbeslissingen.",
                "status": "geïmplementeerd" if profiel.data_governance_ok else "ontbreekt",
            },
            {
                "maatregel_id": "M-003",
                "artikel": "Artikel 13",
                "beschrijving": "AI-disclosure in gebruikersinterfaces en API-responses.",
                "status": "geïmplementeerd" if profiel.artikel_13_transparant else "ontbreekt",
            },
            {
                "maatregel_id": "M-004",
                "artikel": "Artikel 14",
                "beschrijving": "Human-in-the-Loop gate in agent-uitvoerpipeline.",
                "status": "verplicht" if profiel.hitl_verplichting == HITLVerplichting.VERPLICHT
                else "niet vereist",
            },
            {
                "maatregel_id": "M-005",
                "artikel": "Artikel 17",
                "beschrijving": "Kwaliteitsbeheersysteem met periodieke compliance-rapporten.",
                "status": "geïmplementeerd",
            },
        ]

        dossier: dict[str, Any] = {
            "dossier_id": str(uuid.uuid4()),
            "aangemaakt_op": datetime.now(timezone.utc).isoformat(),
            "wettelijke_basis": "EU AI Act (Verordening (EU) 2024/1689), Artikel 9",
            "agent_informatie": {
                "agent_naam": profiel.agent_naam,
                "risicoklasse": profiel.risicoklasse.value,
                "hitl_verplichting": profiel.hitl_verplichting.value,
                "annex_iii_categorie": "5(b) — Krediet/risicobeoordeling met financiële impact"
                if profiel.risicoklasse == AIActRisicoKlasse.HIGH_RISK
                else "Niet van toepassing",
            },
            "artikel_naleving": {
                "artikel_9_risicomanagement": profiel.artikel_9_gedocumenteerd,
                "artikel_10_data_governance": profiel.data_governance_ok,
                "artikel_13_transparantie": profiel.artikel_13_transparant,
                "artikel_14_hitl": profiel.hitl_verplichting == HITLVerplichting.VERPLICHT,
                "artikel_17_kwaliteitsbeheer": True,
            },
            "risico_matrix": risico_matrix,
            "maatregelen": maatregelen,
            "audittrail": {
                "totaal_beslissingen": len(profiel.auditlog),
                "laatste_audit": profiel.laatste_audit.isoformat()
                if profiel.laatste_audit
                else None,
                "recentste_events": profiel.auditlog[-10:],
            },
            "technische_documentatie": {
                "module": "ollama/ai_act_compliance.py",
                "agent_yaml": f"ollama/agents/{profiel.agent_naam}.yaml",
                "policy_engine": "ollama/policy_engine.py",
                "decision_journal": "ollama/decision_journal.py",
                "kwaliteitsmonitoring": "ollama/quality_monitor.py",
            },
        }

        logger.info(
            "Artikel 9 dossier geëxporteerd voor agent '%s' "
            "(dossier_id=%s, %d auditlog entries).",
            agent_naam,
            dossier["dossier_id"],
            len(profiel.auditlog),
        )
        return dossier


# ─────────────────────────────────────────────────────────────────────────────
# Hulpfuncties (intern)
# ─────────────────────────────────────────────────────────────────────────────


def _parse_iso(timestamp_str: str) -> datetime | None:
    """
    Parseer een ISO 8601 timestamp-string naar een timezone-aware datetime.

    Args:
        timestamp_str: ISO 8601 string (bijv. "2024-08-01T12:00:00+00:00").

    Returns:
        UTC ``datetime`` of ``None`` bij parseerfout.
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        logger.debug("Kon timestamp niet parseren: '%s'", timestamp_str)
        return None


def _bereken_compliance_score(
    classificaties: list[AgentCompliance],
    totaal_besluiten: int,
    hitl_verplicht_niet_toegepast: int,
) -> float:
    """
    Bereken de gewogen compliance-score (0.0–1.0).

    Gewichten:
    - 60%: Artikel-naleving per HIGH-RISK agent
      (artikel_9, artikel_13, data_governance elk 1/3 van dit gewicht)
    - 40%: HITL-naleving (verhouding correct-HITL vs verplichte besluiten)

    Args:
        classificaties: Alle agent-profielen.
        totaal_besluiten: Totaal aantal beslissingen in periode.
        hitl_verplicht_niet_toegepast: Beslissingen zonder verplichte HITL.

    Returns:
        Score tussen 0.0 (geen naleving) en 1.0 (volledige naleving).
    """
    high_risk_agents = [
        p for p in classificaties
        if p.risicoklasse == AIActRisicoKlasse.HIGH_RISK
    ]

    # Artikel-naleving score (60% gewicht)
    if high_risk_agents:
        artikel_checks: list[bool] = []
        for profiel in high_risk_agents:
            artikel_checks.extend([
                profiel.artikel_9_gedocumenteerd,
                profiel.artikel_13_transparant,
                profiel.data_governance_ok,
            ])
        artikel_score = sum(artikel_checks) / len(artikel_checks)
    else:
        artikel_score = 1.0  # geen HIGH-RISK agents → volledige naleving

    # HITL-naleving score (40% gewicht)
    if totaal_besluiten > 0:
        hitl_score = max(
            0.0,
            1.0 - (hitl_verplicht_niet_toegepast / totaal_besluiten),
        )
    else:
        hitl_score = 1.0  # geen beslissingen → geen schendingen

    gewogen_score = (0.6 * artikel_score) + (0.4 * hitl_score)
    return max(0.0, min(1.0, gewogen_score))


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_engine: AIActComplianceEngine | None = None


def get_compliance_engine() -> AIActComplianceEngine:
    """
    Geef de module-level singleton ``AIActComplianceEngine`` terug.

    De engine wordt lazy geïnitialiseerd bij het eerste aanroepen.
    Thread-safety is niet gegarandeerd voor multi-threaded omgevingen;
    gebruik in asyncio-context is veilig.

    Returns:
        De gedeelde ``AIActComplianceEngine`` instantie.
    """
    global _engine
    if _engine is None:
        _engine = AIActComplianceEngine()
        logger.info("AIActComplianceEngine singleton geïnitialiseerd.")
    return _engine


# ─────────────────────────────────────────────────────────────────────────────
# Decorator
# ─────────────────────────────────────────────────────────────────────────────


def eu_ai_act_log(agent_naam: str) -> Callable[[_F], _F]:
    """
    Decorator voor async functies die AI-beslissingen nemen.

    Logt automatisch elke aanroep in het EU AI Act auditlog en geeft een
    WARNING als HITL vereist is maar niet in de keyword-argumenten is
    aangetroffen.

    Verwachte keyword-argumenten in de gedecoreerde functie (optioneel):

    - ``trace_id`` (str): correlatie-ID; wordt automatisch aangemaakt als afwezig.
    - ``risicoscore`` (float): risicoscore voor HITL-drempelcheck.
    - ``hitl_toegepast`` (bool): of HITL werd uitgevoerd.
    - ``operator_id`` (str | None): ID van de menselijke operator.
    - ``outcome`` (str): resultaat van de beslissing.

    Voorbeeld::

        @eu_ai_act_log("fraude_detectie_agent")
        async def voer_fraudecheck_uit(order_id: str, risicoscore: float) -> dict:
            ...

    Args:
        agent_naam: Naam van de agent waarvoor de beslissing gelogd wordt.

    Returns:
        Decorator-functie die de originele async functie omhult.
    """
    def decorator(func: _F) -> _F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            risicoscore: float | None = kwargs.get("risicoscore")  # type: ignore[assignment]
            trace_id: str = kwargs.get("trace_id") or str(uuid.uuid4())  # type: ignore[assignment]

            engine = get_compliance_engine()

            # Controleer HITL-verplichting vóór uitvoering
            if engine.check_hitl_vereist(agent_naam, risicoscore=risicoscore):
                logger.warning(
                    "HITL vereist voor '%s' (trace_id=%s) — beslissing vereist "
                    "menselijke goedkeuring voor uitvoering (EU AI Act Artikel 14).",
                    agent_naam,
                    trace_id,
                )

            result = await func(*args, **kwargs)

            # Bepaal uitkomst voor het auditlog
            hitl_toegepast: bool = bool(kwargs.get("hitl_toegepast", False))
            operator_id: str | None = kwargs.get("operator_id")  # type: ignore[assignment]
            outcome: str = kwargs.get("outcome", "goedgekeurd")  # type: ignore[assignment]

            # Normaliseer outcome naar geldige waarden
            if outcome not in {"goedgekeurd", "afgewezen", "geëscaleerd"}:
                outcome = "goedgekeurd"

            try:
                event = ComplianceAuditEvent(
                    agent_naam=agent_naam,
                    timestamp=datetime.now(timezone.utc),
                    beslissing=f"Automatisch gelogd via @eu_ai_act_log voor {func.__name__}",
                    trace_id=trace_id,
                    risicoscore=risicoscore,
                    hitl_toegepast=hitl_toegepast,
                    operator_id=operator_id,
                    outcome=outcome,
                )
                engine.log_beslissing(event)
            except (ValueError, TypeError) as exc:
                # Nooit de hoofdfunctie blokkeren door een logging-fout
                logger.error(
                    "Fout bij loggen van compliance event voor '%s': %s",
                    agent_naam,
                    exc,
                )

            return result

        return wrapper  # type: ignore[return-value]

    return decorator  # type: ignore[return-value]
