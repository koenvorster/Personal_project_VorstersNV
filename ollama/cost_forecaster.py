"""
VorstersNV CostForecaster — W6-06
Berekent de geschatte analyse-duur en -kosten voor een klantproject vóórdat de analyse start.
Werkt samen met AdaptiveChunker om het aantal chunks te bepalen en geeft een aanbevolen model.

Gebruik:
    forecaster = get_cost_forecaster()
    config     = ChunkConfig(model="mistral", max_tokens_per_chunk=2048)
    schatting  = forecaster.bereken_schatting("proj-123", bestanden, "mistral", config)
    print(forecaster.formatteer_rapport(schatting))
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ollama.adaptive_chunker import AdaptiveChunker, ChunkConfig, get_chunker

logger = logging.getLogger(__name__)

# ─── Verwerkingstijd per chunk per model (seconden, CPU-only laptop) ──

CHUNK_VERWERKINGSTIJD: dict[str, int] = {
    "mistral":   290,   # ~5 min per chunk op CPU
    "llama3.2":  120,   # sneller, kleiner model
    "llama3":    290,
    "llama3.1":  450,   # trager, groter context
    "codellama": 350,
}

# Fallback verwerkingstijd als model onbekend is
_DEFAULT_VERWERKINGSTIJD = 290

# ─── Drempelwaarden voor aanbevelingen ───────────────────────────

_DREMPEL_KLEINE_PROJECT    = 50    # < 50 chunks  → llama3.2
_DREMPEL_MIDDEL_PROJECT    = 200   # 50-200 chunks → mistral
# > 200 chunks → llama3.1

_DREMPEL_VEEL_CHUNKS       = 100   # waarschuwing: overweeg groot context model
_DREMPEL_BESTANDSGROOTTE   = 500 * 1024 * 1024  # 500 MB in bytes
_DREMPEL_VEEL_TALEN        = 10    # waarschuwing: te veel talen

# ─── Dataclass ───────────────────────────────────────────────────


@dataclass
class AnalyseSchatting:
    """Volledige schatting van de analyse-duur en -kosten voor een project."""

    project_id: str
    bestandsaantal: int
    totaal_chunks: int
    geschatte_tokens: int
    geschatte_duur_minuten: float
    geschatte_kosten_eur: float      # altijd 0.0 voor lokale Ollama
    model: str
    aanbevolen_model: str            # goedkoopste model dat de taak aankan
    waarschuwingen: list[str] = field(default_factory=list)


# ─── CostForecaster ──────────────────────────────────────────────


class CostForecaster:
    """
    Schat de verwerkingstijd en -kosten van een codebase-analyse.

    Kosten zijn altijd €0,00 omdat VorstersNV uitsluitend lokale Ollama-modellen
    gebruikt. De schatting focust op verwerkingstijd (CPU-only laptop).
    """

    def __init__(self, chunker: Optional[AdaptiveChunker] = None) -> None:
        self._chunker: AdaptiveChunker = chunker or get_chunker()

    # ── Interne hulpmethoden ──────────────────────────────────────

    def _aanbevolen_model(self, totaal_chunks: int) -> str:
        """
        Selecteer het goedkoopste model dat het project aankan.

        Args:
            totaal_chunks: totaal aantal gegenereerde chunks

        Returns:
            Model naam als string
        """
        if totaal_chunks < _DREMPEL_KLEINE_PROJECT:
            return "llama3.2"
        if totaal_chunks <= _DREMPEL_MIDDEL_PROJECT:
            return "mistral"
        return "llama3.1"

    def _bereken_waarschuwingen(
        self,
        totaal_chunks: int,
        bestanden: list[Path],
        talen: dict[str, int],
    ) -> list[str]:
        """
        Genereer waarschuwingen op basis van project-karakteristieken.

        Args:
            totaal_chunks: totaal aantal chunks
            bestanden:     lijst van bestandspaden
            talen:         dict {taal: aantal chunks}

        Returns:
            Lijst van waarschuwingsteksten (kan leeg zijn)
        """
        waarschuwingen: list[str] = []

        # Waarschuwing 1: te veel chunks
        if totaal_chunks > _DREMPEL_VEEL_CHUNKS:
            waarschuwingen.append(
                f"Meer dan {_DREMPEL_VEEL_CHUNKS} chunks: overweeg llama3.1 (32k context) "
                f"voor betere cohesie tussen chunks."
            )

        # Waarschuwing 2: grote bestanden
        totaal_bytes = sum(
            b.stat().st_size for b in bestanden if b.exists() and b.is_file()
        )
        if totaal_bytes > _DREMPEL_BESTANDSGROOTTE:
            totaal_mb = totaal_bytes / (1024 * 1024)
            waarschuwingen.append(
                f"Totale projectgrootte ({totaal_mb:.0f} MB) overschrijdt 500 MB: "
                f"analyse kan zeer lang duren op CPU."
            )

        # Waarschuwing 3: te veel programmeertalen
        if len(talen) > _DREMPEL_VEEL_TALEN:
            taal_lijst = ", ".join(sorted(talen.keys()))
            waarschuwingen.append(
                f"Meer dan {_DREMPEL_VEEL_TALEN} programmeertalen gevonden ({taal_lijst}): "
                f"overweeg de analyse per taal te splitsen."
            )

        return waarschuwingen

    def _verwerkingstijd_seconden(self, model: str, totaal_chunks: int) -> float:
        """
        Bereken de totale verwerkingstijd in seconden.

        Args:
            model:         gekozen model
            totaal_chunks: totaal aantal chunks

        Returns:
            Verwerkingstijd in seconden
        """
        tijd_per_chunk = CHUNK_VERWERKINGSTIJD.get(model, _DEFAULT_VERWERKINGSTIJD)
        return float(tijd_per_chunk * totaal_chunks)

    # ── Publieke API ──────────────────────────────────────────────

    def bereken_schatting(
        self,
        project_id: str,
        bestanden: list[Path],
        model: str,
        config: ChunkConfig,
    ) -> AnalyseSchatting:
        """
        Bereken de volledige analyse-schatting voor een project.

        Stappen:
        1. Chunk alle bestanden via AdaptiveChunker
        2. Bereken verwerkingstijd o.b.v. model en chunk-aantal
        3. Voeg waarschuwingen toe indien van toepassing
        4. Bepaal het aanbevolen model

        Args:
            project_id: unieke project-identifier
            bestanden:  lijst van bestandspaden
            model:      het gekozen Ollama-model
            config:     chunkconfiguratie

        Returns:
            AnalyseSchatting met alle schattingen en aanbevelingen
        """
        logger.info(
            "Bereken schatting voor project '%s': %d bestanden, model=%s",
            project_id, len(bestanden), model,
        )

        # Genereer alle chunks
        chunks = self._chunker.chunk_project(bestanden, config)
        statistieken = self._chunker.get_statistieken(chunks)

        totaal_chunks   = statistieken["totaal_chunks"]
        geschatte_tokens = statistieken.get("totaal_tokens", 0)
        talen: dict[str, int] = statistieken.get("per_taal", {})

        # Verwerkingstijd
        seconden = self._verwerkingstijd_seconden(model, totaal_chunks)
        duur_minuten = round(seconden / 60, 1)

        # Aanbevolen model & waarschuwingen
        aanbevolen = self._aanbevolen_model(totaal_chunks)
        waarschuwingen = self._bereken_waarschuwingen(totaal_chunks, bestanden, talen)

        schatting = AnalyseSchatting(
            project_id=project_id,
            bestandsaantal=len(bestanden),
            totaal_chunks=totaal_chunks,
            geschatte_tokens=geschatte_tokens,
            geschatte_duur_minuten=duur_minuten,
            geschatte_kosten_eur=0.0,    # lokale Ollama: altijd gratis
            model=model,
            aanbevolen_model=aanbevolen,
            waarschuwingen=waarschuwingen,
        )

        logger.info(
            "Schatting klaar voor '%s': %d chunks, ~%.1f min, aanbevolen model=%s, "
            "%d waarschuwingen",
            project_id, totaal_chunks, duur_minuten, aanbevolen, len(waarschuwingen),
        )

        return schatting

    def formatteer_rapport(self, schatting: AnalyseSchatting) -> str:
        """
        Geef een leesbaar tekst-rapport van de schatting, geschikt voor klantcommunicatie.

        Args:
            schatting: een AnalyseSchatting object

        Returns:
            Opgemaakte tekst (multi-line string)
        """
        uren   = int(schatting.geschatte_duur_minuten) // 60
        minuten = int(schatting.geschatte_duur_minuten) % 60
        duur_str = (
            f"{uren}u {minuten}min" if uren > 0 else f"{minuten} minuten"
        )

        aanbeveling_toelichting = ""
        if schatting.aanbevolen_model != schatting.model:
            aanbeveling_toelichting = (
                f"\n  ⚡ Aanbevolen model voor dit project: {schatting.aanbevolen_model} "
                f"(sneller/meer context dan {schatting.model})"
            )

        waarschuwingen_str = ""
        if schatting.waarschuwingen:
            regels = "\n".join(f"  ⚠️  {w}" for w in schatting.waarschuwingen)
            waarschuwingen_str = f"\nWaarschuwingen:\n{regels}"

        rapport = (
            f"╔══════════════════════════════════════════════════════╗\n"
            f"  Analyse Schatting — Project: {schatting.project_id}\n"
            f"╚══════════════════════════════════════════════════════╝\n"
            f"\n"
            f"  📁 Bestanden       : {schatting.bestandsaantal}\n"
            f"  🧩 Chunks          : {schatting.totaal_chunks}\n"
            f"  🔢 Geschatte tokens: {schatting.geschatte_tokens:,}\n"
            f"  ⏱  Geschatte duur  : ≈{duur_str} (CPU-only)\n"
            f"  💰 Kosten          : €{schatting.geschatte_kosten_eur:.2f} (lokale Ollama)\n"
            f"  🤖 Gekozen model   : {schatting.model}{aanbeveling_toelichting}"
            f"{waarschuwingen_str}\n"
        )
        return rapport


# ─── Singleton ───────────────────────────────────────────────────

_forecaster: Optional[CostForecaster] = None


def get_cost_forecaster() -> CostForecaster:
    """Singleton accessor voor CostForecaster."""
    global _forecaster
    if _forecaster is None:
        _forecaster = CostForecaster()
    return _forecaster
