"""Ollama integratie package voor VorstersNV."""
from .agents.agent_runner import Agent, AgentRunner, get_runner
from .agents.consultancy_runner import (
    ConsultancyOrchestratorRunner,
    ConsultancyResult,
    get_consultancy_runner,
)
from .agents.orchestrator import AgentOrchestrator, OrchestratorResult, OrchestratorStep, get_orchestrator
from .core.client import OllamaClient, get_client
from .observability.prompt_iterator import PromptIterator

__all__ = [
    "OllamaClient",
    "get_client",
    "Agent",
    "AgentRunner",
    "get_runner",
    "PromptIterator",
    "AgentOrchestrator",
    "OrchestratorStep",
    "OrchestratorResult",
    "get_orchestrator",
    "ConsultancyOrchestratorRunner",
    "ConsultancyResult",
    "get_consultancy_runner",
]
