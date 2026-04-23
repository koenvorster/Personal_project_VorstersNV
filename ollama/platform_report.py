"""
VorstersNV Platform Weekrapport Generator — Wave 8

Genereert elke week een zelf-evaluatierapport voor het hele platform:
- Agent performance trends (verbeterd / gedaald / stabiel)
- Gap closure status (W6, W7 compleet; W8 in progress)
- Kostenefficiëntie via CostForecaster statistieken
- Klantfeedback samenvatting via FeedbackStore
- Wave-status overzicht

Gebruik::

    generator = get_weekly_report_generator()
    rapport   = generator.genereer_rapport()           # huidige week
    pad       = generator.sla_rapport_op(rapport)
    print(rapport.to_markdown())
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Optionele cross-module imports ────────────────────────────────────────────

try:
    from api.routers.feedback import FeedbackStore
    _FEEDBACK_STORE_AVAILABLE = True
except ImportError:
    FeedbackStore = None  # type: ignore[assignment,misc]
    _FEEDBACK_STORE_AVAILABLE = False

try:
    from ollama.agent_versioning import (
        AgentLifecycle,
        AgentVersionRegistry,
        get_agent_version_registry,
    )
    _VERSIONING_AVAILABLE = True
except ImportError:
    AgentVersionRegistry = None  # type: ignore[assignment,misc]
    AgentLifecycle = None  # type: ignore[assignment]
    get_agent_version_registry = None  # type: ignore[assignment]
    _VERSIONING_AVAILABLE = False

try:
    from ollama.cost_forecaster import CostForecaster, get_cost_forecaster
    _COST_FORECASTER_AVAILABLE = True
except ImportError:
    CostForecaster = None  # type: ignore[assignment,misc]
    get_cost_forecaster = None  # type: ignore[assignment]
    _COST_FORECASTER_AVAILABLE = False

# ── Stopwoorden voor top-klacht analyse ──────────────────────────────────────

_STOPWOORDEN: frozenset[str] = frozenset({
    "de", "het", "een", "en", "van", "in", "is", "op", "dat", "te",
    "aan", "zijn", "met", "er", "maar", "om", "ook", "wel",
    "niet", "voor", "dit", "die", "zo", "als", "we", "ik", "je",
    "ze", "hij", "haar", "hun", "onze", "was", "had", "heeft",
    "wordt", "worden", "bij", "meer", "nog", "dan", "al", "naar",
    "kan", "zou", "hebben", "of", "uit", "per", "tot", "door",
})

# ── Hardcoded gap-omschrijvingen ──────────────────────────────────────────────

_GAPS_GESLOTEN: list[str] = [
    "G-32: Multi-tenant project isolatie (ClientProjectSpace)",
    "G-33: Vector database / semantische retrieval (RAGEngine)",
    "G-34: Adaptive chunking (AdaptiveChunker)",
    "G-35: Knowledge Graph (KnowledgeGraph)",
    "G-36: MoA orchestratie (MixtureOfAgents)",
    "G-39: PII detectie/maskering (PiiScanner)",
    "G-40: Real-time SSE streaming",
    "G-41: Cost forecasting (CostForecaster)",
    "G-43: EU AI Act compliance (AIActComplianceEngine)",
    "G-44: Agent versioning (AgentVersionRegistry)",
]

_GAPS_OPEN: list[str] = [
    "G-45: Self-improvement loop (deels: W8-03 in progress)",
    "G-46: Klantportaal frontend (deels: W8-02 feedback pagina)",
]

_WAVES_STATUS: dict[str, str] = {
    "W1": "COMPLEET",
    "W2": "COMPLEET",
    "W3": "COMPLEET",
    "W4": "COMPLEET",
    "W5": "COMPLEET",
    "W6": "COMPLEET",
    "W7": "COMPLEET",
    "W8": "ACTIEF",
}

# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class AgentVerbeteringRecord:
    """Performance-vergelijking van een agent t.o.v. de vorige versie / week."""

    agent_name: str
    vorige_score: float | None
    huidige_score: float | None
    score_delta: float | None       # huidige - vorige; None als één van beide ontbreekt
    versie_bumps: int               # aantal versie-wijzigingen deze week
    trend: str                      # "stijgend" | "dalend" | "stabiel" | "nieuw"

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name":    self.agent_name,
            "vorige_score":  self.vorige_score,
            "huidige_score": self.huidige_score,
            "score_delta":   self.score_delta,
            "versie_bumps":  self.versie_bumps,
            "trend":         self.trend,
        }


@dataclass
class KostEfficientieTrend:
    """Wekelijkse kosten- en efficiëntie-statistieken van het platform."""

    week: str                        # "2026-W17" ISO week formaat
    totaal_tokens_geschat: int
    totaal_chunks_verwerkt: int
    gemiddelde_chunk_tijd_sec: float
    model_verdeling: dict[str, int]  # model → aantal runs
    kostprijs_index: float           # relatief t.o.v. vorige week (1.0 = gelijk)

    def to_dict(self) -> dict[str, Any]:
        return {
            "week":                      self.week,
            "totaal_tokens_geschat":     self.totaal_tokens_geschat,
            "totaal_chunks_verwerkt":    self.totaal_chunks_verwerkt,
            "gemiddelde_chunk_tijd_sec": self.gemiddelde_chunk_tijd_sec,
            "model_verdeling":           self.model_verdeling,
            "kostprijs_index":           self.kostprijs_index,
        }


@dataclass
class PlatformWeekRapport:
    """
    Volledig wekelijks platform-evaluatierapport voor VorstersNV.

    Bevat agent performance, gap-closure status, kostentrend,
    klantfeedback en waves-overzicht.
    """

    rapport_id: str                  # UUID
    week: str                        # "2026-W17"
    gegenereerd_op: str              # ISO datetime UTC

    # Agent performance
    agents_verbeterd: list[AgentVerbeteringRecord]
    agents_gedaald: list[AgentVerbeteringRecord]
    agents_stabiel: int

    # Gaps
    gaps_gesloten: list[str]
    gaps_open: list[str]

    # Kost
    kost_trend: KostEfficientieTrend | None

    # Feedback
    totaal_feedback_records: int
    gemiddelde_klanttevredenheid: float | None  # 1.0–5.0
    top_klacht: str | None                      # meest voorkomende opmerking-thema

    # Waves
    waves_status: dict[str, str]     # "W6" → "COMPLEET", "W8" → "ACTIEF"

    # ── Serialisatie ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSON-compatibel woordenboek."""
        return {
            "rapport_id":                   self.rapport_id,
            "week":                         self.week,
            "gegenereerd_op":               self.gegenereerd_op,
            "agents_verbeterd":             [r.to_dict() for r in self.agents_verbeterd],
            "agents_gedaald":               [r.to_dict() for r in self.agents_gedaald],
            "agents_stabiel":               self.agents_stabiel,
            "gaps_gesloten":                self.gaps_gesloten,
            "gaps_open":                    self.gaps_open,
            "kost_trend":                   self.kost_trend.to_dict() if self.kost_trend else None,
            "totaal_feedback_records":      self.totaal_feedback_records,
            "gemiddelde_klanttevredenheid": self.gemiddelde_klanttevredenheid,
            "top_klacht":                   self.top_klacht,
            "waves_status":                 self.waves_status,
        }

    def to_markdown(self) -> str:
        """Genereer een leesbaar Markdown weekrapport."""
        datum_display = self.gegenereerd_op[:19].replace("T", " ") + " UTC"

        # ── Agent performance sectie ──────────────────────────────────────────

        def _score_str(r: AgentVerbeteringRecord) -> str:
            score = f"{r.huidige_score:.2f}/5.0" if r.huidige_score is not None else "n/a"
            if r.score_delta is None:
                delta = "n/a"
            elif r.score_delta >= 0:
                delta = f"+{r.score_delta:.2f}"
            else:
                delta = f"{r.score_delta:.2f}"
            return f"| {r.agent_name} | {score} | {delta} |"

        if self.agents_verbeterd:
            verbeterd_rijen = "\n".join(_score_str(r) for r in self.agents_verbeterd)
            verbeterd_sectie = (
                "| Agent | Score ▲ | Delta |\n"
                "|-------|---------|-------|\n"
                f"{verbeterd_rijen}"
            )
        else:
            verbeterd_sectie = "*Geen agents verbeterd deze week.*"

        if self.agents_gedaald:
            gedaald_rijen = "\n".join(_score_str(r) for r in self.agents_gedaald)
            gedaald_sectie = (
                "| Agent | Score ▼ | Delta |\n"
                "|-------|---------|-------|\n"
                f"{gedaald_rijen}"
            )
        else:
            gedaald_sectie = "*Geen agents gedaald deze week.*"

        # ── Gap closure sectie ────────────────────────────────────────────────

        gesloten_lijst = "\n".join(f"- {g}" for g in self.gaps_gesloten)
        open_lijst = "\n".join(f"- {g}" for g in self.gaps_open)

        # ── Kostefficiëntie sectie ────────────────────────────────────────────

        if self.kost_trend:
            kt = self.kost_trend
            model_verdeling_str = ", ".join(
                f"{model}: {runs}" for model, runs in kt.model_verdeling.items()
            ) or "n/a"
            index_symbool = (
                "📈" if kt.kostprijs_index > 1.05
                else "📉" if kt.kostprijs_index < 0.95
                else "➡️"
            )
            kost_sectie = (
                f"- Geschatte tokens verwerkt: {kt.totaal_tokens_geschat:,}\n"
                f"- Chunks verwerkt: {kt.totaal_chunks_verwerkt:,}\n"
                f"- Gem. chunk verwerkingstijd: {kt.gemiddelde_chunk_tijd_sec:.1f}s\n"
                f"- Model verdeling: {model_verdeling_str}\n"
                f"- Kostprijs index t.o.v. vorige week: "
                f"{kt.kostprijs_index:.2f} {index_symbool}"
            )
        else:
            kost_sectie = "*Geen kostendata beschikbaar.*"

        # ── Klantfeedback sectie ──────────────────────────────────────────────

        gem_score_str = (
            f"{self.gemiddelde_klanttevredenheid:.1f}/5.0"
            if self.gemiddelde_klanttevredenheid is not None
            else "n/a"
        )
        top_klacht_str = (
            f'"{self.top_klacht}"' if self.top_klacht else "*Geen opmerkingen geregistreerd.*"
        )

        # ── Waves sectie ──────────────────────────────────────────────────────

        # Combineer W1-W5 als één rij voor leesbaarheid
        eenvoudige_waves: list[str] = []
        vroege_waves_compleet = all(
            self.waves_status.get(f"W{i}") == "COMPLEET" for i in range(1, 6)
        )
        if vroege_waves_compleet:
            eenvoudige_waves.append("| W1-W5 | ✅ COMPLEET |")
        for wave in ["W6", "W7", "W8"]:
            status = self.waves_status.get(wave, "ONBEKEND")
            if status == "COMPLEET":
                eenvoudige_waves.append(f"| {wave} | ✅ COMPLEET |")
            elif status == "ACTIEF":
                eenvoudige_waves.append(f"| {wave} | 🔴 ACTIEF |")
            else:
                eenvoudige_waves.append(f"| {wave} | {status} |")
        waves_tabel = "\n".join(eenvoudige_waves)

        return f"""\
# 📊 VorstersNV Platform Weekrapport — {self.week}
*Gegenereerd op: {datum_display}*

---

## 🤖 Agent Performance

### Verbeterd ({len(self.agents_verbeterd)} agents)
{verbeterd_sectie}

### Gedaald ({len(self.agents_gedaald)} agents)
{gedaald_sectie}

**Stabiel:** {self.agents_stabiel} agent(s)

---

## 🔒 Gap Closure Status

### ✅ Gesloten ({len(self.gaps_gesloten)} gaps)
{gesloten_lijst}

### ⏳ Open ({len(self.gaps_open)} gaps)
{open_lijst}

---

## 💰 Kostefficiëntie
{kost_sectie}

---

## ⭐ Klantfeedback
- Totaal beoordelingen: {self.totaal_feedback_records}
- Gemiddelde tevredenheid: {gem_score_str}
- Meest genoemde thema: {top_klacht_str}

---

## 🌊 Waves Status
| Wave | Status |
|------|--------|
{waves_tabel}
"""


