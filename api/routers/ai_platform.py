"""
VorstersNV AI Control Platform — REST API Router.
Exposes quality monitoring, decision journal, observability and capability registry.
"""
from __future__ import annotations

import dataclasses
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.auth.jwt import TokenData, require_admin_or_tester
from ollama.capability_registry import CapabilityRegistry, get_capability_registry
from ollama.decision_journal import get_decision_journal
from ollama.observability import get_observability_collector
from ollama.platform_adapter import CapabilityRequest, get_platform_adapter
from ollama.quality_monitor import get_quality_monitor

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class RunCapabilityRequest(BaseModel):
    capability_id: str = Field(description="e.g. fraud-detection, order-validation")
    user_input: str = Field(min_length=1, description="The input message for the AI agent")
    context: dict = Field(default_factory=dict, description="Domain context (order_id, etc.)")
    session_id: str = Field(default="", description="Optional session ID for memory")
    tools_requested: list[str] = Field(default_factory=list)
    environment: str = Field(default="dev", pattern="^(dev|test|staging|prod)$")
    risk_score: int = Field(default=0, ge=0, le=100)


class RunCapabilityResponse(BaseModel):
    capability_id: str
    trace_id: str
    agent_name: str
    model_used: str
    response: str
    validated_output: dict | None
    execution_path: str
    policy_violations: list[str]
    cost_eur: float
    latency_ms: float
    success: bool
    error: str | None


class RecordRunRequest(BaseModel):
    agent_name: str
    capability: str
    success: bool
    score: float = Field(ge=0.0, le=1.0)
    latency_ms: float = Field(ge=0.0)
    cost_eur: float = Field(ge=0.0, default=0.0)
    human_escalated: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _entry_to_dict(entry) -> dict:
    """Serialize a JournalEntry to a JSON-safe dict."""
    return {
        "trace_id": entry.trace_id,
        "capability": entry.capability,
        "agent_name": entry.agent_name,
        "model_used": entry.model_used,
        "tools_used": entry.tools_used,
        "selection_reason": entry.selection_reason,
        "alternatives_considered": entry.alternatives_considered,
        "human_override": entry.human_override,
        "verdict": entry.verdict,
        "timestamp": entry.timestamp.isoformat(),
        "environment": entry.environment,
        "risk_score": entry.risk_score,
        "execution_time_ms": entry.execution_time_ms,
        "policy_violations": entry.policy_violations,
    }


def _cap_to_dict(cap) -> dict:
    """Convert a CapabilityDefinition to a summary dict."""
    return {
        "id": cap.name,
        "name": cap.name,
        "version": cap.version,
        "description": cap.description,
        "maturity_level": cap.maturity.level,
        "lane": cap.lane,
        "ring": cap.release.rollout_ring,
        "is_production_ready": cap.is_production_ready(),
        "owner": cap.operational.owner,
        "sla_tier": cap.operational.sla_tier,
        "audience": cap.audience,
        "risk": cap.risk,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health", summary="AI Platform Health Check")
async def health():
    return {
        "status": "ok",
        "platform_version": "5.0",
        "components": {
            "quality_monitor": "active",
            "decision_journal": "active",
            "observability": "active",
            "capability_registry": "active",
        },
    }


@router.post(
    "/run",
    response_model=RunCapabilityResponse,
    summary="Run een AI capability via de volledige Control Platform stack",
    description="Voert een capability uit via Control Plane → Policy Engine → Agent Runner → Decision Journal → Quality Monitor.",
    status_code=200,
)
async def run_capability(
    request: RunCapabilityRequest,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
) -> RunCapabilityResponse:
    cap_request = CapabilityRequest(
        capability_id=request.capability_id,
        user_input=request.user_input,
        context=request.context,
        session_id=request.session_id,
        tools_requested=request.tools_requested,
        environment=request.environment,
        risk_score=request.risk_score,
    )
    result = await get_platform_adapter().run_capability(cap_request)
    if result.policy_violations:
        logger.warning(
            "Policy violations for capability '%s': %s",
            request.capability_id,
            result.policy_violations,
        )
    return RunCapabilityResponse(
        capability_id=result.capability_id,
        trace_id=result.trace_id,
        agent_name=result.agent_name,
        model_used=result.model_used,
        response=result.response,
        validated_output=result.validated_output,
        execution_path=result.execution_path,
        policy_violations=result.policy_violations,
        cost_eur=result.cost_eur,
        latency_ms=result.latency_ms,
        success=result.success,
        error=result.error,
    )


@router.get("/quality/report", summary="Platform Quality Report")
async def quality_report(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    monitor = get_quality_monitor()
    report = monitor.generate_report()
    d = dataclasses.asdict(report)
    return d


@router.get("/quality/alerts", summary="Active Quality Alerts")
async def quality_alerts(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    monitor = get_quality_monitor()
    return monitor.get_alerts()


@router.post("/quality/record-run", summary="Record Agent Run Metrics")
async def record_run(
    body: RecordRunRequest,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    monitor = get_quality_monitor()
    monitor.record_run(
        agent_name=body.agent_name,
        capability=body.capability,
        success=body.success,
        score=body.score,
        latency_ms=body.latency_ms,
        cost_eur=body.cost_eur,
        human_escalated=body.human_escalated,
    )
    return {"recorded": True, "agent_name": body.agent_name}


@router.get("/decisions", summary="Decision Journal Entries")
async def list_decisions(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    capability: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    journal = get_decision_journal()
    if capability:
        entries = journal.list_by_capability(capability)
    else:
        entries = list(journal._store.values())

    # Return the last N (most recent)
    entries = entries[-limit:]
    return [_entry_to_dict(e) for e in entries]


@router.get("/observability/dashboard", summary="Observability Dashboard Snapshot")
async def observability_dashboard(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    collector = get_observability_collector()
    return collector.get_dashboard_snapshot()


@router.get("/capabilities", summary="List All Capabilities")
async def list_capabilities(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    registry = get_capability_registry()
    names = registry.list_all()
    result = []
    for name in names:
        cap = registry.get(name)
        if cap:
            result.append(_cap_to_dict(cap))
    return result


@router.get("/capabilities/{capability_id}", summary="Get Capability by ID")
async def get_capability(
    capability_id: str,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    registry = get_capability_registry()
    cap = registry.get(capability_id)
    if cap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Capability '{capability_id}' not found",
        )
    return {
        "id": cap.name,
        "name": cap.name,
        "version": cap.version,
        "description": cap.description,
        "lane": cap.lane,
        "audience": cap.audience,
        "risk": cap.risk,
        "maturity": {
            "level": cap.maturity.level,
            "label": cap.maturity.label,
            "eval_required": cap.maturity.eval_required,
            "human_approval_required": cap.maturity.human_approval_required,
            "min_first_pass_score": cap.maturity.min_first_pass_score,
        },
        "operational": {
            "owner": cap.operational.owner,
            "sla_tier": cap.operational.sla_tier,
            "cost_budget_monthly_eur": cap.operational.cost_budget_monthly_eur,
            "preferred_model": cap.operational.preferred_model,
            "escalation_model": cap.operational.escalation_model,
        },
        "release": {
            "rollout_ring": cap.release.rollout_ring,
            "feature_flag": cap.release.feature_flag,
        },
        "agents": cap.agents,
        "contract": cap.contract,
        "chain": cap.chain,
        "is_production_ready": cap.is_production_ready(),
    }
