"""
Tests voor V3 Skill Chain Orchestrator.
Dekt chain selectie, uitvoering, checkpoint recovery en singleton gedrag.
"""
import asyncio

import pytest

from ollama.skill_chain_orchestrator import (
    ChainContext,
    ChainDefinition,
    ChainResult,
    ChainStatus,
    ChainStep,
    SkillChainOrchestrator,
    SkillExecutor,
    get_skill_chain_orchestrator,
)


# ─────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────

def make_orchestrator() -> SkillChainOrchestrator:
    """Fresh orchestrator — geen singleton state."""
    return SkillChainOrchestrator()


def run(coro):
    """Sync wrapper voor async testen zonder pytest-asyncio dependency."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ─────────────────────────────────────────────
# select_chain — event-based routing
# ─────────────────────────────────────────────

class TestSelectChainEventRouting:
    def test_code_released_routes_to_release_chain(self):
        orch = make_orchestrator()
        chain, reasons = orch.select_chain("code_released")
        assert chain == "release-to-payroll-impact"

    def test_code_updated_routes_to_release_chain(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("code_updated")
        assert chain == "release-to-payroll-impact"

    def test_test_requested_routes_to_testing_chain(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("test_requested")
        assert chain == "testing-chain"

    def test_anomaly_detected_routes_to_prc(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("anomaly_detected")
        assert chain == "prc-decision-support"

    def test_fraud_detected_routes_to_prc(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("fraud_detected")
        assert chain == "prc-decision-support"

    def test_event_routing_returns_non_empty_reasons(self):
        orch = make_orchestrator()
        _, reasons = orch.select_chain("code_released")
        assert len(reasons) > 0

    def test_event_routing_reason_contains_event_type(self):
        orch = make_orchestrator()
        _, reasons = orch.select_chain("test_requested")
        assert any("test_requested" in r for r in reasons)

    def test_anomaly_reason_contains_chain_name(self):
        orch = make_orchestrator()
        _, reasons = orch.select_chain("anomaly_detected")
        assert any("prc-decision-support" in r for r in reasons)


# ─────────────────────────────────────────────
# select_chain — risk-based routing
# ─────────────────────────────────────────────

class TestSelectChainRiskRouting:
    def test_high_risk_routes_to_prc(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("unknown_event", risk_score=80)
        assert chain == "prc-decision-support"

    def test_risk_exactly_75_routes_to_prc(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("unknown_event", risk_score=75)
        assert chain == "prc-decision-support"

    def test_risk_74_falls_through_to_default(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("unknown_event", risk_score=74)
        assert chain == "testing-chain"

    def test_risk_zero_falls_through_to_default(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("unknown_event", risk_score=0)
        assert chain == "testing-chain"

    def test_risk_routing_reason_contains_score(self):
        orch = make_orchestrator()
        _, reasons = orch.select_chain("unknown", risk_score=90)
        assert any("90" in r for r in reasons)

    def test_default_fallback_reason_contains_event_type(self):
        orch = make_orchestrator()
        _, reasons = orch.select_chain("some_unknown_event", risk_score=0)
        assert any("some_unknown_event" in r for r in reasons)


# ─────────────────────────────────────────────
# select_chain — missing_data routing
# ─────────────────────────────────────────────

class TestSelectChainMissingData:
    def test_missing_payroll_data_routes_to_prc(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("unknown", missing_data=["payroll_data"])
        assert chain == "prc-decision-support"

    def test_missing_other_data_falls_through(self):
        orch = make_orchestrator()
        chain, _ = orch.select_chain("unknown", missing_data=["customer_data"])
        assert chain == "testing-chain"

    def test_missing_payroll_reason_is_recorded(self):
        orch = make_orchestrator()
        _, reasons = orch.select_chain("unknown", missing_data=["payroll_data"])
        assert any("payroll_data" in r for r in reasons)


# ─────────────────────────────────────────────
# list_chains / get_chain
# ─────────────────────────────────────────────

class TestChainLookup:
    def test_list_chains_contains_all_three(self):
        orch = make_orchestrator()
        chains = orch.list_chains()
        assert "release-to-payroll-impact" in chains
        assert "testing-chain" in chains
        assert "prc-decision-support" in chains

    def test_list_chains_length_is_three(self):
        orch = make_orchestrator()
        assert len(orch.list_chains()) == 3

    def test_get_chain_returns_chain_definition(self):
        orch = make_orchestrator()
        chain = orch.get_chain("testing-chain")
        assert isinstance(chain, ChainDefinition)

    def test_get_chain_name_matches(self):
        orch = make_orchestrator()
        chain = orch.get_chain("prc-decision-support")
        assert chain is not None
        assert chain.name == "prc-decision-support"

    def test_get_chain_nonexistent_returns_none(self):
        orch = make_orchestrator()
        assert orch.get_chain("nonexistent-chain") is None

    def test_get_chain_release_has_five_steps(self):
        orch = make_orchestrator()
        chain = orch.get_chain("release-to-payroll-impact")
        assert chain is not None
        assert len(chain.steps) == 5

    def test_get_chain_testing_has_three_steps(self):
        orch = make_orchestrator()
        chain = orch.get_chain("testing-chain")
        assert chain is not None
        assert len(chain.steps) == 3

    def test_get_chain_prc_has_four_steps(self):
        orch = make_orchestrator()
        chain = orch.get_chain("prc-decision-support")
        assert chain is not None
        assert len(chain.steps) == 4


# ─────────────────────────────────────────────
# run() — basis uitvoering
# ─────────────────────────────────────────────

class TestRunBasic:
    def test_run_valid_chain_returns_completed(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={"data": "test"}))
        assert result.status == ChainStatus.COMPLETED

    def test_run_completed_steps_contains_all_skills(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}))
        assert "validate_acceptance_criteria" in result.completed_steps
        assert "generate_advanced_test_cases" in result.completed_steps
        assert "detect_regression_risk" in result.completed_steps

    def test_run_outputs_contains_all_keys(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}))
        assert "criteria_result" in result.outputs
        assert "test_cases" in result.outputs
        assert "regression_risk" in result.outputs

    def test_run_nonexistent_chain_returns_failed(self):
        orch = make_orchestrator()
        result = run(orch.run("no-such-chain", inputs={}))
        assert result.status == ChainStatus.FAILED

    def test_run_nonexistent_chain_has_error_message(self):
        orch = make_orchestrator()
        result = run(orch.run("no-such-chain", inputs={}))
        assert result.error is not None
        assert "no-such-chain" in result.error

    def test_run_selection_reasons_not_empty(self):
        orch = make_orchestrator()
        result = run(orch.run("prc-decision-support", inputs={}))
        assert len(result.selection_reasons) > 0

    def test_run_chain_name_in_result(self):
        orch = make_orchestrator()
        result = run(orch.run("release-to-payroll-impact", inputs={}))
        assert result.chain_name == "release-to-payroll-impact"


# ─────────────────────────────────────────────
# run() — high-risk actions
# ─────────────────────────────────────────────

class TestRunHighRisk:
    def test_high_risk_triggers_actions(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, risk_score=80))
        assert len(result.high_risk_actions_triggered) > 0

    def test_high_risk_triggers_correct_actions_for_testing_chain(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, risk_score=80))
        assert "generate_test_documentation" in result.high_risk_actions_triggered

    def test_high_risk_triggers_all_prc_actions(self):
        orch = make_orchestrator()
        result = run(orch.run("prc-decision-support", inputs={}, risk_score=90))
        assert "audit_trace_generator" in result.high_risk_actions_triggered
        assert "decision_logging" in result.high_risk_actions_triggered

    def test_low_risk_does_not_trigger_actions(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, risk_score=40))
        assert result.high_risk_actions_triggered == []

    def test_risk_74_does_not_trigger_actions(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, risk_score=74))
        assert result.high_risk_actions_triggered == []

    def test_risk_75_triggers_actions(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, risk_score=75))
        assert len(result.high_risk_actions_triggered) > 0


# ─────────────────────────────────────────────
# run() — checkpoint recovery
# ─────────────────────────────────────────────

class TestCheckpointRecovery:
    def test_resume_from_checkpoint_skips_first_step(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, resume_from_checkpoint=0))
        assert "validate_acceptance_criteria" in result.skipped_steps

    def test_resume_from_checkpoint_1_skips_two_steps(self):
        orch = make_orchestrator()
        result = run(orch.run(
            "release-to-payroll-impact",
            inputs={},
            resume_from_checkpoint=1,
        ))
        assert len(result.skipped_steps) == 2

    def test_resume_reason_is_recorded(self):
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, resume_from_checkpoint=0))
        assert any("checkpoint" in r.lower() for r in result.selection_reasons)

    def test_resume_does_not_skip_all_steps_when_checkpoint_is_minus_1(self):
        """Geen checkpoint (None) → alle stappen uitgevoerd."""
        orch = make_orchestrator()
        result = run(orch.run("testing-chain", inputs={}, resume_from_checkpoint=None))
        assert len(result.skipped_steps) == 0
        assert len(result.completed_steps) == 3


# ─────────────────────────────────────────────
# ChainContext
# ─────────────────────────────────────────────

class TestChainContext:
    def _make_ctx(self) -> ChainContext:
        return ChainContext(
            chain_name="test-chain",
            event_type="test",
            risk_score=50,
            environment="dev",
        )

    def test_record_reason_accumulates(self):
        ctx = self._make_ctx()
        ctx.record_reason("reason-1")
        ctx.record_reason("reason-2")
        assert len(ctx.selection_reasons) == 2
        assert ctx.selection_reasons[0] == "reason-1"
        assert ctx.selection_reasons[1] == "reason-2"

    def test_save_checkpoint_sets_index(self):
        ctx = self._make_ctx()
        ctx.save_checkpoint(3)
        assert ctx.checkpoint == 3

    def test_get_step_input_without_input_from_returns_inputs(self):
        ctx = self._make_ctx()
        ctx.inputs = {"key": "value"}
        step = ChainStep(skill="some_skill", output_key="out")
        assert ctx.get_step_input(step) == {"key": "value"}

    def test_get_step_input_with_input_from_reads_outputs(self):
        ctx = self._make_ctx()
        ctx.outputs["prev_result"] = {"data": 42}
        step = ChainStep(skill="some_skill", output_key="out", input_from="prev_result")
        assert ctx.get_step_input(step) == {"data": 42}

    def test_get_step_input_missing_key_returns_none(self):
        ctx = self._make_ctx()
        step = ChainStep(skill="some_skill", output_key="out", input_from="nonexistent")
        assert ctx.get_step_input(step) is None

    def test_default_status_is_pending(self):
        ctx = self._make_ctx()
        assert ctx.status == ChainStatus.PENDING

    def test_checkpoint_starts_as_none(self):
        ctx = self._make_ctx()
        assert ctx.checkpoint is None


# ─────────────────────────────────────────────
# ChainDefinition
# ─────────────────────────────────────────────

class TestChainDefinition:
    def test_chain_definition_created_correctly(self):
        step = ChainStep(skill="my_skill", output_key="my_output")
        chain = ChainDefinition(
            name="my-chain",
            trigger="my_trigger",
            description="My description",
            steps=[step],
        )
        assert chain.name == "my-chain"
        assert chain.trigger == "my_trigger"
        assert chain.description == "My description"
        assert len(chain.steps) == 1
        assert chain.version == "1.0"
        assert chain.on_high_risk == []

    def test_chain_definition_with_on_high_risk(self):
        chain = ChainDefinition(
            name="risky",
            trigger="risk_event",
            description="Risky chain",
            steps=[],
            on_high_risk=["action_a", "action_b"],
        )
        assert chain.on_high_risk == ["action_a", "action_b"]


# ─────────────────────────────────────────────
# register_chain
# ─────────────────────────────────────────────

class TestRegisterChain:
    def test_register_chain_adds_to_orchestrator(self):
        orch = make_orchestrator()
        new_chain = ChainDefinition(
            name="custom-chain",
            trigger="custom_event",
            description="Custom chain",
            steps=[ChainStep("custom_skill", "custom_output")],
        )
        orch.register_chain(new_chain)
        assert "custom-chain" in orch.list_chains()

    def test_register_chain_retrievable_via_get_chain(self):
        orch = make_orchestrator()
        new_chain = ChainDefinition(
            name="another-chain",
            trigger="another_event",
            description="Another chain",
            steps=[],
        )
        orch.register_chain(new_chain)
        retrieved = orch.get_chain("another-chain")
        assert retrieved is not None
        assert retrieved.name == "another-chain"

    def test_register_chain_overrides_existing(self):
        orch = make_orchestrator()
        updated = ChainDefinition(
            name="testing-chain",
            trigger="updated_trigger",
            description="Updated testing chain",
            steps=[],
        )
        orch.register_chain(updated)
        retrieved = orch.get_chain("testing-chain")
        assert retrieved is not None
        assert retrieved.trigger == "updated_trigger"


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

class TestSingleton:
    def test_singleton_returns_same_instance(self):
        # Zorg dat singleton geïnitialiseerd is
        inst1 = get_skill_chain_orchestrator()
        inst2 = get_skill_chain_orchestrator()
        assert inst1 is inst2

    def test_singleton_is_skill_chain_orchestrator(self):
        inst = get_skill_chain_orchestrator()
        assert isinstance(inst, SkillChainOrchestrator)

    def test_singleton_has_all_chains(self):
        inst = get_skill_chain_orchestrator()
        assert len(inst.list_chains()) >= 3


# ─────────────────────────────────────────────
# Custom SkillExecutor
# ─────────────────────────────────────────────

class TestCustomSkillExecutor:
    def test_custom_executor_is_called(self):
        calls: list[str] = []

        class TrackingExecutor(SkillExecutor):
            async def execute(self, skill, input_data, context):
                calls.append(skill)
                return {"tracked": skill}

        orch = SkillChainOrchestrator(executor=TrackingExecutor())
        run(orch.run("testing-chain", inputs={}))
        assert "validate_acceptance_criteria" in calls
        assert "generate_advanced_test_cases" in calls
        assert "detect_regression_risk" in calls

    def test_custom_executor_output_stored_in_result(self):
        class CustomExecutor(SkillExecutor):
            async def execute(self, skill, input_data, context):
                return {"custom": True, "skill": skill}

        orch = SkillChainOrchestrator(executor=CustomExecutor())
        result = run(orch.run("testing-chain", inputs={}))
        assert result.outputs["criteria_result"] == {"custom": True, "skill": "validate_acceptance_criteria"}

    def test_executor_exception_results_in_failed_status(self):
        class FailingExecutor(SkillExecutor):
            async def execute(self, skill, input_data, context):
                raise RuntimeError("skill execution failed")

        orch = SkillChainOrchestrator(executor=FailingExecutor())
        result = run(orch.run("testing-chain", inputs={}))
        assert result.status == ChainStatus.FAILED
        assert result.error == "skill execution failed"