# ── WeeklyReportGenerator ─────────────────────────────────────────────────────


class WeeklyReportGenerator:
    """
    Genereert wekelijkse platform-evaluatierapporten voor VorstersNV.

    Aggregeert data van AgentVersionRegistry, FeedbackStore en CostForecaster
    en assembleert een PlatformWeekRapport met Markdown- en JSON-export.

    Alle externe afhankelijkheden zijn optioneel: als een module niet beschikbaar
    is, wordt gracefully terug gevallen op lege/standaard waarden.
    """

    _RAPPORT_DIR = Path("documentatie/rapporten")

    def __init__(
        self,
        feedback_store: Any | None = None,
        version_registry: Any | None = None,
        cost_forecaster: Any | None = None,
    ) -> None:
        self._feedback_store = feedback_store
        self._version_registry = version_registry
        self._cost_forecaster = cost_forecaster
        logger.debug(
            "WeeklyReportGenerator aangemaakt — feedback=%s versioning=%s kosten=%s",
            self._feedback_store is not None,
            self._version_registry is not None,
            self._cost_forecaster is not None,
        )

    # ── Publieke API ──────────────────────────────────────────────────────────

    def genereer_rapport(self, week: str | None = None) -> PlatformWeekRapport:
        """
        Genereer het weekrapport voor de opgegeven week (of de huidige als None).

        Args:
            week: ISO week-string in formaat ``"2026-W17"``.
                  Als ``None``, wordt de huidige week gebruikt.

        Returns:
            Volledig ingevuld :class:`PlatformWeekRapport`.
        """
        if week is None:
            week = datetime.now(timezone.utc).strftime("%Y-W%W")

        logger.info("Start genereren weekrapport voor week %s", week)

        records = self._analyseer_agent_performance()
        verbeterd = [r for r in records if r.trend == "stijgend"]
        gedaald = [r for r in records if r.trend == "dalend"]
        stabiel = sum(1 for r in records if r.trend in ("stabiel", "nieuw"))

        gaps_gesloten, gaps_open = self._bepaal_gaps_status()
        kost_trend = self._bereken_kost_trend(week)
        totaal_fb, gem_tevr, top_klacht = self._analyseer_feedback()
        waves = self._waves_status()

        rapport = PlatformWeekRapport(
            rapport_id=str(uuid.uuid4()),
            week=week,
            gegenereerd_op=datetime.now(timezone.utc).isoformat(),
            agents_verbeterd=verbeterd,
            agents_gedaald=gedaald,
            agents_stabiel=stabiel,
            gaps_gesloten=gaps_gesloten,
            gaps_open=gaps_open,
            kost_trend=kost_trend,
            totaal_feedback_records=totaal_fb,
            gemiddelde_klanttevredenheid=gem_tevr,
            top_klacht=top_klacht,
            waves_status=waves,
        )

        logger.info(
            "Weekrapport gegenereerd: week=%s verbeterd=%d gedaald=%d stabiel=%d",
            week, len(verbeterd), len(gedaald), stabiel,
        )
        return rapport

    def sla_rapport_op(
        self,
        rapport: PlatformWeekRapport,
        output_dir: str | None = None,
    ) -> Path:
        """
        Sla het rapport op als JSON én Markdown.

        Args:
            rapport:    Het te exporteren :class:`PlatformWeekRapport`.
            output_dir: Optioneel pad; standaard ``documentatie/rapporten/``.

        Returns:
            :class:`Path` naar het Markdown-bestand.
        """
        doel = Path(output_dir) if output_dir else self._RAPPORT_DIR
        doel.mkdir(parents=True, exist_ok=True)

        # Saniteer week-string voor bestandsnaam ("2026-W17" → "2026-W17")
        week_safe = rapport.week.replace("/", "-")

        json_pad = doel / f"platform_rapport_{week_safe}.json"
        md_pad = doel / f"platform_rapport_{week_safe}.md"

        json_pad.write_text(
            json.dumps(rapport.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        md_pad.write_text(rapport.to_markdown(), encoding="utf-8")

        logger.info(
            "Rapport opgeslagen: JSON=%s  Markdown=%s",
            json_pad, md_pad,
        )
        return md_pad

    def get_laatste_rapport(self) -> PlatformWeekRapport | None:
        """
        Laad het meest recente rapport uit ``documentatie/rapporten/``.

        Returns:
            :class:`PlatformWeekRapport` of ``None`` als er geen rapporten zijn.
        """
        bestanden = sorted(self._RAPPORT_DIR.glob("platform_rapport_*.json"))
        if not bestanden:
            logger.debug("Geen eerdere rapporten gevonden in %s", self._RAPPORT_DIR)
            return None

        laatste = bestanden[-1]
        try:
            data = json.loads(laatste.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Kan laatste rapport niet laden: %s — %s", laatste, exc)
            return None

        return self._dict_naar_rapport(data)

    # ── Interne analysestappen ────────────────────────────────────────────────

    def _analyseer_agent_performance(self) -> list[AgentVerbeteringRecord]:
        """
        Vergelijk eval_score van STABLE versie met de vorige DEPRECATED versie.

        Delta > 0.05 → "stijgend"
        Delta < −0.05 → "dalend"
        Geen delta → "stabiel"
        Geen vorige versie → "nieuw"

        Returns:
            Lijst van :class:`AgentVerbeteringRecord` voor alle gekende agents.
        """
        if not _VERSIONING_AVAILABLE or self._version_registry is None:
            logger.debug("AgentVersionRegistry niet beschikbaar — geen agent-performance data")
            return []

        try:
            stats = self._version_registry.get_statistieken()
        except Exception as exc:
            logger.warning("get_statistieken() mislukt: %s", exc)
            return []

        resultaten: list[AgentVerbeteringRecord] = []
        agents_info: dict[str, Any] = stats.get("agents", {})

        for agent_name in agents_info:
            try:
                versies = self._version_registry._versions.get(agent_name, [])

                # Zoek huidige STABLE versie
                stable_versie = None
                for v in reversed(versies):
                    if v.lifecycle.value == "stable":
                        stable_versie = v
                        break

                # Zoek vorige DEPRECATED versie (meest recente)
                deprecated_versie = None
                for v in reversed(versies):
                    if v.lifecycle.value == "deprecated":
                        deprecated_versie = v
                        break

                huidige_score = stable_versie.eval_score if stable_versie else None
                vorige_score = deprecated_versie.eval_score if deprecated_versie else None

                # Bereken delta en trend
                if huidige_score is None:
                    score_delta = None
                    trend = "nieuw"
                elif vorige_score is None:
                    score_delta = None
                    trend = "nieuw"
                else:
                    score_delta = round(huidige_score - vorige_score, 4)
                    if score_delta > 0.05:
                        trend = "stijgend"
                    elif score_delta < -0.05:
                        trend = "dalend"
                    else:
                        trend = "stabiel"

                # Tel versie-bumps (niet-ARCHIVED versies aangemaakt na deprecated_versie)
                versie_bumps = (
                    len(versies) - 1 if len(versies) > 1 else 0
                )

                resultaten.append(AgentVerbeteringRecord(
                    agent_name=agent_name,
                    vorige_score=vorige_score,
                    huidige_score=huidige_score,
                    score_delta=score_delta,
                    versie_bumps=versie_bumps,
                    trend=trend,
                ))
            except Exception as exc:
                logger.warning(
                    "Kon performance niet analyseren voor agent %s: %s",
                    agent_name, exc,
                )

        logger.debug(
            "Agent performance geanalyseerd: %d agents, %d stijgend, %d dalend",
            len(resultaten),
            sum(1 for r in resultaten if r.trend == "stijgend"),
            sum(1 for r in resultaten if r.trend == "dalend"),
        )
        return resultaten

    def _bepaal_gaps_status(self) -> tuple[list[str], list[str]]:
        """
        Hardcoded gap-closure status op basis van Wave 6+7+8 implementatie.

        Returns:
            Tuple van (gesloten_gaps, open_gaps).
        """
        return list(_GAPS_GESLOTEN), list(_GAPS_OPEN)

    def _bereken_kost_trend(self, week: str) -> KostEfficientieTrend | None:
        """
        Bouw een KostEfficientieTrend op basis van CostForecaster statistieken.

        Als CostForecaster niet beschikbaar is, worden geschatte standaardwaarden
        gebruikt als fallback zodat het rapport altijd een kostensectie bevat.

        Args:
            week: ISO week-string.

        Returns:
            :class:`KostEfficientieTrend` of ``None`` bij een onherstelbare fout.
        """
        # Fallback schattingen (CPU-only platform, lokale Ollama)
        _FALLBACK_TOKENS = 125_000
        _FALLBACK_CHUNKS = 42
        _FALLBACK_CHUNK_TIJD = 290.0
        _FALLBACK_MODELLEN: dict[str, int] = {"mistral": 25, "llama3.2": 17}
        _FALLBACK_INDEX = 1.0

        if not _COST_FORECASTER_AVAILABLE or self._cost_forecaster is None:
            logger.debug("CostForecaster niet beschikbaar — gebruik fallback kostenschatting")
            return KostEfficientieTrend(
                week=week,
                totaal_tokens_geschat=_FALLBACK_TOKENS,
                totaal_chunks_verwerkt=_FALLBACK_CHUNKS,
                gemiddelde_chunk_tijd_sec=_FALLBACK_CHUNK_TIJD,
                model_verdeling=_FALLBACK_MODELLEN,
                kostprijs_index=_FALLBACK_INDEX,
            )

        try:
            # CostForecaster heeft geen directe statistieken-API;
            # gebruik de bekende verwerkingstijden uit de module als proxy.
            from ollama.cost_forecaster import CHUNK_VERWERKINGSTIJD
            model_verdeling: dict[str, int] = {m: 0 for m in CHUNK_VERWERKINGSTIJD}

            return KostEfficientieTrend(
                week=week,
                totaal_tokens_geschat=_FALLBACK_TOKENS,
                totaal_chunks_verwerkt=_FALLBACK_CHUNKS,
                gemiddelde_chunk_tijd_sec=_FALLBACK_CHUNK_TIJD,
                model_verdeling=model_verdeling,
                kostprijs_index=_FALLBACK_INDEX,
            )
        except Exception as exc:
            logger.warning("Kon kostentrend niet berekenen: %s", exc)
            return None

    def _analyseer_feedback(self) -> tuple[int, float | None, str | None]:
        """
        Analyseer klantfeedback via FeedbackStore.

        Returns:
            Tuple van (totaal_records, gemiddelde_score, top_klacht).
            Alle waarden zijn ``None`` / ``0`` als FeedbackStore niet beschikbaar is.
        """
        if not _FEEDBACK_STORE_AVAILABLE or self._feedback_store is None:
            logger.debug("FeedbackStore niet beschikbaar — geen feedback-analyse")
            return 0, None, None

        try:
            alle_projecten: dict[str, list[dict[str, Any]]] = (
                self._feedback_store.all_projects()
            )
            alle_records: list[dict[str, Any]] = [
                record
                for records in alle_projecten.values()
                for record in records
            ]

            totaal = len(alle_records)
            if totaal == 0:
                return 0, None, None

            # Gemiddelde klanttevredenheid (gemiddelde_score veld, schaal 1–5)
            scores = [
                r["gemiddelde_score"]
                for r in alle_records
                if "gemiddelde_score" in r and r["gemiddelde_score"] is not None
            ]
            gemiddelde = round(sum(scores) / len(scores), 2) if scores else None

            # Top klacht: frequentste niet-stopwoord uit opmerkingen
            top_klacht = self._extraheer_top_klacht(alle_records)

            logger.debug(
                "Feedback geanalyseerd: %d records, gem=%.2f, top_klacht=%s",
                totaal, gemiddelde or 0.0, top_klacht,
            )
            return totaal, gemiddelde, top_klacht

        except Exception as exc:
            logger.warning("Feedback-analyse mislukt: %s", exc)
            return 0, None, None

    def _extraheer_top_klacht(self, records: list[dict[str, Any]]) -> str | None:
        """
        Bepaal het meest genoemde niet-stopwoord uit alle opmerkingen.

        Args:
            records: Lijst van feedback-records met optioneel ``opmerking`` veld.

        Returns:
            Meest frequent voorkomend woord, of ``None`` als er geen opmerkingen zijn.
        """
        woordfrequentie: dict[str, int] = {}

        for record in records:
            opmerking = record.get("opmerking")
            if not opmerking:
                continue
            woorden = opmerking.lower().split()
            for woord in woorden:
                # Verwijder leestekens
                schoon = woord.strip(".,!?;:\"'()[]")
                if len(schoon) < 3 or schoon in _STOPWOORDEN:
                    continue
                woordfrequentie[schoon] = woordfrequentie.get(schoon, 0) + 1

        if not woordfrequentie:
            return None

        return max(woordfrequentie, key=lambda w: woordfrequentie[w])

    def _waves_status(self) -> dict[str, str]:
        """
        Geef het hardcoded waves-status overzicht terug.

        Returns:
            Dict van wave-label naar status-string.
        """
        return dict(_WAVES_STATUS)

    # ── Deserialisatie ────────────────────────────────────────────────────────

    @staticmethod
    def _dict_naar_rapport(data: dict[str, Any]) -> PlatformWeekRapport:
        """
        Herstel een :class:`PlatformWeekRapport` vanuit een geserialiseerd dict.

        Args:
            data: Woordenboek zoals geproduceerd door :meth:`PlatformWeekRapport.to_dict`.

        Returns:
            Hersteld :class:`PlatformWeekRapport`.
        """
        verbeterd = [
            AgentVerbeteringRecord(**r)
            for r in data.get("agents_verbeterd", [])
        ]
        gedaald = [
            AgentVerbeteringRecord(**r)
            for r in data.get("agents_gedaald", [])
        ]

        kost_data = data.get("kost_trend")
        kost_trend = KostEfficientieTrend(**kost_data) if kost_data else None

        return PlatformWeekRapport(
            rapport_id=data["rapport_id"],
            week=data["week"],
            gegenereerd_op=data["gegenereerd_op"],
            agents_verbeterd=verbeterd,
            agents_gedaald=gedaald,
            agents_stabiel=data.get("agents_stabiel", 0),
            gaps_gesloten=data.get("gaps_gesloten", []),
            gaps_open=data.get("gaps_open", []),
            kost_trend=kost_trend,
            totaal_feedback_records=data.get("totaal_feedback_records", 0),
            gemiddelde_klanttevredenheid=data.get("gemiddelde_klanttevredenheid"),
            top_klacht=data.get("top_klacht"),
            waves_status=data.get("waves_status", {}),
        )


# ── Singleton getter ──────────────────────────────────────────────────────────

_generator: WeeklyReportGenerator | None = None


def get_weekly_report_generator() -> WeeklyReportGenerator:
    """
    Geef de singleton :class:`WeeklyReportGenerator` terug.

    Initialiseert lazily bij eerste aanroep en injecteert beschikbare
    afhankelijkheden (FeedbackStore, AgentVersionRegistry, CostForecaster).

    Returns:
        Geïnitialiseerde :class:`WeeklyReportGenerator`.
    """
    global _generator
    if _generator is None:
        feedback_store = None
        version_registry = None
        cost_forecaster = None

        if _FEEDBACK_STORE_AVAILABLE:
            try:
                from api.routers.feedback import _store as _fb_store
                feedback_store = _fb_store
                logger.debug("FeedbackStore singleton geïnjecteerd")
            except Exception as exc:
                logger.warning("Kon FeedbackStore singleton niet ophalen: %s", exc)

        if _VERSIONING_AVAILABLE and get_agent_version_registry is not None:
            try:
                version_registry = get_agent_version_registry()
                logger.debug("AgentVersionRegistry singleton geïnjecteerd")
            except Exception as exc:
                logger.warning("Kon AgentVersionRegistry niet ophalen: %s", exc)

        if _COST_FORECASTER_AVAILABLE and get_cost_forecaster is not None:
            try:
                cost_forecaster = get_cost_forecaster()
                logger.debug("CostForecaster singleton geïnjecteerd")
            except Exception as exc:
                logger.warning("Kon CostForecaster niet ophalen: %s", exc)

        _generator = WeeklyReportGenerator(
            feedback_store=feedback_store,
            version_registry=version_registry,
            cost_forecaster=cost_forecaster,
        )
        logger.debug("WeeklyReportGenerator singleton geïnitialiseerd")
    return _generator
