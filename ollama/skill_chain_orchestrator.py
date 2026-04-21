"""
V3 Skill Chain Orchestrator — context-driven, event-triggered, fleet-aware.

Verschil met V2 (lineair):
- V3 = context-driven: kiest chain op basis van event_type + risk_level + missing_data
- Fleet delegatie: elke stap kan naar een gespecialiseerde agent
- Keuzereden: elke routing beslissing wordt gelogd
- Checkpoint recovery: chain kan hervat worden na fout
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# Import bestaande modules
try:
    from ollama.events import EventType, DomainEvent, CHAIN_FOR_EVENT
    from ollama.control_plane import ControlPlane, WorkflowLane, Environment
    from ollama.decision_journal import get_decision_journal
    from ollama.contracts import OrderAnalysisContract, FraudAssessmentContract
except ImportError:
    # Graceful fallback voor tests
    pass


class ChainStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"                     # wacht op HITL
    CHECKPOINT_RECOVERY = "checkpoint_recovery"


@dataclass
class ChainStep:
    skill: str
    output_key: str
    input_from: Optional[str] = None
    agent_hint: Optional[str] = None     # welke agent doet dit bij voorkeur
    required: bool = True


@dataclass
class ChainDefinition:
    name: str
    trigger: str
    description: str
    steps: list[ChainStep]
    on_high_risk: list[str] = field(default_factory=list)
    version: str = "1.0"


@dataclass
class ChainContext:
    """Runtime context voor een actieve chain execution."""
    chain_name: str
    event_type: str
    risk_score: int
    environment: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)   # output_key → result
    completed_steps: list[str] = field(default_factory=list)
    skipped_steps: list[str] = field(default_factory=list)
    selection_reasons: list[str] = field(default_factory=list)
    status: ChainStatus = ChainStatus.PENDING
    trace_id: str = ""
    checkpoint: Optional[int] = None     # index van laatste geslaagde stap

    def record_reason(self, reason: str) -> None:
        self.selection_reasons.append(reason)

    def save_checkpoint(self, step_index: int) -> None:
        self.checkpoint = step_index

    def get_step_input(self, step: ChainStep) -> Any:
        """Haalt input op voor step: uit outputs van vorige stap of inputs."""
        if step.input_from:
            return self.outputs.get(step.input_from)
        return self.inputs


@dataclass
class ChainResult:
    chain_name: str
    status: ChainStatus
    outputs: dict[str, Any]
    selection_reasons: list[str]
    completed_steps: list[str]
    skipped_steps: list[str]
    high_risk_actions_triggered: list[str] = field(default_factory=list)
    error: Optional[str] = None


class SkillExecutor:
    """Voert skills uit — in productie via agent fleet, in tests via mock."""

    async def execute(self, skill: str, input_data: Any, context: ChainContext) -> Any:
        """Executes a skill. Override in production to delegate to agent fleet."""
        # Default: passthrough (voor testen)
        return {"skill": skill, "result": f"executed_{skill}", "input": str(input_data)[:100]}


class SkillChainOrchestrator:
    """
    V3 context-driven orchestrator.

    Routing logica:
    - IF release_detected → run DEV chain
    - IF payroll_completed → run VALIDATION chain
    - IF anomaly_high → run EXPLANATION + ACTION chain
    """

    def __init__(self, executor: Optional[SkillExecutor] = None) -> None:
        self._executor = executor or SkillExecutor()
        self._chains: dict[str, ChainDefinition] = {}
        self._load_builtin_chains()

    def _load_builtin_chains(self) -> None:
        """Laadt de 3 V3 chains."""
        self._chains = {
            "release-to-payroll-impact": ChainDefinition(
                name="release-to-payroll-impact",
                trigger="code_released",
                description="Chain 1: Release → Payroll Impact",
                steps=[
                    ChainStep("analyze_code_changes", "code_analysis"),
                    ChainStep("map_changes_to_business_logic", "business_impact", input_from="code_analysis"),
                    ChainStep("detect_regression_scope", "regression_scope", input_from="business_impact"),
                    ChainStep("compare_with_previous_run", "comparison", input_from="regression_scope"),
                    ChainStep("detect_salary_anomalies", "anomalies", input_from="comparison"),
                ],
                on_high_risk=["classify_payroll_risk", "explain_salary_difference", "suggest_prc_actions"],
            ),
            "testing-chain": ChainDefinition(
                name="testing-chain",
                trigger="test_requested",
                description="Chain 2: Testing Intelligence",
                steps=[
                    ChainStep("validate_acceptance_criteria", "criteria_result"),
                    ChainStep("generate_advanced_test_cases", "test_cases", input_from="criteria_result"),
                    ChainStep("detect_regression_risk", "regression_risk", input_from="test_cases"),
                ],
                on_high_risk=["generate_test_documentation"],
            ),
            "prc-decision-support": ChainDefinition(
                name="prc-decision-support",
                trigger="anomaly_detected",
                description="Chain 3: PRC Decision Support",
                steps=[
                    ChainStep("detect_salary_anomalies", "anomalies"),
                    ChainStep("classify_payroll_risk", "risk_class", input_from="anomalies"),
                    ChainStep("explain_salary_difference", "explanation", input_from="risk_class"),
                    ChainStep("suggest_prc_actions", "actions", input_from="explanation"),
                ],
                on_high_risk=["audit_trace_generator", "decision_logging"],
            ),
        }

    def select_chain(
        self,
        event_type: str,
        risk_score: int = 0,
        missing_data: Optional[list[str]] = None,
    ) -> tuple[str, list[str]]:
        """
        Context-driven chain selectie. Returns (chain_name, reasons).

        IF release_detected → release-to-payroll-impact
        IF test_requested  → testing-chain
        IF anomaly_detected OR risk_score >= 75 → prc-decision-support
        """
        reasons: list[str] = []
        missing_data = missing_data or []

        # Event-based routing
        event_chain_map: dict[str, str] = {
            "code_released": "release-to-payroll-impact",
            "code_updated":  "release-to-payroll-impact",
            "test_requested": "testing-chain",
            "anomaly_detected": "prc-decision-support",
            "fraud_detected": "prc-decision-support",
        }

        if event_type in event_chain_map:
            chain = event_chain_map[event_type]
            reasons.append(f"event_type={event_type} → {chain}")
            return chain, reasons

        # Risk-based routing
        if risk_score >= 75:
            reasons.append(f"risk_score={risk_score} >= 75 → prc-decision-support")
            return "prc-decision-support", reasons

        # Missing data fallback
        if "payroll_data" in missing_data:
            reasons.append("missing_data=payroll_data → prc-decision-support")
            return "prc-decision-support", reasons

        # Default
        reasons.append(f"default fallback for event_type={event_type}")
        return "testing-chain", reasons

    async def run(
        self,
        chain_name: str,
        inputs: dict[str, Any],
        risk_score: int = 0,
        environment: str = "dev",
        resume_from_checkpoint: Optional[int] = None,
    ) -> ChainResult:
        """Voert een chain uit met checkpoint recovery."""
        trace_id = hashlib.sha256(f"{chain_name}:{time.time()}".encode()).hexdigest()[:12]

        chain = self._chains.get(chain_name)
        if not chain:
            return ChainResult(
                chain_name=chain_name,
                status=ChainStatus.FAILED,
                outputs={},
                selection_reasons=[],
                completed_steps=[],
                skipped_steps=[],
                error=f"Chain '{chain_name}' not found",
            )

        ctx = ChainContext(
            chain_name=chain_name,
            event_type=chain.trigger,
            risk_score=risk_score,
            environment=environment,
            inputs=inputs,
            trace_id=trace_id,
            status=ChainStatus.RUNNING,
        )

        if resume_from_checkpoint is not None:
            ctx.checkpoint = resume_from_checkpoint
            ctx.status = ChainStatus.CHECKPOINT_RECOVERY
            ctx.record_reason(f"Resuming from checkpoint step {resume_from_checkpoint}")

        start_index = resume_from_checkpoint + 1 if resume_from_checkpoint is not None else 0

        try:
            for i, step in enumerate(chain.steps):
                if i < start_index:
                    ctx.skipped_steps.append(step.skill)
                    continue

                step_input = ctx.get_step_input(step)
                result = await self._executor.execute(step.skill, step_input, ctx)
                ctx.outputs[step.output_key] = result
                ctx.completed_steps.append(step.skill)
                ctx.save_checkpoint(i)
                ctx.record_reason(f"step[{i}] {step.skill} → {step.output_key}")

            # High-risk actions
            high_risk_triggered: list[str] = []
            if risk_score >= 75 and chain.on_high_risk:
                ctx.record_reason(f"risk_score={risk_score} >= 75 → triggering high-risk actions")
                for skill in chain.on_high_risk:
                    await self._executor.execute(skill, ctx.outputs, ctx)
                    high_risk_triggered.append(skill)

            ctx.status = ChainStatus.COMPLETED
            return ChainResult(
                chain_name=chain_name,
                status=ChainStatus.COMPLETED,
                outputs=ctx.outputs,
                selection_reasons=ctx.selection_reasons,
                completed_steps=ctx.completed_steps,
                skipped_steps=ctx.skipped_steps,
                high_risk_actions_triggered=high_risk_triggered,
            )

        except Exception as e:
            ctx.status = ChainStatus.FAILED
            return ChainResult(
                chain_name=chain_name,
                status=ChainStatus.FAILED,
                outputs=ctx.outputs,
                selection_reasons=ctx.selection_reasons,
                completed_steps=ctx.completed_steps,
                skipped_steps=ctx.skipped_steps,
                error=str(e),
            )

    def get_chain(self, name: str) -> Optional[ChainDefinition]:
        return self._chains.get(name)

    def list_chains(self) -> list[str]:
        return list(self._chains.keys())

    def register_chain(self, chain: ChainDefinition) -> None:
        self._chains[chain.name] = chain


_orchestrator: Optional[SkillChainOrchestrator] = None


def get_skill_chain_orchestrator() -> SkillChainOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SkillChainOrchestrator()
    return _orchestrator
