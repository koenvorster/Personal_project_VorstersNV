"""
VorstersNV AdaptiveChunker — W6-03
Verdeelt broncodebestanden in LLM-vriendelijke chunks die passen in het context window
van het gekozen model. De strategie past zich aan op basis van taaltype, bestandsgrootte
en het context window van het model.

Gebruik:
    chunker = get_chunker()
    config  = ChunkConfig(model="mistral", max_tokens_per_chunk=2048)
    chunks  = chunker.chunk_bestand(Path("src/Main.java"), config)
    stats   = chunker.get_statistieken(chunks)
"""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Model context windows ────────────────────────────────────────

MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "mistral":   8_192,
    "llama3":    8_192,
    "llama3.1":  32_768,
    "llama3.2":  131_072,
    "codellama": 16_384,
}

# ─── Taal detectie ───────────────────────────────────────────────

_EXTENSIE_TAAL: dict[str, str] = {
    ".java":  "java",
    ".py":    "python",
    ".php":   "php",
    ".cs":    "csharp",
    ".js":    "javascript",
    ".ts":    "typescript",
}

# Regex voor functie/methode grenzen per taal
_FUNCTIE_REGEX: dict[str, re.Pattern[str]] = {
    "python": re.compile(r"^(async\s+)?def\s+\w+", re.MULTILINE),
    "java":   re.compile(
        r"^\s*(public|private|protected|static|final|abstract|synchronized|native|strictfp)"
        r"(\s+(public|private|protected|static|final|abstract|synchronized|native|strictfp))*"
        r"\s+\w[\w<>\[\],\s]*\s+\w+\s*\(",
        re.MULTILINE,
    ),
}


# ─── Dataclasses ─────────────────────────────────────────────────

@dataclass
class ChunkConfig:
    """Configuratie voor de chunking strategie."""

    model: str = "mistral"
    max_tokens_per_chunk: int = 2_048
    overlap_tokens: int = 200
    preserve_functions: bool = True


@dataclass
class CodeChunk:
    """Één chunk van een broncode-bestand."""

    chunk_id: str
    bestand: str          # relatief of absoluut pad als string
    taal: str             # java | python | php | csharp | javascript | typescript | other
    inhoud: str           # de eigenlijke codetekst
    lijn_start: int
    lijn_eind: int
    token_schatting: int  # geschat aantal tokens (len // 4)
    volgnummer: int       # 1-based chunk nummer binnen dit bestand
    totaal_chunks: int    # totaal aantal chunks voor dit bestand


# ─── AdaptiveChunker ─────────────────────────────────────────────

