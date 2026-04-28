"""
VorstersNV Platform Adapter
Single entry-point facade that wires agent_runner through the full AI Control
Platform stack: ControlPlane → PolicyEngine → AgentRunner → CostGovernance
→ DecisionJournal → QualityMonitor → EventBus.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ..control.control_plane import (
    ControlPlane,
    Environment,
    ExecutionContext,
    ExecutionPath,
    MaturityLevel,
    PolicyViolationError,
)
from ..observability.decision_journal import (
    VERDICT_APPROVED,
    VERDICT_REJECTED,
    DecisionJournal,
    JournalEntry,
    get_decision_journal,
)
from ..observability.quality_monitor import QualityMonitor, get_quality_monitor
from ..agents.agent_runner import AgentRunner, get_runner
from ..core.events import DomainEvent, EventType, EventBus, OrderCreatedEvent, get_event_bus
from ..observability.cost_governance import CostGovernanceEngine, get_cost_governance

logger = logging.getLogger(__name__)

# Cost per token in EUR (matches cost_governance._COST_PER_TOKEN)
_COST_PER_TOKEN: float = 0.000002

# capability_id → agent_name mapping
_CAPABILITY_TO_AGENT: dict[str, str] = {
    "fraud-detection":    "fraude_detectie_agent",
    "order-validation":   "order_verwerking_agent",
    "content-generation": "product_beschrijving_agent",
    "customer-service":   "klantenservice_agent",
    "audit-reporting":    "audit_trace_agent",
}

_FALLBACK_AGENT = "audit_trace_agent"


# ─────────────────────────────────────────────
# Request / Result dataclasses
# ─────────────────────────────────────────────

@dataclass
class CapabilityRequest:
    capability_id: str
    user_input: str
    context: dict                                     # e.g. {"order_id": "...", "risk_signals": [...]}
    session_id: str = ""
    tools_requested: list[str] = field(default_factory=list)
    environment: str = "dev"                          # dev / test / staging / prod
    risk_score: int = 0                               # 0-100, pre-assessed risk


@dataclass
class CapabilityResult:
    capability_id: str
    trace_id: str
    agent_name: str
    model_used: str
    response: str
    validated_output: dict | None
    execution_path: str                               # e.g. "advisory/llama3"
    policy_violations: list[str]
    cost_eur: float
    latency_ms: float
    success: bool
    error: str | None = None


# ─────────────────────────────────────────────
# PlatformAdapter
# ─────────────────────────────────────────────

class PlatformAdapter:
    """
    Facade over the full AI Control Platform stack.

    Call run_capability() (async) or run_capability_sync() (sync wrapper)
    to execute any capability through the complete governance pipeline.
    """

    def __init__(self) -> None:
        self._control_plane = ControlPlane()

    async def run_capability(self, request: CapabilityRequest) -> CapabilityResult:
        """
        Full-stack execution pipeline:

        1. Control Plane → select ExecutionPath (capability, context, risk, env)
        2. Policy Engine → enforce policies (raises PolicyViolationError on BLOCKER)
        3. Agent Runner → run_agent(agent_name, user_input, context) → (response, id, validated)
        4. Cost Governance → estimate + record cost
        5. Decision Journal → log entry
        6. Quality Monitor → record_run
        7. Event Bus → emit ORDER_CREATED event with trace_id
        8. Return CapabilityResult
        """
        trace_id = str(uuid.uuid4())
        t0 = time.monotonic()

        agent_name = _CAPABILITY_TO_AGENT.get(request.capability_id, _FALLBACK_AGENT)

        # ── Build ExecutionContext ────────────────────────────────────────────
        try:
            env = Environment(request.environment)
        except ValueError:
            logger.warning("Unknown environment '%s', defaulting to dev", request.environment)
            env = Environment.DEV

        ctx = ExecutionContext(
            environment=env,
            risk_score=request.risk_score,
            trace_id=trace_id,
        )

        # ── Step 1: Control Plane — select ExecutionPath ──────────────────────
        exec_path: ExecutionPath = self._control_plane.select_execution_path(
            request.capability_id, ctx
        )
        model_used = exec_path.primary_model
        execution_path_str = f"{exec_path.lane.value}/{model_used}"

        # ── Step 2: Policy Engine — enforce ──────────────────────────────────
        try:
            self._control_plane.enforce_policy(
                request.capability_id,
                ctx,
                tools_requested=request.tools_requested if request.tools_requested else None,
            )
        except PolicyViolationError as exc:
            latency_ms = (time.monotonic() - t0) * 1000
            violations = [str(exc)]
            self._log_journal(
                trace_id=trace_id,
                capability=request.capability_id,
                agent_name=agent_name,
                model_used=model_used,
                verdict=VERDICT_REJECTED,
                env=request.environment,
                risk_score=request.risk_score,
                execution_time_ms=latency_ms,
                policy_violations=violations,
                selection_reason=exec_path.selection_reason,
            )
            self._record_quality(
                agent_name, request.capability_id,
                success=False, score=0.0,
                latency_ms=latency_ms, cost_eur=0.0,
            )
            return CapabilityResult(
                capability_id=request.capability_id,
                trace_id=trace_id,
                agent_name=agent_name,
                model_used=model_used,
                response="",
                validated_output=None,
                execution_path=execution_path_str,
                policy_violations=violations,
                cost_eur=0.0,
                latency_ms=latency_ms,
                success=False,
                error=str(exc),
            )

        # ── Step 3: Agent Runner — execute ────────────────────────────────────
        runner = get_runner()
        try:
            response, _interaction_id, validated = await runner.run_agent(
                agent_name=agent_name,
                user_input=request.user_input,
                context=request.context,
                session_id=request.session_id or None,
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - t0) * 1000
            logger.error("Agent '%s' execution failed: %s", agent_name, exc)
            self._log_journal(
                trace_id=trace_id,
                capability=request.capability_id,
                agent_name=agent_name,
                model_used=model_used,
                verdict=VERDICT_REJECTED,
                env=request.environment,
                risk_score=request.risk_score,
                execution_time_ms=latency_ms,
                policy_violations=[],
                selection_reason=exec_path.selection_reason,
            )
            self._record_quality(
                agent_name, request.capability_id,
                success=False, score=0.0,
                latency_ms=latency_ms, cost_eur=0.0,
            )
            return CapabilityResult(
                capability_id=request.capability_id,
                trace_id=trace_id,
                agent_name=agent_name,
                model_used=model_used,
                response="",
                validated_output=None,
                execution_path=execution_path_str,
                policy_violations=[],
                cost_eur=0.0,
                latency_ms=latency_ms,
                success=False,
                error=str(exc),
            )

        latency_ms = (time.monotonic() - t0) * 1000

        # ── Step 4: Cost Governance — estimate + record ───────────────────────
        input_tokens = max(1, len(request.user_input.split()))
        output_tokens = max(1, len(response.split()))
        cost_eur = (input_tokens + output_tokens) * _COST_PER_TOKEN

        cg: CostGovernanceEngine = get_cost_governance()
        cg.record_usage(request.capability_id, model_used, input_tokens, output_tokens, 0)

        # ── Step 5: Decision Journal — log ────────────────────────────────────
        self._log_journal(
            trace_id=trace_id,
            capability=request.capability_id,
            agent_name=agent_name,
            model_used=model_used,
            verdict=VERDICT_APPROVED,
            env=request.environment,
            risk_score=request.risk_score,
            execution_time_ms=latency_ms,
            policy_violations=[],
            selection_reason=exec_path.selection_reason,
        )

        # ── Step 6: Quality Monitor — record ─────────────────────────────────
        score = _extract_score(validated)
        self._record_quality(
            agent_name, request.capability_id,
            success=True, score=score,
            latency_ms=latency_ms, cost_eur=cost_eur,
        )

        # ── Step 7: Event Bus — emit ──────────────────────────────────────────
        await self._emit_event(trace_id, request.context)

        return CapabilityResult(
            capability_id=request.capability_id,
            trace_id=trace_id,
            agent_name=agent_name,
            model_used=model_used,
            response=response,
            validated_output=validated,
            execution_path=execution_path_str,
            policy_violations=[],
            cost_eur=cost_eur,
            latency_ms=latency_ms,
            success=True,
        )

    def run_capability_sync(self, request: CapabilityRequest) -> CapabilityResult:
        """Sync wrapper around run_capability() for non-async callers."""
        return asyncio.run(self.run_capability(request))

    # ── Private helpers ───────────────────────────────────────────────────────

    def _log_journal(
        self,
        *,
        trace_id: str,
        capability: str,
        agent_name: str,
        model_used: str,
        verdict: str,
        env: str,
        risk_score: int,
        execution_time_ms: float,
        policy_violations: list[str],
        selection_reason: str,
    ) -> None:
        journal: DecisionJournal = get_decision_journal()
        entry = JournalEntry(
            capability=capability,
            agent_name=agent_name,
            model_used=model_used,
            verdict=verdict,
            trace_id=trace_id,
            environment=env,
            risk_score=float(risk_score),
            execution_time_ms=execution_time_ms,
            policy_violations=policy_violations,
            selection_reason=selection_reason,
        )
        journal.record(entry)

    def _record_quality(
        self,
        agent_name: str,
        capability: str,
        *,
        success: bool,
        score: float,
        latency_ms: float,
        cost_eur: float,
    ) -> None:
        monitor: QualityMonitor = get_quality_monitor()
        monitor.record_run(
            agent_name=agent_name,
            capability=capability,
            success=success,
            score=score,
            latency_ms=latency_ms,
            cost_eur=cost_eur,
            human_escalated=False,
        )

    async def _emit_event(self, trace_id: str, context: dict[str, Any]) -> None:
        bus: EventBus = get_event_bus()
        event = OrderCreatedEvent(
            order_id=context.get("order_id", ""),
            trace_id=trace_id,
        )
        try:
            await bus.publish(event)
        except Exception as exc:
            logger.warning("EventBus emit failed (non-fatal): %s", exc)


# ─────────────────────────────────────────────
# Score extraction helper
# ─────────────────────────────────────────────

def _extract_score(validated_output: dict | None) -> float:
    """Extract quality score from validated agent output (0.0–1.0)."""
    if validated_output and "confidence" in validated_output:
        raw = validated_output["confidence"]
        if isinstance(raw, (int, float)):
            # If given as percentage (0–100), normalise to 0.0–1.0
            if raw > 1.0:
                return float(raw) / 100.0
            return float(raw)
    return 0.8


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

_adapter: PlatformAdapter | None = None


def get_platform_adapter() -> PlatformAdapter:
    """Return the singleton PlatformAdapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = PlatformAdapter()
    return _adapter
