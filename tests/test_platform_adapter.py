"""
Tests for ollama/platform_adapter.py — PlatformAdapter full-stack facade.

Covers:
- run_capability() happy path
- PolicyViolationError handling
- All 5 capability → agent mappings
- Unknown capability fallback
- run_capability_sync() wrapper
- Latency / trace_id / cost invariants
- DecisionJournal, QualityMonitor, EventBus call verification (mocked)
- Singleton identity
- Agent runner error handling
- Score extraction logic
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from ollama.platform_adapter import (
    CapabilityRequest,
    CapabilityResult,
    PlatformAdapter,
    _CAPABILITY_TO_AGENT,
    _FALLBACK_AGENT,
    _extract_score,
    get_platform_adapter,
)
from ollama.control_plane import PolicyViolationError
from ollama.decision_journal import VERDICT_APPROVED, VERDICT_REJECTED


# ─────────────────────────────────────────────
# Shared fixtures & helpers
# ─────────────────────────────────────────────

def _make_runner_mock(response: str = "mocked response") -> MagicMock:
    """Return an AgentRunner mock whose run_agent() is an AsyncMock."""
    mock = MagicMock()
    mock.run_agent = AsyncMock(return_value=(response, "interaction-id-123", None))
    return mock


def _make_request(
    capability_id: str = "fraud-detection",
    user_input: str = "Check this order",
    context: dict | None = None,
    environment: str = "dev",
    risk_score: int = 0,
    tools_requested: list[str] | None = None,
    session_id: str = "",
) -> CapabilityRequest:
    return CapabilityRequest(
        capability_id=capability_id,
        user_input=user_input,
        context=context or {"order_id": "ORD-1"},
        environment=environment,
        risk_score=risk_score,
        tools_requested=tools_requested or [],
        session_id=session_id,
    )


@pytest.fixture()
def adapter() -> PlatformAdapter:
    return PlatformAdapter()


# ─────────────────────────────────────────────
# 1. Happy path — CapabilityResult fields
# ─────────────────────────────────────────────

class TestHappyPath:
    async def test_returns_capability_result(self, adapter):
        runner_mock = _make_runner_mock("Good result")
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert isinstance(result, CapabilityResult)

    async def test_capability_id_preserved(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request(capability_id="order-validation"))
        assert result.capability_id == "order-validation"

    async def test_success_is_true(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.success is True

    async def test_error_is_none_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.error is None

    async def test_response_equals_agent_output(self, adapter):
        runner_mock = _make_runner_mock("expected output")
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.response == "expected output"

    async def test_model_used_not_empty(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.model_used != ""

    async def test_execution_path_not_empty(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.execution_path != ""

    async def test_execution_path_contains_model(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.model_used in result.execution_path

    async def test_policy_violations_empty_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.policy_violations == []

    async def test_validated_output_none_when_no_schema(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.validated_output is None

    async def test_validated_output_returned_when_present(self, adapter):
        mock = MagicMock()
        mock.run_agent = AsyncMock(
            return_value=("resp", "iid", {"confidence": 0.9, "fraud": False})
        )
        with patch("ollama.platform_adapter.get_runner", return_value=mock):
            result = await adapter.run_capability(_make_request())
        assert result.validated_output == {"confidence": 0.9, "fraud": False}


# ─────────────────────────────────────────────
# 2. Trace ID
# ─────────────────────────────────────────────

class TestTraceId:
    async def test_trace_id_is_valid_uuid(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        uuid.UUID(result.trace_id)  # raises if invalid

    async def test_trace_id_unique_per_call(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            r1 = await adapter.run_capability(_make_request())
            r2 = await adapter.run_capability(_make_request())
        assert r1.trace_id != r2.trace_id

    async def test_trace_id_is_string(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert isinstance(result.trace_id, str)


# ─────────────────────────────────────────────
# 3. Latency
# ─────────────────────────────────────────────

class TestLatency:
    async def test_latency_ms_non_negative(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.latency_ms >= 0

    async def test_latency_ms_is_float(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert isinstance(result.latency_ms, float)

    async def test_latency_ms_set_on_policy_violation(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("HITL-001", "test violation"),
        ):
            result = await adapter.run_capability(_make_request())
        assert result.latency_ms >= 0


# ─────────────────────────────────────────────
# 4. Policy Violation
# ─────────────────────────────────────────────

class TestPolicyViolation:
    async def test_policy_violation_sets_success_false(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("HITL-002", "high risk"),
        ):
            result = await adapter.run_capability(_make_request())
        assert result.success is False

    async def test_policy_violation_sets_error(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("HITL-002", "high risk"),
        ):
            result = await adapter.run_capability(_make_request())
        assert result.error is not None
        assert "HITL-002" in result.error

    async def test_policy_violation_populates_violations_list(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("HITL-002", "high risk"),
        ):
            result = await adapter.run_capability(_make_request())
        assert len(result.policy_violations) == 1

    async def test_policy_violation_response_empty(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("MAT-001", "not in prod"),
        ):
            result = await adapter.run_capability(_make_request())
        assert result.response == ""

    async def test_policy_violation_cost_zero(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("MAT-001", "not in prod"),
        ):
            result = await adapter.run_capability(_make_request())
        assert result.cost_eur == 0.0

    async def test_policy_violation_trace_id_still_set(self, adapter):
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("HITL-001", "action in prod"),
        ):
            result = await adapter.run_capability(_make_request())
        uuid.UUID(result.trace_id)  # still a valid UUID


# ─────────────────────────────────────────────
# 5. Capability → agent name mapping
# ─────────────────────────────────────────────

class TestCapabilityToAgentMapping:
    async def _agent_for(self, capability: str, adapter) -> str:
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request(capability_id=capability))
        return result.agent_name

    async def test_fraud_detection_maps_to_fraude_detectie_agent(self, adapter):
        agent = await self._agent_for("fraud-detection", adapter)
        assert agent == "fraude_detectie_agent"

    async def test_order_validation_maps_to_order_verwerking_agent(self, adapter):
        agent = await self._agent_for("order-validation", adapter)
        assert agent == "order_verwerking_agent"

    async def test_content_generation_maps_to_product_beschrijving_agent(self, adapter):
        agent = await self._agent_for("content-generation", adapter)
        assert agent == "product_beschrijving_agent"

    async def test_customer_service_maps_to_klantenservice_agent(self, adapter):
        agent = await self._agent_for("customer-service", adapter)
        assert agent == "klantenservice_agent"

    async def test_audit_reporting_maps_to_audit_trace_agent(self, adapter):
        agent = await self._agent_for("audit-reporting", adapter)
        assert agent == "audit_trace_agent"

    def test_mapping_dict_has_all_five_capabilities(self):
        assert len(_CAPABILITY_TO_AGENT) == 5
        assert "fraud-detection" in _CAPABILITY_TO_AGENT
        assert "order-validation" in _CAPABILITY_TO_AGENT
        assert "content-generation" in _CAPABILITY_TO_AGENT
        assert "customer-service" in _CAPABILITY_TO_AGENT
        assert "audit-reporting" in _CAPABILITY_TO_AGENT


# ─────────────────────────────────────────────
# 6. Unknown capability → fallback
# ─────────────────────────────────────────────

class TestUnknownCapability:
    async def test_unknown_capability_returns_result(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request(capability_id="unknown-cap"))
        assert isinstance(result, CapabilityResult)

    async def test_unknown_capability_uses_fallback_agent(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request(capability_id="unknown-cap"))
        assert result.agent_name == _FALLBACK_AGENT


# ─────────────────────────────────────────────
# 7. Sync wrapper
# ─────────────────────────────────────────────

class TestSyncWrapper:
    def test_run_capability_sync_returns_capability_result(self):
        adapter = PlatformAdapter()
        runner_mock = _make_runner_mock("sync response")
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = adapter.run_capability_sync(_make_request())
        assert isinstance(result, CapabilityResult)

    def test_run_capability_sync_success_true(self):
        adapter = PlatformAdapter()
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = adapter.run_capability_sync(_make_request())
        assert result.success is True

    def test_run_capability_sync_returns_response(self):
        adapter = PlatformAdapter()
        runner_mock = _make_runner_mock("hello from sync")
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = adapter.run_capability_sync(_make_request())
        assert result.response == "hello from sync"

    def test_run_capability_sync_trace_id_is_uuid(self):
        adapter = PlatformAdapter()
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = adapter.run_capability_sync(_make_request())
        uuid.UUID(result.trace_id)

    def test_run_capability_sync_policy_violation(self):
        adapter = PlatformAdapter()
        with patch.object(
            adapter._control_plane,
            "enforce_policy",
            side_effect=PolicyViolationError("HITL-002", "risk"),
        ):
            result = adapter.run_capability_sync(_make_request())
        assert result.success is False


# ─────────────────────────────────────────────
# 8. Cost
# ─────────────────────────────────────────────

class TestCost:
    async def test_cost_eur_positive_on_success(self, adapter):
        runner_mock = _make_runner_mock("some response with words")
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert result.cost_eur > 0.0

    async def test_cost_eur_is_float(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request())
        assert isinstance(result.cost_eur, float)

    async def test_longer_response_higher_cost(self, adapter):
        short_mock = _make_runner_mock("hi")
        long_mock = _make_runner_mock("word " * 200)
        with patch("ollama.platform_adapter.get_runner", return_value=short_mock):
            short = await adapter.run_capability(_make_request())
        with patch("ollama.platform_adapter.get_runner", return_value=long_mock):
            long = await adapter.run_capability(_make_request())
        assert long.cost_eur > short.cost_eur

    async def test_cost_governance_record_usage_called(self, adapter):
        runner_mock = _make_runner_mock("response text")
        cg_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_cost_governance", return_value=cg_mock),
        ):
            await adapter.run_capability(_make_request())
        cg_mock.record_usage.assert_called_once()

    async def test_cost_governance_called_with_capability(self, adapter):
        runner_mock = _make_runner_mock("x")
        cg_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_cost_governance", return_value=cg_mock),
        ):
            await adapter.run_capability(_make_request(capability_id="order-validation"))
        args = cg_mock.record_usage.call_args[0]
        assert args[0] == "order-validation"


# ─────────────────────────────────────────────
# 9. Decision Journal (mocked)
# ─────────────────────────────────────────────

class TestDecisionJournal:
    async def test_journal_record_called_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        journal_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_decision_journal", return_value=journal_mock),
        ):
            await adapter.run_capability(_make_request())
        journal_mock.record.assert_called_once()

    async def test_journal_record_called_on_policy_violation(self, adapter):
        journal_mock = MagicMock()
        with (
            patch.object(
                adapter._control_plane,
                "enforce_policy",
                side_effect=PolicyViolationError("HITL-002", "risk"),
            ),
            patch("ollama.platform_adapter.get_decision_journal", return_value=journal_mock),
        ):
            await adapter.run_capability(_make_request())
        journal_mock.record.assert_called_once()

    async def test_journal_entry_verdict_approved_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        journal_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_decision_journal", return_value=journal_mock),
        ):
            result = await adapter.run_capability(_make_request())
        entry = journal_mock.record.call_args[0][0]
        assert entry.verdict == VERDICT_APPROVED

    async def test_journal_entry_verdict_rejected_on_violation(self, adapter):
        journal_mock = MagicMock()
        with (
            patch.object(
                adapter._control_plane,
                "enforce_policy",
                side_effect=PolicyViolationError("HITL-002", "risk"),
            ),
            patch("ollama.platform_adapter.get_decision_journal", return_value=journal_mock),
        ):
            await adapter.run_capability(_make_request())
        entry = journal_mock.record.call_args[0][0]
        assert entry.verdict == VERDICT_REJECTED

    async def test_journal_entry_trace_id_matches_result(self, adapter):
        runner_mock = _make_runner_mock()
        journal_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_decision_journal", return_value=journal_mock),
        ):
            result = await adapter.run_capability(_make_request())
        entry = journal_mock.record.call_args[0][0]
        assert entry.trace_id == result.trace_id

    async def test_journal_entry_capability_matches(self, adapter):
        runner_mock = _make_runner_mock()
        journal_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_decision_journal", return_value=journal_mock),
        ):
            await adapter.run_capability(_make_request(capability_id="customer-service"))
        entry = journal_mock.record.call_args[0][0]
        assert entry.capability == "customer-service"


# ─────────────────────────────────────────────
# 10. Quality Monitor (mocked)
# ─────────────────────────────────────────────

class TestQualityMonitor:
    async def test_quality_monitor_called_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        monitor_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_quality_monitor", return_value=monitor_mock),
        ):
            await adapter.run_capability(_make_request())
        monitor_mock.record_run.assert_called_once()

    async def test_quality_monitor_called_on_policy_violation(self, adapter):
        monitor_mock = MagicMock()
        with (
            patch.object(
                adapter._control_plane,
                "enforce_policy",
                side_effect=PolicyViolationError("HITL-002", "risk"),
            ),
            patch("ollama.platform_adapter.get_quality_monitor", return_value=monitor_mock),
        ):
            await adapter.run_capability(_make_request())
        monitor_mock.record_run.assert_called_once()

    async def test_quality_monitor_success_true_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        monitor_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_quality_monitor", return_value=monitor_mock),
        ):
            await adapter.run_capability(_make_request())
        _, kwargs = monitor_mock.record_run.call_args
        assert kwargs.get("success") is True or monitor_mock.record_run.call_args[0][2] is True

    async def test_quality_monitor_success_false_on_violation(self, adapter):
        monitor_mock = MagicMock()
        with (
            patch.object(
                adapter._control_plane,
                "enforce_policy",
                side_effect=PolicyViolationError("HITL-002", "risk"),
            ),
            patch("ollama.platform_adapter.get_quality_monitor", return_value=monitor_mock),
        ):
            await adapter.run_capability(_make_request())
        record_args = monitor_mock.record_run.call_args
        # success is the 3rd positional arg (index 2) or kwarg
        success_val = (
            record_args.kwargs.get("success")
            if record_args.kwargs.get("success") is not None
            else record_args.args[2]
        )
        assert success_val is False

    async def test_quality_monitor_latency_ms_non_negative(self, adapter):
        runner_mock = _make_runner_mock()
        monitor_mock = MagicMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_quality_monitor", return_value=monitor_mock),
        ):
            result = await adapter.run_capability(_make_request())
        record_args = monitor_mock.record_run.call_args
        latency_val = (
            record_args.kwargs.get("latency_ms")
            if record_args.kwargs.get("latency_ms") is not None
            else record_args.args[4]
        )
        assert latency_val >= 0


# ─────────────────────────────────────────────
# 11. Agent Runner error handling
# ─────────────────────────────────────────────

class TestAgentRunnerError:
    async def test_agent_error_returns_failure_result(self, adapter):
        mock = MagicMock()
        mock.run_agent = AsyncMock(side_effect=ValueError("agent not found"))
        with patch("ollama.platform_adapter.get_runner", return_value=mock):
            result = await adapter.run_capability(_make_request())
        assert result.success is False

    async def test_agent_error_sets_error_field(self, adapter):
        mock = MagicMock()
        mock.run_agent = AsyncMock(side_effect=RuntimeError("connection refused"))
        with patch("ollama.platform_adapter.get_runner", return_value=mock):
            result = await adapter.run_capability(_make_request())
        assert "connection refused" in result.error

    async def test_agent_error_empty_response(self, adapter):
        mock = MagicMock()
        mock.run_agent = AsyncMock(side_effect=Exception("boom"))
        with patch("ollama.platform_adapter.get_runner", return_value=mock):
            result = await adapter.run_capability(_make_request())
        assert result.response == ""

    async def test_agent_error_latency_ms_set(self, adapter):
        mock = MagicMock()
        mock.run_agent = AsyncMock(side_effect=Exception("boom"))
        with patch("ollama.platform_adapter.get_runner", return_value=mock):
            result = await adapter.run_capability(_make_request())
        assert result.latency_ms >= 0


# ─────────────────────────────────────────────
# 12. Score extraction (_extract_score)
# ─────────────────────────────────────────────

class TestExtractScore:
    def test_none_returns_default(self):
        assert _extract_score(None) == 0.8

    def test_empty_dict_returns_default(self):
        assert _extract_score({}) == 0.8

    def test_confidence_0_to_1_used_directly(self):
        assert _extract_score({"confidence": 0.75}) == 0.75

    def test_confidence_0_returns_0(self):
        assert _extract_score({"confidence": 0.0}) == 0.0

    def test_confidence_1_returns_1(self):
        assert _extract_score({"confidence": 1.0}) == 1.0

    def test_confidence_percentage_divided_by_100(self):
        assert abs(_extract_score({"confidence": 80}) - 0.8) < 1e-9

    def test_confidence_100_returns_1(self):
        assert abs(_extract_score({"confidence": 100}) - 1.0) < 1e-9

    def test_other_fields_ignored_returns_default(self):
        assert _extract_score({"risk_score": 50}) == 0.8


# ─────────────────────────────────────────────
# 13. EventBus emission
# ─────────────────────────────────────────────

class TestEventBus:
    async def test_event_bus_publish_called_on_success(self, adapter):
        runner_mock = _make_runner_mock()
        bus_mock = MagicMock()
        bus_mock.publish = AsyncMock()
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_event_bus", return_value=bus_mock),
        ):
            await adapter.run_capability(_make_request())
        bus_mock.publish.assert_called_once()

    async def test_event_bus_failure_does_not_crash(self, adapter):
        runner_mock = _make_runner_mock()
        bus_mock = MagicMock()
        bus_mock.publish = AsyncMock(side_effect=RuntimeError("bus down"))
        with (
            patch("ollama.platform_adapter.get_runner", return_value=runner_mock),
            patch("ollama.platform_adapter.get_event_bus", return_value=bus_mock),
        ):
            result = await adapter.run_capability(_make_request())
        assert result.success is True  # bus error is non-fatal


# ─────────────────────────────────────────────
# 14. Singleton identity
# ─────────────────────────────────────────────

class TestSingleton:
    def test_get_platform_adapter_returns_platform_adapter(self):
        import ollama.platform_adapter as mod
        original = mod._adapter
        mod._adapter = None
        try:
            inst = get_platform_adapter()
            assert isinstance(inst, PlatformAdapter)
        finally:
            mod._adapter = original

    def test_get_platform_adapter_same_instance_twice(self):
        import ollama.platform_adapter as mod
        original = mod._adapter
        mod._adapter = None
        try:
            a = get_platform_adapter()
            b = get_platform_adapter()
            assert a is b
        finally:
            mod._adapter = original

    def test_get_platform_adapter_after_reset_creates_new(self):
        import ollama.platform_adapter as mod
        original = mod._adapter
        mod._adapter = None
        try:
            a = get_platform_adapter()
            mod._adapter = None
            b = get_platform_adapter()
            assert a is not b
        finally:
            mod._adapter = original


# ─────────────────────────────────────────────
# 15. Environment handling
# ─────────────────────────────────────────────

class TestEnvironmentHandling:
    async def test_dev_environment_accepted(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request(environment="dev"))
        assert result.success is True

    async def test_unknown_environment_falls_back_gracefully(self, adapter):
        runner_mock = _make_runner_mock()
        with patch("ollama.platform_adapter.get_runner", return_value=runner_mock):
            result = await adapter.run_capability(_make_request(environment="unknown-env"))
        assert isinstance(result, CapabilityResult)

    async def test_request_dataclass_default_environment_is_dev(self):
        req = CapabilityRequest(
            capability_id="fraud-detection",
            user_input="test",
            context={},
        )
        assert req.environment == "dev"

    async def test_request_dataclass_default_risk_score_zero(self):
        req = CapabilityRequest(
            capability_id="fraud-detection",
            user_input="test",
            context={},
        )
        assert req.risk_score == 0
