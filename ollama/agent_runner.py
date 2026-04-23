"""
VorstersNV Agent Runner
Voert AI-agents uit met Ollama op basis van YAML-configuraties.
"""
import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml

from .client import OllamaClient, get_client
from .memory import ContextAssembler, get_context_assembler
from .prompt_iterator import PromptIterator

# Optionele ReasoningLogger — als import mislukt, gewoon doorgaan
try:
    from .reasoning_logger import get_reasoning_logger as _get_reasoning_logger
    _REASONING_LOGGER_AVAILABLE = True
except Exception as _exc:  # pragma: no cover
    logger.debug("ReasoningLogger niet beschikbaar: %s", _exc)
    _REASONING_LOGGER_AVAILABLE = False

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).parent.parent / "agents"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Exceptions that trigger a retry (transient network/timeout issues)
_RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)


@dataclass
class RetryConfig:
    """Configuratie voor retry-logica bij Ollama-aanroepen."""
    max_retries: int = 3
    delay_seconds: float = 2.0
    backoff_factor: float = 2.0  # elke poging wacht delay * backoff_factor^attempt


class Agent:
    """Vertegenwoordigt een geconfigureerde AI-agent."""

    def __init__(self, config: dict[str, Any]):
        self.name = config["name"]
        self.model = config.get("model", "llama3")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1024)
        self.system_prompt = self._load_text(config.get("system_prompt_ref", ""))
        preprompt_ref = config.get("preprompt_ref", "")
        self.preprompt = self._load_text(preprompt_ref)
        self.output_schema: dict[str, Any] | None = config.get("output_schema")
        self._config = config

    def _load_text(self, ref: str) -> str:
        """Laad een tekstbestand vanuit de prompts map."""
        if not ref:
            return ""
        path = Path(__file__).parent.parent / ref
        if not path.exists():
            logger.warning("Prompt bestand niet gevonden: %s", path)
            return ""
        return path.read_text(encoding="utf-8")

    async def run(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
        client: OllamaClient | None = None,
        session_id: str | None = None,
        reasoning_logging_enabled: bool = True,
        project_id: str | None = None,
    ) -> tuple[str, str, dict[str, Any] | None]:
        """
        Voer de agent uit met de gegeven input.

        Args:
            user_input: De invoer van de gebruiker of het systeem
            context: Extra context-variabelen voor de pre-prompt
            client: Optioneel een aangepaste Ollama client
            session_id: Optioneel sessie-ID voor geheugen en context injectie
            reasoning_logging_enabled: Sla chain-of-thought reasoning op (standaard True)
            project_id: Optioneel project-ID voor reasoning-koppeling

        Returns:
            Tuple van (antwoord, interaction_id, validated_output)
            validated_output is None als er geen output_schema is of validatie mislukt.
        """
        if client is None:
            client = get_client()

        # Vul pre-prompt variabelen in als context beschikbaar is
        preprompt = self.preprompt
        if context and preprompt:
            for key, value in context.items():
                preprompt = preprompt.replace(f"{{{key}}}", str(value))

        # Inject versioned context via ContextAssembler
        assembler: ContextAssembler = get_context_assembler()
        task_context = preprompt if preprompt else ""
        versioned = assembler.assemble(
            task_context=task_context,
            session_id=session_id,
        )
        context_prefix = versioned.assemble()

        # Bouw de volledige prompt
        if context_prefix:
            full_prompt = context_prefix + "\n\n" + user_input
        elif preprompt:
            full_prompt = preprompt + "\n\n" + user_input
        else:
            full_prompt = user_input

        # Registreer user turn in geheugen indien sessie actief
        if session_id:
            assembler.record_turn(session_id, "user", user_input)

        logger.info("Agent '%s' wordt uitgevoerd (model: %s)", self.name, self.model)

        response = await client.generate(
            prompt=full_prompt,
            model=self.model,
            system=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        logger.info("Agent '%s' klaar. Respons: %d tekens", self.name, len(response))

        # Optioneel: log chain-of-thought reasoning
        if reasoning_logging_enabled and _REASONING_LOGGER_AVAILABLE:
            try:
                _get_reasoning_logger().log_reasoning(
                    llm_output=response,
                    agent_name=self.name,
                    model_name=self.model,
                    project_id=project_id,
                    input_tekst=user_input,
                )
            except Exception as _rl_exc:
                logger.debug("ReasoningLogger fout (niet-kritiek): %s", _rl_exc)

        # Registreer assistant turn in geheugen indien sessie actief
        if session_id:
            assembler.record_turn(session_id, "assistant", response)

        # Valideer outputtegen schema indien aanwezig
        validated: dict[str, Any] | None = None
        if self.output_schema:
            from .schema_validator import validate_output
            validated = validate_output(response, self.output_schema, self.name)
            if validated is None:
                logger.warning(
                    "Agent '%s': output-schema validatie mislukt — raw output wordt doorgegeven",
                    self.name,
                )

        # Log de interactie automatisch voor prompt-iteratie analyse
        iterator = PromptIterator(self.name)
        interaction_id = iterator.log_interaction(
            user_input=user_input,
            agent_output=response,
            metadata={"context": context or {}, "model": self.model},
        )

        return response, interaction_id, validated

    async def chat(
        self,
        history: list[dict[str, str]],
        client: OllamaClient | None = None,
    ) -> str:
        """
        Voer een multi-turn gesprek met de agent.

        Args:
            history: Lijst van eerdere berichten
            client: Optioneel een aangepaste Ollama client

        Returns:
            Het antwoord van de agent
        """
        if client is None:
            client = get_client()

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(history)

        return await client.chat(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


class AgentRunner:
    """Laadt en beheert alle geconfigureerde agents."""

    def __init__(self, agents_dir: Path = AGENTS_DIR):
        self.agents_dir = agents_dir
        self._agents: dict[str, Agent] = {}
        self._load_agents()

    def _load_agents(self):
        """Laad alle agent-configuraties vanuit de agents map."""
        if not self.agents_dir.exists():
            logger.warning("Agents map niet gevonden: %s", self.agents_dir)
            return
        for yaml_file in self.agents_dir.glob("*.yml"):
            try:
                config = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                agent = Agent(config)
                self._agents[agent.name] = agent
                logger.info("Agent geladen: %s", agent.name)
            except Exception as exc:
                logger.error("Fout bij laden agent %s: %s", yaml_file.name, exc)

    def get(self, name: str) -> Agent | None:
        """Geef een agent op naam terug."""
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """Geef een lijst van beschikbare agent-namen terug."""
        return list(self._agents.keys())

    async def run_agent(
        self,
        agent_name: str,
        user_input: str,
        context: dict[str, Any] | None = None,
        client: OllamaClient | None = None,
        session_id: str | None = None,
    ) -> tuple[str, str, dict[str, Any] | None]:
        """
        Voer een specifieke agent uit.

        Args:
            agent_name: Naam van de agent
            user_input: Invoer voor de agent
            context: Extra context-variabelen
            client: Optioneel een aangepaste Ollama client (handig voor testen)
            session_id: Optioneel sessie-ID voor geheugen en context injectie

        Returns:
            Tuple van (antwoord, interaction_id, validated_output)

        Raises:
            ValueError: Als de agent niet gevonden wordt
        """
        agent = self.get(agent_name)
        if agent is None:
            raise ValueError(f"Agent '{agent_name}' niet gevonden. Beschikbaar: {self.list_agents()}")
        return await agent.run(user_input, context=context, client=client, session_id=session_id)

    async def run_agent_with_retry(
        self,
        agent_name: str,
        user_input: str,
        context: dict[str, Any] | None = None,
        client: OllamaClient | None = None,
        retry_config: RetryConfig | None = None,
        session_id: str | None = None,
    ) -> tuple[str, str, dict[str, Any] | None]:
        """
        Voer een agent uit met automatische retry bij Ollama timeout/netwerkfouten.

        Args:
            agent_name: Naam van de agent
            user_input: Invoer voor de agent
            context: Extra context-variabelen
            client: Optioneel een aangepaste Ollama client
            retry_config: Retry-instellingen (standaard: 3 pogingen, 2s delay, factor 2)
            session_id: Optioneel sessie-ID voor geheugen en context injectie

        Returns:
            Tuple van (antwoord, interaction_id, validated_output)

        Raises:
            ValueError: Als de agent niet gevonden wordt
            Exception: Als alle retry-pogingen mislukken
        """
        cfg = retry_config or RetryConfig()
        last_exc: Exception | None = None

        for attempt in range(cfg.max_retries + 1):
            try:
                return await self.run_agent(
                    agent_name, user_input, context=context, client=client, session_id=session_id
                )
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < cfg.max_retries:
                    wait = cfg.delay_seconds * (cfg.backoff_factor ** attempt)
                    logger.warning(
                        "Agent '%s' timeout/netwerkfout (poging %d/%d) — wacht %.1fs: %s",
                        agent_name, attempt + 1, cfg.max_retries + 1, wait, exc,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        "Agent '%s' mislukt na %d pogingen: %s",
                        agent_name, cfg.max_retries + 1, exc,
                    )
            except Exception:
                # Niet-retrybare fout — meteen doorgooien
                raise

        raise last_exc  # type: ignore[misc]


# Singleton runner
_runner: AgentRunner | None = None


def get_runner() -> AgentRunner:
    """Geef de singleton AgentRunner terug."""
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner
