"""
VorstersNV API – Gedeelde FastAPI dependencies.
Gebruik Depends(get_agent_runner) in routers die AgentRunner nodig hebben.
"""
from typing import Annotated

from fastapi import Depends, Request

from ollama.agent_runner import AgentRunner


def get_agent_runner(request: Request) -> AgentRunner:
    """Geeft de AgentRunner singleton terug vanuit app.state (geïnitialiseerd in lifespan)."""
    runner: AgentRunner = request.app.state.agent_runner
    return runner


AgentRunnerDep = Annotated[AgentRunner, Depends(get_agent_runner)]
