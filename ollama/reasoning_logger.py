"""
VorstersNV ReasoningLogger (Wave 9)
Extraheert, logt en analyseert chain-of-thought reasoning uit LLM-uitvoer.

Persistentie: logs/reasoning/{agent_name}/{session_id}.json
Geen externe dependencies — token-schatting via len(text) // 4.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOGS_DIR = Path(__file__).parent.parent / "logs" / "reasoning"

# ── Patronen voor reasoning-extractie (volgorde is belangrijk) ────────────────
_TAG_PATTERNS: list[tuple[str, str]] = [
    (r"<reasoning>(.*?)</reasoning>", "reasoning_tag"),
    (r"<thinking>(.*?)</thinking>",   "thinking_tag"),
]

_STAP_PATTERNS: list[tuple[str, str]] = [
    (r"(?:^|\n)(?:Stap\s+\d+[:.].*?)(?=\nStap\s+\d+|$)", "stap_nl"),
    (r"(?:^|\n)(?:Step\s+\d+[:.].*?)(?=\nStep\s+\d+|$)", "step_en"),
    (r"(?:^|\n)(\d+\.\s+.+?)(?=\n\d+\.|$)",              "numbered"),
]

# Stopwoorden voor keyword-analyse
_STOPWOORDEN = frozenset({
    "de", "het", "een", "en", "van", "in", "is", "dat", "op", "te",
    "voor", "met", "zijn", "aan", "er", "ook", "the", "a", "an", "of",
    "to", "in", "is", "it", "and", "or", "for", "on", "with", "that",
    "this", "we", "i", "at", "be", "as", "by", "but", "not", "from",
})


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class ReasoningExtractie:
    """Bevat alle geëxtraheerde gegevens van één reasoning-sessie."""

    session_id: str
    agent_name: str
    project_id: str | None
    reasoning_text: str                   # volledige geëxtraheerde reasoning
    chain_of_thought_stappen: list[str]   # individuele genummerde stappen
    input_tokens: int
    reasoning_tokens: int
    output_tokens: int
    model_name: str | None
    gecreeerd_op: str                     # ISO 8601

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar een JSON-serialiseerbaar woordenboek."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReasoningExtractie:
        """Herstel een ReasoningExtractie uit een woordenboek."""
        return cls(
            session_id=data["session_id"],
            agent_name=data["agent_name"],
            project_id=data.get("project_id"),
            reasoning_text=data["reasoning_text"],
            chain_of_thought_stappen=data.get("chain_of_thought_stappen", []),
            input_tokens=data.get("input_tokens", 0),
            reasoning_tokens=data.get("reasoning_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            model_name=data.get("model_name"),
            gecreeerd_op=data.get("gecreeerd_op", ""),
        )


# ── Hoofd-klasse ──────────────────────────────────────────────────────────────

class ReasoningLogger:
    """
    Extraheert en logt chain-of-thought reasoning uit LLM-uitvoer.

    Persistentie via JSON-bestanden in logs/reasoning/{agent_name}/.
    Alle methoden zijn synchronous en goedkoop — geschikt voor gebruik
    direct na een Ollama generate()-aanroep.
    """

    def __init__(self, logs_dir: Path = LOGS_DIR) -> None:
        self._logs_dir = logs_dir
        logger.debug("ReasoningLogger geïnitialiseerd (logs_dir=%s)", logs_dir)

    # ── Publieke API ──────────────────────────────────────────────────────────

    def extraheer_reasoning(self, tekst: str, agent_name: str) -> str | None:
        """
        Extraheer reasoning-blokken uit LLM-uitvoer.

        Probeert in volgorde:
        1. <reasoning>...</reasoning> tags (DOTALL)
        2. <thinking>...</thinking> tags (DOTALL)
        3. "Stap 1:", "Stap 2:" genummerde stappen (Nederlands)
        4. "Step 1:", "Step 2:" genummerde stappen (Engels)
        5. "1.", "2." patronen aan het begin van regels

        Returns:
            Geëxtraheerde tekst (stripped), of None als niets gevonden.
        """
        # 1 & 2: XML-achtige tags
        for pattern, label in _TAG_PATTERNS:
            match = re.search(pattern, tekst, re.DOTALL | re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if extracted:
                    logger.debug(
                        "Agent '%s': reasoning gevonden via %s (%d tekens)",
                        agent_name, label, len(extracted),
                    )
                    return extracted

        # 3, 4 & 5: Genummerde stappen
        for pattern, label in _STAP_PATTERNS:
            matches = re.findall(pattern, tekst, re.DOTALL)
            if len(matches) >= 2:
                # Meerdere stappen gevonden — samenvoegen
                extracted = "\n".join(
                    (m.strip() if isinstance(m, str) else m[0].strip())
                    for m in matches
                ).strip()
                if extracted:
                    logger.debug(
                        "Agent '%s': reasoning gevonden via %s (%d stappen)",
                        agent_name, label, len(matches),
                    )
                    return extracted

        logger.debug("Agent '%s': geen reasoning gevonden in uitvoer", agent_name)
        return None

    def tel_chain_of_thought_stappen(self, reasoning_tekst: str) -> list[str]:
        """
        Splits reasoning-tekst in individuele chain-of-thought stappen.

        Herkent:
        - "Stap N:" / "Step N:" regels
        - "N." aan het begin van een regel
        - Alinea's gescheiden door lege regels (als geen nummering)

        Returns:
            Lijst van stappenstrings (stripped, niet-leeg).
        """
        # Probeer expliciete Stap/Step nummering
        stap_re = re.compile(
            r"(?:Stap|Step)\s+\d+[:.]\s*.+?(?=(?:Stap|Step)\s+\d+|$)",
            re.DOTALL | re.IGNORECASE,
        )
        stappen = [m.strip() for m in stap_re.findall(reasoning_tekst) if m.strip()]
        if stappen:
            return stappen

        # Probeer "1. tekst" nummering
        num_re = re.compile(r"(?:^|\n)\d+\.\s+.+?(?=\n\d+\.|$)", re.DOTALL)
        stappen = [m.strip() for m in num_re.findall(reasoning_tekst) if m.strip()]
        if stappen:
            return stappen

        # Fallback: splits op lege regels (alinea's)
        alineas = [
            p.strip()
            for p in re.split(r"\n\s*\n", reasoning_tekst)
            if p.strip()
        ]
        return alineas if len(alineas) > 1 else [reasoning_tekst.strip()]

    def log_reasoning(
        self,
        llm_output: str,
        agent_name: str,
        model_name: str | None = None,
        project_id: str | None = None,
        input_tekst: str = "",
    ) -> ReasoningExtractie | None:
        """
        Alles-in-één: extraheer reasoning, tel tokens en sla op als JSON.

        Token-schatting: len(text) // 4 (geen tiktoken-dependency).
        Persistentie: logs/reasoning/{agent_name}/{session_id}.json

        Returns:
            ReasoningExtractie als er reasoning gevonden is, anders None.
        """
        reasoning = self.extraheer_reasoning(llm_output, agent_name)
        if reasoning is None:
            return None

        stappen = self.tel_chain_of_thought_stappen(reasoning)
        session_id = str(uuid.uuid4())
        nu = datetime.now(timezone.utc).isoformat()

        extractie = ReasoningExtractie(
            session_id=session_id,
            agent_name=agent_name,
            project_id=project_id,
            reasoning_text=reasoning,
            chain_of_thought_stappen=stappen,
            input_tokens=len(input_tekst) // 4,
            reasoning_tokens=len(reasoning) // 4,
            output_tokens=len(llm_output) // 4,
            model_name=model_name,
            gecreeerd_op=nu,
        )

        self._sla_op(extractie)
        logger.info(
            "Reasoning gelogd voor agent '%s': %d stappen, %d reasoning-tokens (sessie %s)",
            agent_name,
            len(stappen),
            extractie.reasoning_tokens,
            session_id,
        )
        return extractie

    def laad_reasoning_geschiedenis(
        self,
        agent_name: str,
        max_sessies: int = 50,
    ) -> list[ReasoningExtractie]:
        """
        Laad de meest recente reasoning-sessies voor een agent.

        Bestanden worden gesorteerd op aanmaaktijdstip (nieuwste eerst).

        Args:
            agent_name: Naam van de agent.
            max_sessies: Maximum aantal sessies om te laden.

        Returns:
            Lijst van ReasoningExtractie-objecten (nieuwste eerst).
        """
        agent_dir = self._logs_dir / agent_name
        if not agent_dir.exists():
            logger.debug("Geen reasoning-logs gevonden voor agent '%s'", agent_name)
            return []

        json_bestanden = sorted(
            agent_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:max_sessies]

        resultaten: list[ReasoningExtractie] = []
        for bestand in json_bestanden:
            try:
                data = json.loads(bestand.read_text(encoding="utf-8"))
                resultaten.append(ReasoningExtractie.from_dict(data))
            except Exception as exc:
                logger.warning("Kon reasoning-log niet laden (%s): %s", bestand.name, exc)

        return resultaten

    def analyseer_redeneerpatronen(self, agent_name: str) -> dict[str, Any]:
        """
        Analyseer redeneerpatronen over alle beschikbare sessies van een agent.

        Returns een dict met:
        - gem_stappen_per_sessie (float)
        - meest_voorkomende_keywords (list[tuple[str, int]], top 10)
        - gem_reasoning_tokens (float)
        - sessies_met_reasoning (str, percentage als "73.5%")
        - totaal_sessies (int)
        """
        sessies = self.laad_reasoning_geschiedenis(agent_name, max_sessies=200)
        totaal = len(sessies)

        if totaal == 0:
            return {
                "gem_stappen_per_sessie": 0.0,
                "meest_voorkomende_keywords": [],
                "gem_reasoning_tokens": 0.0,
                "sessies_met_reasoning": "0%",
                "totaal_sessies": 0,
            }

        # Gemiddeld aantal stappen
        gem_stappen = sum(len(s.chain_of_thought_stappen) for s in sessies) / totaal

        # Gemiddeld aantal reasoning-tokens
        gem_tokens = sum(s.reasoning_tokens for s in sessies) / totaal

        # Keyword-frequentie (woorden > 3 tekens, geen stopwoorden)
        alle_woorden: list[str] = []
        for sessie in sessies:
            woorden = re.findall(r"\b[a-zA-ZÀ-ÿ]{4,}\b", sessie.reasoning_text.lower())
            alle_woorden.extend(w for w in woorden if w not in _STOPWOORDEN)
        top_keywords = Counter(alle_woorden).most_common(10)

        # Percentage sessies mét reasoning (alle geladen sessies hebben reasoning)
        pct = "100.0%"  # alleen sessies mét reasoning worden opgeslagen

        return {
            "gem_stappen_per_sessie": round(gem_stappen, 2),
            "meest_voorkomende_keywords": top_keywords,
            "gem_reasoning_tokens": round(gem_tokens, 2),
            "sessies_met_reasoning": pct,
            "totaal_sessies": totaal,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _sla_op(self, extractie: ReasoningExtractie) -> None:
        """Sla een ReasoningExtractie op als JSON-bestand."""
        doelmap = self._logs_dir / extractie.agent_name
        try:
            doelmap.mkdir(parents=True, exist_ok=True)
            bestand = doelmap / f"{extractie.session_id}.json"
            bestand.write_text(
                json.dumps(extractie.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.debug("Reasoning opgeslagen: %s", bestand)
        except Exception as exc:
            logger.error(
                "Kon reasoning niet opslaan voor agent '%s' (sessie %s): %s",
                extractie.agent_name,
                extractie.session_id,
                exc,
            )


# ── Singleton ─────────────────────────────────────────────────────────────────

_logger_instance: ReasoningLogger | None = None


def get_reasoning_logger() -> ReasoningLogger:
    """Geef de singleton ReasoningLogger terug (lazy-geïnitialiseerd)."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ReasoningLogger()
    return _logger_instance
