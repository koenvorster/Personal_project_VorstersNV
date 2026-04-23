"""
VorstersNV Self-Improvement Loop

Hart van het autonome verbeteringsproces: feedback verzamelen, analyseren,
verbetervoorstellen genereren en agents automatisch promoten.

Revisie 5 architectuur — SELF_IMPROVEMENT laag.

Gebruik::

    from ollama.self_improvement import get_self_improvement_loop

    loop = get_self_improvement_loop()
    resultaat = await loop.run_cyclus(trace_id="abc-123")
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Optionele imports
# ─────────────────────────────────────────────

try:
    from ollama.agent_versioning import (
        AgentVersionRegistry,
        VersionBump,
        _bump_version,
        get_agent_version_registry,
    )
    _HAS_VERSIONING = True
except ImportError:
    AgentVersionRegistry = None        # type: ignore[assignment, misc]
    VersionBump = None                 # type: ignore[assignment]
    _bump_version = None               # type: ignore[assignment]
    get_agent_version_registry = None  # type: ignore[assignment]
    _HAS_VERSIONING = False
    logger.debug("agent_versioning niet beschikbaar — versioning uitgeschakeld")

try:
    from ollama.decision_journal import (
        DecisionJournal,
        JournalEntry,
        get_decision_journal,
    )
    _HAS_JOURNAL = True
except ImportError:
    DecisionJournal = None     # type: ignore[assignment, misc]
    JournalEntry = None        # type: ignore[assignment, misc]
    get_decision_journal = None  # type: ignore[assignment]
    _HAS_JOURNAL = False
    logger.debug("decision_journal niet beschikbaar — journaling uitgeschakeld")

try:
    from ollama.client import OllamaClient
    from ollama.client import get_client as get_ollama_client
    _HAS_OLLAMA = True
except ImportError:
    OllamaClient = None          # type: ignore[assignment, misc]
    get_ollama_client = None     # type: ignore[assignment]
    _HAS_OLLAMA = False
    logger.debug("OllamaClient niet beschikbaar — LLM-generatie uitgeschakeld")

# ─────────────────────────────────────────────
# Constanten
# ─────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).parent.parent
_LOGS_DIR = _PROJECT_ROOT / "logs"
_FEEDBACK_DIR = _LOGS_DIR / "feedback"
_PROPOSALS_DIR = _FEEDBACK_DIR / "proposals"

_DREMPELWAARDE_ZWAK: float = 3.5      # scores < dit → verbetering nodig
_SCORE_MAJOR_BUMP: float = 2.5        # < 2.5 → MAJOR bump
_SCORE_MINOR_BUMP: float = 3.5        # 2.5..3.5 → MINOR bump, anders PATCH

_CANARY_MIN_RUNS: int = 50            # minimale runs voor auto-promotie naar CANARY
_CANARY_MIN_SCORE: float = 0.8        # minimale eval_score (0.0–1.0) voor auto-promotie

# Talen die gedetecteerd worden in opmerkingen
_BEKENDE_TALEN = ["python", "java", "php", "c#", "javascript", "typescript", "go", "ruby"]

# Sectie-tips mapping (sectienaam → actiepunt)
_SECTIE_TIPS: dict[str, str] = {
    "kwaliteit":     "Voeg meer concrete voorbeelden toe aan de system prompt",
    "duidelijkheid": "Gebruik kortere zinnen en opsommingen",
    "bruikbaarheid": "Voeg actionable aanbevelingen toe met prioriteit",
    "volledigheid":  "Zorg dat alle aspecten (technisch, proces, risico) behandeld worden",
    "aanbevelingen": "Maak aanbevelingen specifieker met ROI-schatting",
}


# ─────────────────────────────────────────────
# Hulpfuncties
# ─────────────────────────────────────────────

def _nu_iso() -> str:
    """Geef de huidige UTC-tijd terug als ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _lokale_bump_version(current: str, bump_type: str) -> str:
    """
    Bereken een nieuwe SemVer-string zonder agent_versioning import (fallback).

    Args:
        current:   Huidige versie als ``"X.Y.Z"`` string.
        bump_type: ``"major"``, ``"minor"`` of ``"patch"``.

    Returns:
        Nieuwe versie-string, of de originele string bij een parseerfout.
    """
    parts = current.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return current
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _bereken_volgende_versie(huidige: str, bump_type: str) -> str:
    """
    Bereken de volgende versie via agent_versioning of de lokale fallback.

    Args:
        huidige:   Huidige SemVer-string.
        bump_type: ``"major"``, ``"minor"`` of ``"patch"``.

    Returns:
        Nieuwe SemVer-string.
    """
    if _HAS_VERSIONING and _bump_version is not None and VersionBump is not None:
        try:
            bump = VersionBump(bump_type)
            return _bump_version(huidige, bump)
        except Exception:
            pass
    return _lokale_bump_version(huidige, bump_type)


# ─────────────────────────────────────────────
# FeedbackRecord
# ─────────────────────────────────────────────