class AdaptiveChunker:
    """
    Verdeelt broncodebestanden adaptief in LLM-vriendelijke chunks.

    - Bij kleine bestanden (< max_tokens): één chunk
    - Bij grote bestanden met preserve_functions=True voor Java/Python:
      splits op functie/methode grenzen
    - Overige gevallen: regel-gebaseerd splitsen met overlap
    """

    # ── Hulpmethoden ─────────────────────────────────────────────

    def detect_taal(self, bestand: Path) -> str:
        """
        Detecteer de programmeertaal op basis van bestandsextensie.

        Args:
            bestand: pad naar het bronbestand

        Returns:
            Taal-string: java | python | php | csharp | javascript | typescript | other
        """
        return _EXTENSIE_TAAL.get(bestand.suffix.lower(), "other")

    def schat_tokens(self, tekst: str) -> int:
        """
        Schat het aantal tokens zonder tiktoken.
        Vuistregel: 1 token ≈ 4 tekens.

        Args:
            tekst: willekeurige tekst

        Returns:
            Geschat aantal tokens (minimum 1)
        """
        return max(1, len(tekst) // 4)

    # ── Interne splitsmethoden ────────────────────────────────────

    def _splits_op_functies(
        self,
        regels: list[str],
        config: ChunkConfig,
        taal: str,
    ) -> list[list[str]]:
        """
        Splits regels op functie/methode grenzen voor Java en Python.
        Valt terug op regel-gebaseerd splitsen als geen grenzen gevonden.

        Args:
            regels: alle regels van het bestand
            config: chunkconfiguratie
            taal:   "java" of "python"

        Returns:
            Lijst van regelgroepen (elke groep wordt één chunk)
        """
        patroon = _FUNCTIE_REGEX.get(taal)
        if patroon is None:
            return self._splits_op_regels(regels, config)

        # Bepaal de startregelnummers van elke functie/methode
        grenzen: list[int] = []
        for idx, regel in enumerate(regels):
            if patroon.match(regel):
                grenzen.append(idx)

        if not grenzen:
            logger.debug("Geen functiegrenzen gevonden in %s-bestand; gebruik regel-splitsing", taal)
            return self._splits_op_regels(regels, config)

        # Voeg een schildwacht toe aan het einde
        grenzen.append(len(regels))

        groepen: list[list[str]] = []
        for i, start in enumerate(grenzen[:-1]):
            eind = grenzen[i + 1]
            blok = regels[start:eind]

            # Blok is te groot → sub-splits op regels
            if self.schat_tokens("\n".join(blok)) > config.max_tokens_per_chunk:
                groepen.extend(self._splits_op_regels(blok, config))
            else:
                groepen.append(blok)

        # Regels vóór de eerste functie (imports, package, etc.)
        if grenzen[0] > 0:
            prefix = regels[: grenzen[0]]
            groepen.insert(0, prefix)

        return groepen

    def _splits_op_regels(
        self,
        regels: list[str],
        config: ChunkConfig,
    ) -> list[list[str]]:
        """
        Splits regels in groepen tot max_tokens_per_chunk bereikt, met overlap.

        Args:
            regels: regels om te splitsen
            config: chunkconfiguratie

        Returns:
            Lijst van regelgroepen
        """
        groepen: list[list[str]] = []
        huidige: list[str] = []
        huidige_tokens = 0
        overlap_regels: list[str] = []

        for regel in regels:
            regel_tokens = self.schat_tokens(regel)

            if huidige_tokens + regel_tokens > config.max_tokens_per_chunk and huidige:
                groepen.append(list(huidige))
                # Bereken overlap: neem de laatste regels die samen ≤ overlap_tokens vormen
                overlap_regels = self._bereken_overlap(huidige, config.overlap_tokens)
                huidige = list(overlap_regels)
                huidige_tokens = self.schat_tokens("\n".join(huidige))

            huidige.append(regel)
            huidige_tokens += regel_tokens

        if huidige:
            groepen.append(huidige)

        return groepen

    def _bereken_overlap(self, regels: list[str], overlap_tokens: int) -> list[str]:
        """
        Selecteer de laatste N regels die samen ≤ overlap_tokens vormen.

        Args:
            regels:         oorspronkelijke regellijst
            overlap_tokens: maximaal aantal overlap-tokens

        Returns:
            Sublijst van de laatste regels als overlap
        """
        overlap: list[str] = []
        tokens = 0
        for regel in reversed(regels):
            t = self.schat_tokens(regel)
            if tokens + t > overlap_tokens:
                break
            overlap.insert(0, regel)
            tokens += t
        return overlap

    def _groepen_naar_chunks(
        self,
        groepen: list[list[str]],
        bestand: Path,
        taal: str,
        lijn_offset: int = 0,
    ) -> list[CodeChunk]:
        """
        Converteer regelgroepen naar CodeChunk objecten.

        Args:
            groepen:      lijst van regelgroepen
            bestand:      bronbestandspad
            taal:         gedetecteerde taal
            lijn_offset:  startregel offset (voor sub-splits)

        Returns:
            Lijst van CodeChunk objecten
        """
        totaal = len(groepen)
        chunks: list[CodeChunk] = []
        huidig_lijn = lijn_offset

        for volgnummer, groep in enumerate(groepen, start=1):
            inhoud = "\n".join(groep)
            lijn_start = huidig_lijn + 1          # 1-based
            lijn_eind = huidig_lijn + len(groep)
            huidig_lijn += len(groep)

            chunks.append(
                CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    bestand=str(bestand),
                    taal=taal,
                    inhoud=inhoud,
                    lijn_start=lijn_start,
                    lijn_eind=lijn_eind,
                    token_schatting=self.schat_tokens(inhoud),
                    volgnummer=volgnummer,
                    totaal_chunks=totaal,
                )
            )

        return chunks

    # ── Publieke API ──────────────────────────────────────────────

    def chunk_bestand(self, bestand: Path, config: ChunkConfig) -> list[CodeChunk]:
        """
        Chunk één bronbestand op basis van de gegeven configuratie.

        Strategie (in volgorde):
        1. Bestand past in één chunk → retourneer één CodeChunk
        2. preserve_functions=True én taal is java/python → splits op functiegrenzen
        3. Overig → splits op regels met overlap

        Args:
            bestand: pad naar het bronbestand
            config:  chunkconfiguratie

        Returns:
            Lijst van CodeChunk objecten (minimaal 1)
        """
        try:
            tekst = bestand.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Kan bestand niet lezen: %s — %s", bestand, exc)
            return []

        taal = self.detect_taal(bestand)
        tokens = self.schat_tokens(tekst)

        logger.debug(
            "chunk_bestand: %s | taal=%s | ~%d tokens | preserve_functions=%s",
            bestand.name, taal, tokens, config.preserve_functions,
        )

        # ── Geval 1: alles past in één chunk ─────────────────────
        if tokens <= config.max_tokens_per_chunk:
            regels = tekst.splitlines()
            return [
                CodeChunk(
                    chunk_id=str(uuid.uuid4()),
                    bestand=str(bestand),
                    taal=taal,
                    inhoud=tekst,
                    lijn_start=1,
                    lijn_eind=len(regels),
                    token_schatting=tokens,
                    volgnummer=1,
                    totaal_chunks=1,
                )
            ]

        regels = tekst.splitlines()

        # ── Geval 2: functie-preserving splitsing ─────────────────
        if config.preserve_functions and taal in ("java", "python"):
            groepen = self._splits_op_functies(regels, config, taal)
        else:
            # ── Geval 3: regel-gebaseerde splitsing ───────────────
            groepen = self._splits_op_regels(regels, config)

        chunks = self._groepen_naar_chunks(groepen, bestand, taal)
        logger.info(
            "Gechunkt: %s → %d chunks (taal=%s, ~%d tokens totaal)",
            bestand.name, len(chunks), taal, tokens,
        )
        return chunks

    def chunk_project(
        self,
        bestanden: list[Path],
        config: ChunkConfig,
    ) -> list[CodeChunk]:
        """
        Chunk alle bestanden van een project.

        Args:
            bestanden: lijst van bestandspaden
            config:    chunkconfiguratie

        Returns:
            Gecombineerde lijst van alle CodeChunk objecten
        """
        alle_chunks: list[CodeChunk] = []
        for bestand in bestanden:
            chunks = self.chunk_bestand(bestand, config)
            alle_chunks.extend(chunks)
        logger.info(
            "chunk_project: %d bestanden → %d chunks totaal",
            len(bestanden), len(alle_chunks),
        )
        return alle_chunks

    def get_statistieken(self, chunks: list[CodeChunk]) -> dict[str, Any]:
        """
        Bereken statistieken over een set chunks.

        Args:
            chunks: lijst van CodeChunk objecten

        Returns:
            dict met:
            - totaal_chunks (int)
            - gemiddeld_tokens (float)
            - max_tokens (int)
            - min_tokens (int)
            - totaal_tokens (int)
            - per_taal (dict[str, int]): aantal chunks per taal
            - unieke_bestanden (int)
        """
        if not chunks:
            return {
                "totaal_chunks": 0,
                "gemiddeld_tokens": 0.0,
                "max_tokens": 0,
                "min_tokens": 0,
                "totaal_tokens": 0,
                "per_taal": {},
                "unieke_bestanden": 0,
            }

        tokens_lijst = [c.token_schatting for c in chunks]
        per_taal: dict[str, int] = {}
        for chunk in chunks:
            per_taal[chunk.taal] = per_taal.get(chunk.taal, 0) + 1

        return {
            "totaal_chunks": len(chunks),
            "gemiddeld_tokens": round(sum(tokens_lijst) / len(tokens_lijst), 1),
            "max_tokens": max(tokens_lijst),
            "min_tokens": min(tokens_lijst),
            "totaal_tokens": sum(tokens_lijst),
            "per_taal": per_taal,
            "unieke_bestanden": len({c.bestand for c in chunks}),
        }


# ─── Singleton ───────────────────────────────────────────────────

_chunker: Optional[AdaptiveChunker] = None


def get_chunker() -> AdaptiveChunker:
    """Singleton accessor voor AdaptiveChunker."""
    global _chunker
    if _chunker is None:
        _chunker = AdaptiveChunker()
    return _chunker
