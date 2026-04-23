"""
VorstersNV Mixture of Agents (MoA)
LLM-ensemble pattern voor diepgaande code-analyse.

Proposers (3 parallel) → elk een specialistisch perspectief
Aggregator (1)         → synthetiseert de beste inzichten

Gebruik:
    moa = get_mixture_of_agents()
    resultaat = await moa.run("Analyseer deze FastAPI service op kwaliteit", context=code_str)
    print(resultaat.aggregator_antwoord)

    # Met RAG context uit een klantproject:
    resultaat = await moa.run_met_rag_context("Wat zijn de grootste risico's?", project_id="PRJ-001")
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .client import OllamaClient, get_client

logger = logging.getLogger(__name__)

# ─── Proposer configuratie ────────────────────────────────────────────────────

@dataclass
class ProposerConfig:
    """Configuratie voor één proposer in de MoA-ensemble."""
    naam: str
    model: str
    temperature: float
    systeem_rol: str


DEFAULT_PROPOSERS: list[ProposerConfig] = [
    ProposerConfig(
        naam="java_specialist",
        model="codellama",
        temperature=0.3,
        systeem_rol=(
            "Je bent een Java/Spring Boot expert. "
            "Analyseer de code vanuit architectuur- en design pattern perspectief. "
            "Focus op SOLID-principes, layering, dependency management en schaalbaarheid. "
            "Antwoord altijd in het Nederlands."
        ),
    ),
    ProposerConfig(
        naam="kwaliteit_analyst",
        model="mistral",
        temperature=0.4,
        systeem_rol=(
            "Je bent een software kwaliteitsanalist. "
            "Focus op code smells, technische schuld en onderhoudbaarheid. "
            "Identificeer duplicatie, hoge complexiteit, slechte naamgeving en ontbrekende tests. "
            "Antwoord altijd in het Nederlands."
        ),
    ),
    ProposerConfig(
        naam="security_reviewer",
        model="llama3.2",
        temperature=0.2,
        systeem_rol=(
            "Je bent een security specialist. "
            "Analyseer de code op beveiligingsrisico's, OWASP Top 10 en kwetsbaarheden. "
            "Besteed aandacht aan injection, authenticatie, autorisatie, data-expositie en logging. "
            "Antwoord altijd in het Nederlands."
        ),
    ),
]

# ─── Resultaat dataclasses ────────────────────────────────────────────────────

@dataclass
class ProposerResultaat:
    """Resultaat van één proposer in de ensemble."""
    proposer_naam: str
    model: str
    antwoord: str
    interaction_id: str
    duur_seconden: float
    tokens_schatting: int   # len(antwoord) // 4


@dataclass
class MoAResultaat:
    """Volledig resultaat van een Mixture-of-Agents uitvoering."""
    vraag: str
    proposer_resultaten: list[ProposerResultaat]
    aggregator_antwoord: str
    aggregator_interaction_id: str
    totale_duur_seconden: float
    trace_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ─── Aggregator constanten ────────────────────────────────────────────────────

_AGGREGATOR_MODEL = "mistral"
_AGGREGATOR_TEMPERATURE = 0.3
_AGGREGATOR_MAX_TOKENS = 2048
_PROPOSER_MAX_TOKENS = 1536

_AGGREGATOR_SYSTEEM = (
    "Je bent een senior IT-architect en synthesizer. "
    "Je ontvangt meerdere analyses van gespecialiseerde AI-agents over dezelfde vraag of code. "
    "Jouw taak is om de beste, meest relevante inzichten te combineren tot één coherent, "
    "volledig en praktisch antwoord in het Nederlands. "
    "Vermijd herhaling. Structureer het antwoord helder met koppen indien zinvol. "
    "Wees concreet en actiegeritcht."
)


# ─── Mixture of Agents klasse ─────────────────────────────────────────────────

class MixtureOfAgents:
    """
    LLM-ensemble voor diepgaande analyse via parallelle specialisten + aggregatie.

    Drie proposers (elk een ander model + rol) worden parallel uitgevoerd.
    Een aggregator synthetiseert hun antwoorden tot het eindantwoord.
    """

    def __init__(
        self,
        proposers: list[ProposerConfig] | None = None,
        client: OllamaClient | None = None,
    ) -> None:
        self._proposers: list[ProposerConfig] = proposers if proposers is not None else DEFAULT_PROPOSERS
        self._client: OllamaClient | None = client

    def _get_client(self) -> OllamaClient:
        """Geef de Ollama client terug (singleton als niet geïnjecteerd)."""
        return self._client if self._client is not None else get_client()

    # ─── Proposer uitvoering ──────────────────────────────────────────────────

    async def _run_proposer(
        self,
        config: ProposerConfig,
        prompt: str,
        client: OllamaClient,
    ) -> ProposerResultaat:
        """
        Voer één proposer uit en retourneer zijn resultaat.

        Bij een fout wordt een foutmelding ingevuld als antwoord zodat de
        ensemble door kan gaan met de overige proposers.
        """
        start = time.monotonic()
        interaction_id = str(uuid.uuid4())
        try:
            antwoord = await client.generate(
                prompt=prompt,
                model=config.model,
                system=config.systeem_rol,
                temperature=config.temperature,
                max_tokens=_PROPOSER_MAX_TOKENS,
            )
            duur = time.monotonic() - start
            tokens_schatting = len(antwoord) // 4
            logger.info(
                "Proposer '%s' (%s) klaar in %.1fs — ~%d tokens",
                config.naam, config.model, duur, tokens_schatting,
            )
            return ProposerResultaat(
                proposer_naam=config.naam,
                model=config.model,
                antwoord=antwoord,
                interaction_id=interaction_id,
                duur_seconden=round(duur, 2),
                tokens_schatting=tokens_schatting,
            )
        except Exception as exc:  # noqa: BLE001
            duur = time.monotonic() - start
            fout_antwoord = f"[{config.naam} niet beschikbaar: {exc}]"
            logger.warning(
                "Proposer '%s' (%s) mislukt na %.1fs: %s",
                config.naam, config.model, duur, exc,
            )
            return ProposerResultaat(
                proposer_naam=config.naam,
                model=config.model,
                antwoord=fout_antwoord,
                interaction_id=interaction_id,
                duur_seconden=round(duur, 2),
                tokens_schatting=0,
            )

    # ─── Aggregator prompt opbouw ─────────────────────────────────────────────

    @staticmethod
    def _bouw_aggregator_prompt(
        vraag: str,
        proposer_resultaten: list[ProposerResultaat],
    ) -> str:
        """Bouw de aggregator-prompt op vanuit alle proposer-antwoorden."""
        n = len(proposer_resultaten)
        secties: list[str] = [
            f"Je ontvangt {n} analyses van verschillende AI-specialisten over dezelfde vraag of code.",
            "Syntheseer de beste inzichten tot één coherent, volledig antwoord in het Nederlands.",
            "",
        ]
        for pr in proposer_resultaten:
            secties.append(f"=== Analyse van {pr.proposer_naam} ({pr.model}) ===")
            secties.append(pr.antwoord)
            secties.append("")

        secties.append(f"Vraag: {vraag}")
        return "\n".join(secties)

    # ─── Publieke API ─────────────────────────────────────────────────────────

    async def run(
        self,
        vraag: str,
        context: str = "",
        trace_id: str | None = None,
    ) -> MoAResultaat:
        """
        Voer de Mixture-of-Agents pipeline uit.

        1. Alle proposers worden parallel uitgevoerd via asyncio.gather().
        2. De aggregator synthetiseert hun antwoorden.

        Args:
            vraag:     De vraag of analyse-opdracht.
            context:   Optionele extra context (bijv. code fragment).
            trace_id:  Optioneel trace-ID voor correlatie; wordt aangemaakt als None.

        Returns:
            MoAResultaat met alle proposer-antwoorden + het gesynthetiseerde eindantwoord.

        Raises:
            RuntimeError: Als alle proposers gefaald zijn.
        """
        trace_id = trace_id or str(uuid.uuid4())
        start_totaal = time.monotonic()
        client = self._get_client()

        # Bouw de proposer-prompt (vraag + eventuele context)
        if context:
            proposer_prompt = f"{context}\n\n{vraag}"
        else:
            proposer_prompt = vraag

        logger.info(
            "MoA gestart — trace_id=%s, %d proposers parallel",
            trace_id, len(self._proposers),
        )

        # ── Stap 1: Proposers parallel uitvoeren ──────────────────────────────
        proposer_taken = [
            self._run_proposer(cfg, proposer_prompt, client)
            for cfg in self._proposers
        ]
        proposer_resultaten: list[ProposerResultaat] = await asyncio.gather(*proposer_taken)

        # Controleer of minstens één proposer succesvol was
        succesvolle = [
            pr for pr in proposer_resultaten
            if not pr.antwoord.startswith("[") or "niet beschikbaar" not in pr.antwoord
        ]
        if not succesvolle:
            raise RuntimeError(
                f"Alle proposers gefaald voor trace_id={trace_id}. "
                "Controleer of Ollama bereikbaar is en de modellen beschikbaar zijn."
            )

        # ── Stap 2: Aggregator ────────────────────────────────────────────────
        aggregator_prompt = self._bouw_aggregator_prompt(vraag, proposer_resultaten)
        aggregator_interaction_id = str(uuid.uuid4())

        logger.info(
            "MoA aggregator gestart — trace_id=%s, model=%s",
            trace_id, _AGGREGATOR_MODEL,
        )
        aggregator_antwoord = await client.generate(
            prompt=aggregator_prompt,
            model=_AGGREGATOR_MODEL,
            system=_AGGREGATOR_SYSTEEM,
            temperature=_AGGREGATOR_TEMPERATURE,
            max_tokens=_AGGREGATOR_MAX_TOKENS,
        )
        totale_duur = time.monotonic() - start_totaal

        logger.info(
            "MoA klaar — trace_id=%s, totaal %.1fs, aggregator ~%d tokens",
            trace_id, totale_duur, len(aggregator_antwoord) // 4,
        )

        metadata: dict[str, Any] = {
            "proposer_namen": [pr.proposer_naam for pr in proposer_resultaten],
            "proposer_modellen": [pr.model for pr in proposer_resultaten],
            "succesvolle_proposers": len(succesvolle),
            "context_lengte": len(context),
            "aggregator_model": _AGGREGATOR_MODEL,
        }

        return MoAResultaat(
            vraag=vraag,
            proposer_resultaten=list(proposer_resultaten),
            aggregator_antwoord=aggregator_antwoord,
            aggregator_interaction_id=aggregator_interaction_id,
            totale_duur_seconden=round(totale_duur, 2),
            trace_id=trace_id,
            metadata=metadata,
        )

    async def run_met_rag_context(
        self,
        vraag: str,
        project_id: str,
        top_k: int = 3,
    ) -> MoAResultaat:
        """
        Voer MoA uit met RAG-context opgehaald uit een klantproject.

        De RAG-context wordt als extra context aan alle proposers meegegeven.
        Als de rag_engine module niet beschikbaar is, wordt MoA zonder context uitgevoerd.

        Args:
            vraag:       De vraag of analyse-opdracht.
            project_id:  ID van het klantproject in de RAG-index.
            top_k:       Aantal relevante fragmenten om op te halen.

        Returns:
            MoAResultaat met RAG-verrijkte analyse.
        """
        rag_context = ""
        try:
            from ollama.rag_engine import get_rag_engine  # type: ignore[import]
            rag_engine = get_rag_engine()
            rag_context = await rag_engine.get_context(project_id, vraag, top_k)
            logger.info(
                "RAG context opgehaald voor project_id=%s (%d tekens)",
                project_id, len(rag_context),
            )
        except ImportError:
            logger.warning(
                "rag_engine module niet beschikbaar — MoA wordt uitgevoerd zonder RAG context"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "RAG context ophalen mislukt voor project_id=%s: %s — doorgaan zonder context",
                project_id, exc,
            )

        return await self.run(vraag=vraag, context=rag_context)


# ─── Module-level singleton ───────────────────────────────────────────────────

_moa_instance: MixtureOfAgents | None = None


def get_mixture_of_agents() -> MixtureOfAgents:
    """Geef de singleton MixtureOfAgents instantie terug."""
    global _moa_instance
    if _moa_instance is None:
        _moa_instance = MixtureOfAgents()
    return _moa_instance