@dataclass
class FeedbackRecord:
    """
    Één feedback-beoordeling voor een agent-uitvoering.

    Attributes:
        feedback_id:     Uniek UUID van deze beoordeling.
        project_id:      Klant- of project-identifier.
        agent_name:      Naam van de beoordeelde agent.
        prompt_version:  SemVer van de prompt tijdens uitvoering (bijv. ``"1.0.0"``).
        ratings:         Sectienaam → score (1–5).
        gemiddelde_score: Gewogen gemiddelde van alle sectiescores.
        opmerking:       Optionele vrije tekstnoot.
        beoordelaar:     ``"klant"`` | ``"consultant"`` | ``"auto"``.
        trace_id:        Koppeling met een specifieke agent-uitvoering of None.
        aangemaakt_op:   ISO 8601 UTC-tijdstempel.
    """

    feedback_id: str
    project_id: str
    agent_name: str
    prompt_version: str
    ratings: dict[str, int]
    gemiddelde_score: float
    opmerking: str | None
    beoordelaar: str
    trace_id: str | None
    aangemaakt_op: str

    # ─── Factory ──────────────────────────────────────────────────

    @classmethod
    def nieuw(
        cls,
        project_id: str,
        agent_name: str,
        prompt_version: str,
        ratings: dict[str, int],
        opmerking: str | None = None,
        beoordelaar: str = "auto",
        trace_id: str | None = None,
    ) -> FeedbackRecord:
        """
        Maak een nieuw FeedbackRecord aan met automatisch berekend gemiddelde.

        Args:
            project_id:    Project- of klant-identifier.
            agent_name:    Naam van de agent.
            prompt_version: Versie van de prompt.
            ratings:       Sectie → score (1–5) mapping.
            opmerking:     Optionele tekstnoot.
            beoordelaar:   Wie de beoordeling heeft gegeven.
            trace_id:      Koppeling aan specifieke uitvoering.

        Returns:
            Nieuw :class:`FeedbackRecord` met berekend gemiddelde.
        """
        gemiddelde = (
            round(sum(ratings.values()) / len(ratings), 3) if ratings else 0.0
        )
        return cls(
            feedback_id=str(uuid.uuid4()),
            project_id=project_id,
            agent_name=agent_name,
            prompt_version=prompt_version,
            ratings=ratings,
            gemiddelde_score=gemiddelde,
            opmerking=opmerking,
            beoordelaar=beoordelaar,
            trace_id=trace_id,
            aangemaakt_op=_nu_iso(),
        )

    # ─── Serialisatie ─────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar een JSON-compatibel dict."""
        return {
            "feedback_id":    self.feedback_id,
            "project_id":     self.project_id,
            "agent_name":     self.agent_name,
            "prompt_version": self.prompt_version,
            "ratings":        self.ratings,
            "gemiddelde_score": self.gemiddelde_score,
            "opmerking":      self.opmerking,
            "beoordelaar":    self.beoordelaar,
            "trace_id":       self.trace_id,
            "aangemaakt_op":  self.aangemaakt_op,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FeedbackRecord:
        """Deserialiseer vanuit een dict (bijv. geladen JSON)."""
        return cls(
            feedback_id=    d["feedback_id"],
            project_id=     d["project_id"],
            agent_name=     d["agent_name"],
            prompt_version= d["prompt_version"],
            ratings=        d["ratings"],
            gemiddelde_score=float(d["gemiddelde_score"]),
            opmerking=      d.get("opmerking"),
            beoordelaar=    d["beoordelaar"],
            trace_id=       d.get("trace_id"),
            aangemaakt_op=  d["aangemaakt_op"],
        )


# ─────────────────────────────────────────────
# AgentPerformanceProfile
# ─────────────────────────────────────────────

@dataclass
class AgentPerformanceProfile:
    """
    Geaggregeerd prestatieprofiel van een agent op basis van feedback.

    Attributes:
        agent_name:            Naam van de agent.
        prompt_version:        Laatste gebruikte prompt-versie.
        totaal_beoordelingen:  Aantal FeedbackRecords meegenomen in dit profiel.
        gemiddelde_per_sectie: Sectienaam → gemiddelde score (1.0–5.0).
        algeheel_gemiddelde:   Ongewogen gemiddelde over alle records.
        zwakste_sectie:        Sectie met de laagste gemiddelde score, of None.
        taal_breakdown:        Programmeertaal → gemiddelde score voor die taal.
        trend:                 ``"stijgend"`` | ``"dalend"`` | ``"stabiel"``.
        verbetering_nodig:     True als algeheel_gemiddelde < 3.5.
    """

    agent_name: str
    prompt_version: str
    totaal_beoordelingen: int
    gemiddelde_per_sectie: dict[str, float]
    algeheel_gemiddelde: float
    zwakste_sectie: str | None
    taal_breakdown: dict[str, float]
    trend: str
    verbetering_nodig: bool


# ─────────────────────────────────────────────
# ImprovementProposal
# ─────────────────────────────────────────────

@dataclass
class ImprovementProposal:
    """
    Voorstel voor verbetering van een agent-prompt.

    Attributes:
        proposal_id:          Uniek UUID.
        agent_name:           Naam van de te verbeteren agent.
        huidige_versie:       Huidige SemVer van de prompt.
        voorgestelde_versie:  Automatisch berekende nieuwe SemVer.
        bump_type:            ``"major"`` | ``"minor"`` | ``"patch"``.
        probleembeschrijving: Samenvatting van wat slecht scoort.
        voorgestelde_wijziging: LLM- of rule-based verbeterd systeem-prompt.
        verwachte_verbetering: Verwacht scoreherstel (0.0–1.0).
        requires_human_review: True bij MAJOR bump.
        aangemaakt_op:        ISO 8601 UTC-tijdstempel.
        status:               ``"draft"`` | ``"shadow_testing"`` | ``"goedgekeurd"`` | ``"afgewezen"``.
    """

    proposal_id: str
    agent_name: str
    huidige_versie: str
    voorgestelde_versie: str
    bump_type: str
    probleembeschrijving: str
    voorgestelde_wijziging: str
    verwachte_verbetering: float
    requires_human_review: bool
    aangemaakt_op: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar een JSON-compatibel dict."""
        return {
            "proposal_id":           self.proposal_id,
            "agent_name":            self.agent_name,
            "huidige_versie":        self.huidige_versie,
            "voorgestelde_versie":   self.voorgestelde_versie,
            "bump_type":             self.bump_type,
            "probleembeschrijving":  self.probleembeschrijving,
            "voorgestelde_wijziging": self.voorgestelde_wijziging,
            "verwachte_verbetering": self.verwachte_verbetering,
            "requires_human_review": self.requires_human_review,
            "aangemaakt_op":         self.aangemaakt_op,
            "status":                self.status,
        }


# ─────────────────────────────────────────────
# FeedbackStore
# ─────────────────────────────────────────────

@dataclass
class FeedbackStore:
    """
    In-memory feedback-opslag met JSON-persistentie.

    Records worden automatisch geladen vanuit en opgeslagen naar
    ``logs/feedback/feedback_store.json``.  De opslagmap wordt aangemaakt
    als die nog niet bestaat.

    Attributes:
        _records:    In-memory lijst van FeedbackRecord objecten.
        _store_path: Pad naar het persistente JSON-bestand.
    """

    _records:    list[FeedbackRecord] = field(default_factory=list)
    _store_path: Path = field(
        default_factory=lambda: _FEEDBACK_DIR / "feedback_store.json"
    )

    def __post_init__(self) -> None:
        """Zorg dat de opslagmap bestaat en laad bestaande records."""
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        if self._store_path.exists():
            self.load()

    # ─── Mutatoren ────────────────────────────────────────────────

    def add_record(self, record: FeedbackRecord) -> None:
        """
        Voeg een FeedbackRecord toe en sla direct op.

        Args:
            record: Het toe te voegen record.
        """
        self._records.append(record)
        self.save()
        logger.debug(
            "Feedback record toegevoegd: feedback_id=%s agent=%s score=%.2f",
            record.feedback_id, record.agent_name, record.gemiddelde_score,
        )

    # ─── Opvragen ─────────────────────────────────────────────────

    def get_records_for_agent(
        self,
        agent_name: str,
        prompt_version: str | None = None,
    ) -> list[FeedbackRecord]:
        """
        Geef records terug voor een specifieke agent, optioneel op versie gefilterd.

        Args:
            agent_name:     Naam van de agent.
            prompt_version: Filter op exacte versiestring, of None voor alle versies.

        Returns:
            Gefilterde lijst van FeedbackRecord objecten.
        """
        records = [r for r in self._records if r.agent_name == agent_name]
        if prompt_version is not None:
            records = [r for r in records if r.prompt_version == prompt_version]
        return records

    def get_records_for_project(self, project_id: str) -> list[FeedbackRecord]:
        """
        Geef alle records voor een project terug.

        Args:
            project_id: Klant- of project-identifier.

        Returns:
            Lijst van bijbehorende FeedbackRecord objecten.
        """
        return [r for r in self._records if r.project_id == project_id]

    def get_alle_records(self) -> list[FeedbackRecord]:
        """Geef een kopie van alle records terug."""
        return list(self._records)

    # ─── Persistentie ─────────────────────────────────────────────

    def save(self) -> None:
        """Sla alle records geserialiseerd op naar het JSON-bestand."""
        try:
            data = [r.to_dict() for r in self._records]
            self._store_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.debug("FeedbackStore opgeslagen: %d records", len(self._records))
        except OSError as exc:
            logger.error("FeedbackStore opslaan mislukt: %s", exc)

    def load(self) -> None:
        """Laad records vanuit het JSON-bestand en overschrijf de in-memory lijst."""
        try:
            raw: list[dict[str, Any]] = json.loads(
                self._store_path.read_text(encoding="utf-8")
            )
            self._records = [FeedbackRecord.from_dict(d) for d in raw]
            logger.debug("FeedbackStore geladen: %d records", len(self._records))
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("FeedbackStore laden mislukt: %s — lege store", exc)
            self._records = []


# ─────────────────────────────────────────────
# FeedbackAnalyzer
# ─────────────────────────────────────────────

class FeedbackAnalyzer:
    """
    Analyseert feedback-patronen en identificeert verbeterpunten.

    Berekent scores per sectie, detecteert trends en signaleert welke agents
    verbetering nodig hebben via een drempelwaarde-check.

    Args:
        store: De FeedbackStore waaruit records worden gelezen.
    """

    def __init__(self, store: FeedbackStore) -> None:
        self._store = store

    # ─── Analyse ──────────────────────────────────────────────────

    def analyseer_agent(
        self,
        agent_name: str,
        prompt_version: str | None = None,
    ) -> AgentPerformanceProfile:
        """
        Bereken een volledig AgentPerformanceProfile op basis van feedback records.

        - Berekent gemiddelde per sectie over alle records.
        - Detecteert de zwakste sectie (laagste gemiddelde).
        - Berekent trend door eerste vs. tweede helft (tijd-gesorteerd) te vergelijken:
          stijgend als tweede helft > eerste helft + 0.2, dalend als < eerste helft - 0.2.
        - Extraheert taalverdeling door te zoeken naar bekende taalwoorden in opmerkingen.
        - ``verbetering_nodig`` = True als algeheel_gemiddelde < 3.5.

        Args:
            agent_name:     Naam van de agent.
            prompt_version: Optioneel filter op specifieke versie.

        Returns:
            Ingevuld :class:`AgentPerformanceProfile`.
        """
        records = self._store.get_records_for_agent(agent_name, prompt_version)

        if not records:
            return AgentPerformanceProfile(
                agent_name=agent_name,
                prompt_version=prompt_version or "1.0.0",
                totaal_beoordelingen=0,
                gemiddelde_per_sectie={},
                algeheel_gemiddelde=0.0,
                zwakste_sectie=None,
                taal_breakdown={},
                trend="stabiel",
                verbetering_nodig=False,
            )

        # Sorteer op aanmaaktijd voor trend-berekening
        records_gesorteerd = sorted(records, key=lambda r: r.aangemaakt_op)

        # ── Gemiddelde per sectie ──────────────────────────────────
        sectie_scores: dict[str, list[float]] = {}
        for record in records_gesorteerd:
            for sectie, score in record.ratings.items():
                sectie_scores.setdefault(sectie, []).append(float(score))

        gemiddelde_per_sectie: dict[str, float] = {
            sectie: round(sum(scores) / len(scores), 3)
            for sectie, scores in sectie_scores.items()
        }

        # ── Zwakste sectie ────────────────────────────────────────
        zwakste_sectie: str | None = (
            min(gemiddelde_per_sectie, key=lambda k: gemiddelde_per_sectie[k])
            if gemiddelde_per_sectie
            else None
        )

        # ── Algeheel gemiddelde ───────────────────────────────────
        alle_scores = [r.gemiddelde_score for r in records_gesorteerd]
        algeheel_gemiddelde = round(sum(alle_scores) / len(alle_scores), 3)

        # ── Trend ─────────────────────────────────────────────────
        n = len(records_gesorteerd)
        if n >= 2:
            helft = n // 2
            eerste_helft = records_gesorteerd[:helft]
            tweede_helft = records_gesorteerd[helft:]
            gem_eerste = sum(r.gemiddelde_score for r in eerste_helft) / len(eerste_helft)
            gem_tweede = sum(r.gemiddelde_score for r in tweede_helft) / len(tweede_helft)
            if gem_tweede > gem_eerste + 0.2:
                trend = "stijgend"
            elif gem_tweede < gem_eerste - 0.2:
                trend = "dalend"
            else:
                trend = "stabiel"
        else:
            trend = "stabiel"

        # ── Taal-breakdown ────────────────────────────────────────
        taal_scores: dict[str, list[float]] = {}
        for record in records_gesorteerd:
            if record.opmerking:
                opmerking_lower = record.opmerking.lower()
                for taal in _BEKENDE_TALEN:
                    patroon = r"\b" + re.escape(taal) + r"\b"
                    if re.search(patroon, opmerking_lower):
                        taal_scores.setdefault(taal, []).append(record.gemiddelde_score)

        taal_breakdown: dict[str, float] = {
            taal: round(sum(scores) / len(scores), 3)
            for taal, scores in taal_scores.items()
        }

        # Gebruik de versie van het meest recente record als we niet op versie filteren
        gebruikte_versie = prompt_version or records_gesorteerd[-1].prompt_version

        return AgentPerformanceProfile(
            agent_name=agent_name,
            prompt_version=gebruikte_versie,
            totaal_beoordelingen=len(records),
            gemiddelde_per_sectie=gemiddelde_per_sectie,
            algeheel_gemiddelde=algeheel_gemiddelde,
            zwakste_sectie=zwakste_sectie,
            taal_breakdown=taal_breakdown,
            trend=trend,
            verbetering_nodig=algeheel_gemiddelde < _DREMPELWAARDE_ZWAK,
        )

    def detecteer_zwakke_agents(
        self, drempelwaarde: float = _DREMPELWAARDE_ZWAK
    ) -> list[AgentPerformanceProfile]:
        """
        Identificeer alle agents met een algeheel gemiddelde onder de drempelwaarde.

        Args:
            drempelwaarde: Minimale gewenste score (standaard 3.5).

        Returns:
            Gesorteerde lijst van :class:`AgentPerformanceProfile` voor zwakke agents.
        """
        alle_records = self._store.get_alle_records()
        unieke_agents = sorted({r.agent_name for r in alle_records})

        profielen: list[AgentPerformanceProfile] = []
        for agent_name in unieke_agents:
            profiel = self.analyseer_agent(agent_name)
            if profiel.totaal_beoordelingen > 0 and profiel.algeheel_gemiddelde < drempelwaarde:
                profielen.append(profiel)

        logger.info(
            "Zwakke agents gedetecteerd: %d van %d (drempel=%.1f)",
            len(profielen), len(unieke_agents), drempelwaarde,
        )
        return profielen

    def genereer_verbetertips(self, profiel: AgentPerformanceProfile) -> list[str]:
        """
        Genereer regel-gebaseerde verbetertips op basis van het profiel.

        Controleert elke bekende sectie op een score onder 3.5 en koppelt een
        specifieke actiegerichte tip.  Als geen sectie onder 3.5 scoort maar het
        profiel toch verbetering nodig heeft, wordt een generieke tip gegeven.

        Args:
            profiel: Het :class:`AgentPerformanceProfile` dat geanalyseerd wordt.

        Returns:
            Lijst van actiegerichte verbetertips als strings.
        """
        tips: list[str] = []
        for sectie, tip in _SECTIE_TIPS.items():
            score = profiel.gemiddelde_per_sectie.get(sectie)
            if score is not None and score < _DREMPELWAARDE_ZWAK:
                tips.append(tip)

        if not tips and profiel.verbetering_nodig:
            tips.append(
                "Analyseer de laagst scorende sectie en verfijn de system prompt"
            )
        return tips


# ─────────────────────────────────────────────
# PromptImprovementProposer
# ─────────────────────────────────────────────

class PromptImprovementProposer:
    """
    Genereert verbeteringsvoorstellen voor agent-prompts.

    Gebruikt het mistral-model (temperature=0.3) voor deterministische,
    professionele prompt-suggesties.  Bij onbeschikbaarheid van Ollama wordt
    een rule-based fallback toegepast die de verbetertips als instructies
    achter de huidige prompt plaatst.

    Args:
        ollama_client: Optionele OllamaClient instantie.  Als None, wordt de
                       singleton opgehaald via ``get_ollama_client()``.
    """

    _MODEL = "mistral"
    _TEMPERATURE = 0.3
    _MAX_TOKENS = 2048

    def __init__(self, ollama_client: OllamaClient | None = None) -> None:  # type: ignore[valid-type]
        self._client: Any = ollama_client

    # ─── Publieke interface ────────────────────────────────────────

    async def genereer_voorstel(
        self,
        profiel: AgentPerformanceProfile,
        huidige_system_prompt: str,
        tips: list[str],
    ) -> ImprovementProposal:
        """
        Genereer een ImprovementProposal voor de gegeven agent.

        Bepaalt het bump-type op basis van de gemiddelde score:
        - ``major`` als score < 2.5
        - ``minor`` als score < 3.5
        - ``patch`` anders

        Probeert Ollama (mistral, temp=0.3) voor een verbeterd systeem-prompt.
        Valt terug op een rule-based methode bij onbeschikbaarheid.

        Het voorstel wordt opgeslagen in ``logs/feedback/proposals/``.

        Args:
            profiel:              AgentPerformanceProfile van de te verbeteren agent.
            huidige_system_prompt: De huidige system prompt tekst.
            tips:                 Verbetertips van :class:`FeedbackAnalyzer`.

        Returns:
            Ingevuld :class:`ImprovementProposal` met status ``"draft"``.
        """
        # ── Bump type bepalen ──────────────────────────────────────
        if profiel.algeheel_gemiddelde < _SCORE_MAJOR_BUMP:
            bump_type = "major"
        elif profiel.algeheel_gemiddelde < _SCORE_MINOR_BUMP:
            bump_type = "minor"
        else:
            bump_type = "patch"

        voorgestelde_versie = _bereken_volgende_versie(profiel.prompt_version, bump_type)

        # ── Probleembeschrijving opbouwen ──────────────────────────
        zwakke_secties = [
            f"{sectie} ({score:.1f}/5)"
            for sectie, score in sorted(
                profiel.gemiddelde_per_sectie.items(), key=lambda x: x[1]
            )
            if score < _DREMPELWAARDE_ZWAK
        ]
        probleembeschrijving = (
            f"Agent '{profiel.agent_name}' scoort gemiddeld "
            f"{profiel.algeheel_gemiddelde:.2f}/5 "
            f"({profiel.totaal_beoordelingen} beoordelingen). "
        )
        if zwakke_secties:
            probleembeschrijving += f"Zwakke secties: {', '.join(zwakke_secties)}. "
        if profiel.zwakste_sectie:
            probleembeschrijving += f"Zwakste sectie: {profiel.zwakste_sectie}. "
        if profiel.trend == "dalend":
            probleembeschrijving += "Trend is dalend — urgente actie vereist."

        # ── Verbeterd prompt genereren ─────────────────────────────
        voorgestelde_wijziging = await self._genereer_via_ollama(
            profiel=profiel,
            huidige_system_prompt=huidige_system_prompt,
            tips=tips,
            probleembeschrijving=probleembeschrijving,
        )

        # ── Verwachte verbetering inschatten ───────────────────────
        verwachte_verbetering: float
        if bump_type == "major":
            verwachte_verbetering = 0.6
        elif bump_type == "minor":
            verwachte_verbetering = 0.35
        else:
            verwachte_verbetering = 0.15

        proposal = ImprovementProposal(
            proposal_id=str(uuid.uuid4()),
            agent_name=profiel.agent_name,
            huidige_versie=profiel.prompt_version,
            voorgestelde_versie=voorgestelde_versie,
            bump_type=bump_type,
            probleembeschrijving=probleembeschrijving,
            voorgestelde_wijziging=voorgestelde_wijziging,
            verwachte_verbetering=verwachte_verbetering,
            requires_human_review=(bump_type == "major"),
            aangemaakt_op=_nu_iso(),
            status="draft",
        )

        self._sla_voorstel_op(proposal)

        logger.info(
            "Voorstel gegenereerd: agent=%s bump=%s versie=%s → %s "
            "requires_review=%s verwacht=%.0f%%",
            profiel.agent_name, bump_type, profiel.prompt_version,
            voorgestelde_versie, proposal.requires_human_review,
            verwachte_verbetering * 100,
        )
        return proposal

    # ─── Interne methoden ─────────────────────────────────────────

    async def _genereer_via_ollama(
        self,
        profiel: AgentPerformanceProfile,
        huidige_system_prompt: str,
        tips: list[str],
        probleembeschrijving: str,
    ) -> str:
        """
        Vraag Ollama om een verbeterd systeem-prompt te genereren.

        Geeft de rule-based fallback terug als Ollama niet beschikbaar is of
        een fout gooit.

        Args:
            profiel:              Het AgentPerformanceProfile.
            huidige_system_prompt: De huidige prompt tekst.
            tips:                 Verbetertips.
            probleembeschrijving: Samenvatting van het probleem.

        Returns:
            Verbeterde prompt als string.
        """
        client: Any = self._client
        if client is None and _HAS_OLLAMA and get_ollama_client is not None:
            client = get_ollama_client()

        if client is None:
            logger.debug(
                "Geen Ollama client beschikbaar voor agent=%s — rule-based fallback",
                profiel.agent_name,
            )
            return self._rule_based_improvement(huidige_system_prompt, tips)

        try:
            beschikbaar: bool = await client.is_available()
            if not beschikbaar:
                logger.info(
                    "Ollama niet bereikbaar voor agent=%s — rule-based fallback",
                    profiel.agent_name,
                )
                return self._rule_based_improvement(huidige_system_prompt, tips)

            tips_tekst = (
                "\n".join(f"- {tip}" for tip in tips)
                if tips
                else "- Geen specifieke tips beschikbaar"
            )
            sectie_overzicht = "\n".join(
                f"  {sectie}: {score:.2f}/5"
                for sectie, score in sorted(
                    profiel.gemiddelde_per_sectie.items(), key=lambda x: x[1]
                )
            ) or "  (geen sectiedata)"

            prompt = (
                "Je bent een expert in het schrijven van system prompts voor AI-agents "
                "die zakelijke analyses uitvoeren voor Belgische bedrijven.\n\n"
                f"PROBLEEM:\n{probleembeschrijving}\n\n"
                f"SCORES PER SECTIE:\n{sectie_overzicht}\n\n"
                f"VERBETER-TIPS:\n{tips_tekst}\n\n"
                f"HUIDIGE SYSTEM PROMPT:\n```\n{huidige_system_prompt}\n```\n\n"
                "Schrijf een verbeterde versie van de system prompt die de genoemde "
                "problemen oplost. Pas de structuur aan, voeg concrete voorbeelden toe "
                "en maak instructies actiegerichter. "
                "Geef ALLEEN de verbeterde system prompt terug, zonder uitleg of commentaar."
            )

            verbeterde_prompt: str = await client.generate(
                prompt=prompt,
                model=self._MODEL,
                temperature=self._TEMPERATURE,
                max_tokens=self._MAX_TOKENS,
            )
            logger.info(
                "Ollama genereerde verbeteringsvoorstel voor agent=%s (%d tekens)",
                profiel.agent_name, len(verbeterde_prompt),
            )
            return verbeterde_prompt.strip()

        except Exception as exc:
            logger.warning(
                "Ollama aanroep mislukt voor agent=%s: %s — rule-based fallback",
                profiel.agent_name, exc,
            )
            return self._rule_based_improvement(huidige_system_prompt, tips)

    def _rule_based_improvement(self, huidige_prompt: str, tips: list[str]) -> str:
        """
        Voeg verbetertips als instructies toe aan het einde van de huidige prompt.

        Args:
            huidige_prompt: De huidige system prompt tekst.
            tips:           Lijst van verbetertips die als instructies worden toegevoegd.

        Returns:
            Uitgebreide prompt met tips als opsomming achteraan.
        """
        if not tips:
            return huidige_prompt

        instructies = "\n\n## Verbeter-instructies (automatisch gegenereerd)\n"
        instructies += "Houd bij het geven van antwoorden rekening met de volgende richtlijnen:\n"
        for tip in tips:
            instructies += f"- {tip}\n"

        return huidige_prompt + instructies

    def _sla_voorstel_op(self, proposal: ImprovementProposal) -> None:
        """
        Sla het voorstel op als JSON-bestand in ``logs/feedback/proposals/``.

        Args:
            proposal: Het op te slaan :class:`ImprovementProposal`.
        """
        try:
            _PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
            voorstel_pad = _PROPOSALS_DIR / f"{proposal.proposal_id}.json"
            voorstel_pad.write_text(
                json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.debug("Voorstel opgeslagen: %s", voorstel_pad.name)
        except OSError as exc:
            logger.error("Voorstel opslaan mislukt: %s", exc)


# ─────────────────────────────────────────────
# SelfImprovementLoop
# ─────────────────────────────────────────────

class SelfImprovementLoop:
    """
    Orchestrator van de autonome zelf-verbeterings-cyclus voor VorstersNV agents.

    Voert een 6-staps cyclus uit:

    1. **Feedback collectie** — ophalen van alle FeedbackRecords.
    2. **Feedback analyse** — AgentPerformanceProfile per agent berekenen.
    3. **Prompt improvement proposals** — voorstellen genereren voor zwakke agents.
    4. **Shadow testing indicatie** — DRAFT-versies promoten naar SHADOW.
    5. **Auto-promotie gate** — SHADOW-versies met genoeg runs/score naar CANARY.
    6. **Knowledge update** — beslissingen loggen in DecisionJournal.

    Args:
        store:            FeedbackStore met alle feedback-records.
        analyzer:         FeedbackAnalyzer voor het analyseren van patronen.
        proposer:         PromptImprovementProposer voor het genereren van voorstellen.
        version_registry: Optionele AgentVersionRegistry voor promotie-acties.
    """

    def __init__(
        self,
        store: FeedbackStore,
        analyzer: FeedbackAnalyzer,
        proposer: PromptImprovementProposer,
        version_registry: AgentVersionRegistry | None = None,  # type: ignore[valid-type]
    ) -> None:
        self._store = store
        self._analyzer = analyzer
        self._proposer = proposer
        self._version_registry: Any = version_registry
        self._laatste_cyclus: dict[str, Any] | None = None

    # ─── Hoofdcyclus ──────────────────────────────────────────────

    async def run_cyclus(self, trace_id: str | None = None) -> dict[str, Any]:
        """
        Voer de volledige self-improvement cyclus sequentieel uit.

        Args:
            trace_id: Optioneel externe trace-ID voor audit-koppeling.

        Returns:
            Dict met cyclus-samenvatting: cyclus_id, timestamp, agents_geanalyseerd,
            zwakke_agents, voorstellen, promoties en duur_seconden.
        """
        cyclus_id = str(uuid.uuid4())
        start = time.perf_counter()
        eigen_trace_id = trace_id or str(uuid.uuid4())

        logger.info(
            "Self-improvement cyclus gestart: cyclus_id=%s trace_id=%s",
            cyclus_id, eigen_trace_id,
        )

        # ── Stap 1: FEEDBACK COLLECTIE ────────────────────────────
        alle_records = self._store.get_alle_records()
        logger.info("Cyclus gestart: %d feedback records gevonden", len(alle_records))

        # ── Stap 2: FEEDBACK ANALYSE ──────────────────────────────
        unieke_agents = sorted({r.agent_name for r in alle_records})
        for agent_name in unieke_agents:
            self._analyzer.analyseer_agent(agent_name)

        zwakke_profielen = self._analyzer.detecteer_zwakke_agents()
        zwakke_namen = [p.agent_name for p in zwakke_profielen]
        logger.info("Zwakke agents: %s", zwakke_namen if zwakke_namen else "geen")

        # ── Stap 3: PROMPT IMPROVEMENT PROPOSALS ──────────────────
        voorstellen: list[ImprovementProposal] = []
        for profiel in zwakke_profielen:
            tips = self._analyzer.genereer_verbetertips(profiel)
            huidige_prompt = self._laad_system_prompt(profiel.agent_name)
            try:
                voorstel = await self._proposer.genereer_voorstel(
                    profiel=profiel,
                    huidige_system_prompt=huidige_prompt,
                    tips=tips,
                )
                voorstellen.append(voorstel)
                logger.info(
                    "Voorstel gegenereerd voor %s: bump %s",
                    profiel.agent_name, voorstel.bump_type,
                )
            except Exception as exc:
                logger.error(
                    "Voorstel genereren mislukt voor agent=%s: %s",
                    profiel.agent_name, exc,
                )

        # ── Stap 4: SHADOW TESTING INDICATIE ──────────────────────
        shadow_acties: list[dict[str, str]] = []
        if self._version_registry is not None:
            for voorstel in voorstellen:
                agent_name = voorstel.agent_name
                actieve_versie = self._version_registry.get_active_version(agent_name)
                if actieve_versie is not None:
                    gepromoveerd: bool = self._version_registry.promote(
                        agent_name, actieve_versie.version
                    )
                    if gepromoveerd:
                        shadow_acties.append({
                            "agent":  agent_name,
                            "versie": actieve_versie.version,
                            "actie":  "shadow_testing",
                        })
                        voorstel.status = "shadow_testing"
                        logger.info(
                            "Shadow testing aangevraagd voor %s v%s",
                            agent_name, actieve_versie.version,
                        )

        # ── Stap 5: AUTO-PROMOTIE GATE ────────────────────────────
        promoties: list[dict[str, str]] = []
        if self._version_registry is not None:
            for agent_name in unieke_agents:
                shadow_versie = self._version_registry.get_shadow_version(agent_name)
                if shadow_versie is None:
                    continue
                voldoet = (
                    shadow_versie.run_count >= _CANARY_MIN_RUNS
                    and shadow_versie.eval_score is not None
                    and shadow_versie.eval_score > _CANARY_MIN_SCORE
                )
                if voldoet:
                    gepromoveerd = self._version_registry.promote(
                        agent_name, shadow_versie.version
                    )
                    if gepromoveerd:
                        promoties.append({
                            "agent":  agent_name,
                            "versie": shadow_versie.version,
                            "naar":   "canary",
                        })
                        logger.info(
                            "CANARY promotie: %s v%s (runs=%d score=%.3f)",
                            agent_name, shadow_versie.version,
                            shadow_versie.run_count, shadow_versie.eval_score,
                        )

        # ── Stap 6: KNOWLEDGE UPDATE ──────────────────────────────
        self._log_naar_journal(
            cyclus_id=cyclus_id,
            trace_id=eigen_trace_id,
            agents_geanalyseerd=len(unieke_agents),
            zwakke_namen=zwakke_namen,
            voorstellen=voorstellen,
            promoties=promoties,
        )

        duur = time.perf_counter() - start
        resultaat: dict[str, Any] = {
            "cyclus_id":           cyclus_id,
            "timestamp":           _nu_iso(),
            "agents_geanalyseerd": len(unieke_agents),
            "zwakke_agents":       zwakke_namen,
            "voorstellen":         [v.to_dict() for v in voorstellen],
            "promoties":           promoties,
            "duur_seconden":       round(duur, 3),
        }
        self._laatste_cyclus = resultaat

        logger.info(
            "Self-improvement cyclus voltooid: cyclus_id=%s duur=%.2fs "
            "agents=%d zwak=%d voorstellen=%d promoties=%d",
            cyclus_id, duur, len(unieke_agents), len(zwakke_namen),
            len(voorstellen), len(promoties),
        )
        return resultaat

    # ─── Status ───────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """
        Geef de huidige staat van de loop terug.

        Returns:
            Dict met ``laatste_cyclus``, ``totaal_records``,
            ``unieke_agents`` en ``zwakke_agents``.
        """
        alle_records = self._store.get_alle_records()
        zwakke_profielen = self._analyzer.detecteer_zwakke_agents()
        return {
            "laatste_cyclus": self._laatste_cyclus,
            "totaal_records":  len(alle_records),
            "unieke_agents":   len({r.agent_name for r in alle_records}),
            "zwakke_agents":   [p.agent_name for p in zwakke_profielen],
        }

    # ─── Private helpers ──────────────────────────────────────────

    def _laad_system_prompt(self, agent_name: str) -> str:
        """
        Laad de meest recente system prompt voor een agent.

        Zoekt in ``prompts/preprompt/`` naar ``.txt``-bestanden die overeenkomen
        met de agent-naam (gesorteerd reverse = meest recente versie eerst).

        Args:
            agent_name: Naam van de agent.

        Returns:
            De geladen prompttekst, of een lege string als niets gevonden is.
        """
        preprompt_dir = _PROJECT_ROOT / "prompts" / "preprompt"
        if not preprompt_dir.exists():
            return ""

        # Meest recente versie-bestand op basis van bestandsnaam
        kandidaten = sorted(preprompt_dir.glob(f"{agent_name}*.txt"), reverse=True)
        if kandidaten:
            try:
                inhoud = kandidaten[0].read_text(encoding="utf-8")
                logger.debug(
                    "System prompt geladen voor %s: %s (%d tekens)",
                    agent_name, kandidaten[0].name, len(inhoud),
                )
                return inhoud
            except OSError as exc:
                logger.warning(
                    "System prompt laden mislukt voor %s: %s", agent_name, exc
                )

        # Fallback: controleer iterations YAML-bestand
        iteraties_bestand = preprompt_dir / f"{agent_name}_iterations.yml"
        if iteraties_bestand.exists():
            logger.debug(
                "Iterations bestand gevonden voor %s — geen directe prompt beschikbaar",
                agent_name,
            )
            return (
                f"# Agent: {agent_name}\n"
                f"# System prompt wordt beheerd via PromptIterator "
                f"({iteraties_bestand.name})"
            )

        logger.debug("Geen system prompt gevonden voor agent=%s", agent_name)
        return ""

    def _log_naar_journal(
        self,
        cyclus_id: str,
        trace_id: str,
        agents_geanalyseerd: int,
        zwakke_namen: list[str],
        voorstellen: list[ImprovementProposal],
        promoties: list[dict[str, str]],
    ) -> None:
        """
        Log de cyclus-beslissingen in het DecisionJournal.

        Slaat af als ``_HAS_JOURNAL`` False is of als het aanmaken van de
        JournalEntry mislukt.

        Args:
            cyclus_id:           UUID van de huidige cyclus.
            trace_id:            Trace-ID voor audit-koppeling.
            agents_geanalyseerd: Aantal geanalyseerde agents.
            zwakke_namen:        Namen van zwakke agents.
            voorstellen:         Gegenereerde ImprovementProposal objecten.
            promoties:           Uitgevoerde promotie-acties.
        """
        if not _HAS_JOURNAL or get_decision_journal is None or JournalEntry is None:
            return

        try:
            journal = get_decision_journal()
            verdict = "APPROVED" if voorstellen else "REVIEW"
            reden = (
                f"Cyclus {cyclus_id}: {agents_geanalyseerd} agents geanalyseerd, "
                f"{len(zwakke_namen)} zwak, {len(voorstellen)} voorstellen, "
                f"{len(promoties)} promoties."
            )
            entry = JournalEntry(
                capability="self-improvement",
                agent_name="self_improvement_loop",
                model_used=PromptImprovementProposer._MODEL,
                verdict=verdict,
                trace_id=trace_id,
                selection_reason=reden,
                alternatives_considered=zwakke_namen,
                tools_used=["FeedbackAnalyzer", "PromptImprovementProposer"],
            )
            journal.record(entry)
            logger.debug(
                "Cyclus gelogd in DecisionJournal: trace_id=%s verdict=%s",
                trace_id, verdict,
            )
        except Exception as exc:
            logger.warning("DecisionJournal logging mislukt: %s", exc)


# ─────────────────────────────────────────────
# Singleton getters
# ─────────────────────────────────────────────

_feedback_store: FeedbackStore | None = None
_feedback_analyzer: FeedbackAnalyzer | None = None
_improvement_loop: SelfImprovementLoop | None = None


def get_feedback_store() -> FeedbackStore:
    """
    Geef de singleton :class:`FeedbackStore` terug.

    Bij de eerste aanroep wordt de store aangemaakt en worden bestaande
    records geladen vanuit ``logs/feedback/feedback_store.json``.

    Returns:
        Gedeelde FeedbackStore instantie.
    """
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store


def get_feedback_analyzer() -> FeedbackAnalyzer:
    """
    Geef de singleton :class:`FeedbackAnalyzer` terug.

    Maakt gebruik van de gedeelde FeedbackStore singleton.

    Returns:
        Gedeelde FeedbackAnalyzer instantie.
    """
    global _feedback_analyzer
    if _feedback_analyzer is None:
        _feedback_analyzer = FeedbackAnalyzer(store=get_feedback_store())
    return _feedback_analyzer


def get_self_improvement_loop() -> SelfImprovementLoop:
    """
    Geef de singleton :class:`SelfImprovementLoop` terug.

    Bouwt de volledige stack op: FeedbackStore → FeedbackAnalyzer →
    PromptImprovementProposer → AgentVersionRegistry (optioneel) →
    SelfImprovementLoop.

    Returns:
        Geconfigureerde SelfImprovementLoop instantie.
    """
    global _improvement_loop
    if _improvement_loop is None:
        store = get_feedback_store()
        analyzer = get_feedback_analyzer()
        proposer = PromptImprovementProposer()

        version_registry: Any = None
        if _HAS_VERSIONING and get_agent_version_registry is not None:
            try:
                version_registry = get_agent_version_registry()
                logger.debug("AgentVersionRegistry gekoppeld aan SelfImprovementLoop")
            except Exception as exc:
                logger.warning(
                    "AgentVersionRegistry niet beschikbaar voor SelfImprovementLoop: %s",
                    exc,
                )

        _improvement_loop = SelfImprovementLoop(
            store=store,
            analyzer=analyzer,
            proposer=proposer,
            version_registry=version_registry,
        )
    return _improvement_loop
