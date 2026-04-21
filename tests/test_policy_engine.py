"""Tests voor ollama/policy_engine.py"""
import pytest
from pathlib import Path

from ollama.control_plane import (
    Environment,
    ExecutionContext,
    MaturityLevel,
    PolicyViolationError,
    WorkflowLane,
)
from ollama.events import EventType
from ollama.policy_engine import PolicyEngine, PolicyViolation, Severity


@pytest.fixture
def engine(tmp_path) -> PolicyEngine:
    """PolicyEngine met echte /policies/ YAML bestanden."""
    # Wijst naar de echte policies/ map van het project
    policies_dir = Path(__file__).parent.parent / "policies"
    e = PolicyEngine(policies_dir=policies_dir)
    return e


@pytest.fixture
def dev_ctx() -> ExecutionContext:
    return ExecutionContext(
        environment=Environment.DEV,
        risk_score=20,
        maturity_level=MaturityLevel.L3_TEAM_PRODUCTION,
    )


@pytest.fixture
def prod_ctx() -> ExecutionContext:
    return ExecutionContext(
        environment=Environment.PROD,
        risk_score=20,
        maturity_level=MaturityLevel.L4_BUSINESS_CRITICAL,
    )


# ─────────────────────────────────────────────
# HITL Policy Tests
# ─────────────────────────────────────────────

class TestHitlPolicies:
    def test_action_prod_without_hitl_is_blocker(self, engine, prod_ctx):
        violations = engine.evaluate(
            "order-blocking", prod_ctx, lane=WorkflowLane.ACTION
        )
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        assert any(v.rule_id == "HITL-001" for v in blockers)

    def test_action_prod_with_hitl_approved_no_blocker(self, engine):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=20,
            maturity_level=MaturityLevel.L4_BUSINESS_CRITICAL,
            metadata={"hitl_approved": True},
        )
        violations = engine.evaluate("order-blocking", ctx, lane=WorkflowLane.ACTION)
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        assert not any(v.rule_id == "HITL-001" for v in blockers)

    def test_high_risk_without_hitl_is_blocker(self, engine, dev_ctx):
        dev_ctx.risk_score = 80
        violations = engine.evaluate("fraud-detection", dev_ctx)
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        assert any(v.rule_id == "HITL-002" for v in blockers)

    def test_critical_risk_is_blocker(self, engine, dev_ctx):
        dev_ctx.risk_score = 95
        violations = engine.evaluate("fraud-detection", dev_ctx)
        blocker_ids = {v.rule_id for v in violations if v.severity == Severity.BLOCKER}
        assert "HITL-002" in blocker_ids or "HITL-003" in blocker_ids

    def test_low_risk_dev_no_hitl_blocker(self, engine, dev_ctx):
        violations = engine.evaluate("fraud-detection", dev_ctx)
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        assert not blockers


# ─────────────────────────────────────────────
# Maturity Policy Tests
# ─────────────────────────────────────────────

class TestMaturityPolicies:
    def test_l1_in_prod_is_blocker(self, engine):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=5,
            maturity_level=MaturityLevel.L1_EXPERIMENTAL,
            metadata={"hitl_approved": True},
        )
        violations = engine.evaluate("fraud-detection", ctx)
        blocker_ids = {v.rule_id for v in violations if v.severity == Severity.BLOCKER}
        assert "MAT-001" in blocker_ids

    def test_l2_in_prod_is_blocker(self, engine):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=5,
            maturity_level=MaturityLevel.L2_INTERNAL_BETA,
            metadata={"hitl_approved": True},
        )
        violations = engine.evaluate("fraud-detection", ctx)
        blocker_ids = {v.rule_id for v in violations if v.severity == Severity.BLOCKER}
        assert "MAT-002" in blocker_ids

    def test_l3_in_prod_is_warning_not_blocker(self, engine):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=5,
            maturity_level=MaturityLevel.L3_TEAM_PRODUCTION,
            metadata={"hitl_approved": True},
        )
        violations = engine.evaluate("fraud-detection", ctx)
        mat3_violations = [v for v in violations if v.rule_id == "MAT-003"]
        assert mat3_violations
        assert all(v.severity == Severity.WARNING for v in mat3_violations)

    def test_l4_in_prod_no_maturity_blocker(self, engine, prod_ctx):
        violations = engine.evaluate("fraud-detection", prod_ctx)
        mat_blockers = [v for v in violations if v.rule_id.startswith("MAT-") and v.severity == Severity.BLOCKER]
        assert not mat_blockers

    def test_l1_in_dev_no_blocker(self, engine):
        ctx = ExecutionContext(
            environment=Environment.DEV,
            maturity_level=MaturityLevel.L1_EXPERIMENTAL,
            risk_score=10,
        )
        violations = engine.evaluate("fraud-detection", ctx)
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        assert not blockers


# ─────────────────────────────────────────────
# Tool Policy Tests
# ─────────────────────────────────────────────

class TestToolPolicies:
    def test_denied_tool_for_fraud_detection(self, engine, dev_ctx):
        violations = engine.evaluate(
            "fraud-detection", dev_ctx,
            tools_requested=["backoffice-write"],
        )
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        assert blockers
        assert "TOOL-001" in {v.rule_id for v in blockers}

    def test_allowed_tool_for_fraud_detection(self, engine, dev_ctx):
        violations = engine.evaluate(
            "fraud-detection", dev_ctx,
            tools_requested=["mollie-api-readonly"],
        )
        tool_blockers = [v for v in violations if v.rule_id.startswith("TOOL-") and v.severity == Severity.BLOCKER]
        assert not tool_blockers

    def test_unknown_tool_for_fraud_detection_blocked(self, engine, dev_ctx):
        violations = engine.evaluate(
            "fraud-detection", dev_ctx,
            tools_requested=["some-unknown-tool"],
        )
        tool_blockers = [v for v in violations if v.rule_id.startswith("TOOL-") and v.severity == Severity.BLOCKER]
        assert tool_blockers

    def test_is_tool_allowed_deny(self, engine):
        assert engine.is_tool_allowed("fraud-detection", "backoffice-write") is False

    def test_is_tool_allowed_allow(self, engine):
        assert engine.is_tool_allowed("fraud-detection", "mollie-api-readonly") is True

    def test_is_tool_allowed_no_policy_returns_true(self, engine):
        assert engine.is_tool_allowed("unknown-capability", "any-tool") is True

    def test_get_allowed_tools(self, engine):
        tools = engine.get_allowed_tools("fraud-detection")
        assert tools is not None
        assert "mollie-api-readonly" in tools

    def test_get_denied_tools(self, engine):
        denied = engine.get_denied_tools("fraud-detection")
        assert "backoffice-write" in denied


# ─────────────────────────────────────────────
# enforce() Tests
# ─────────────────────────────────────────────

class TestEnforce:
    def test_enforce_raises_on_blocker(self, engine, dev_ctx):
        dev_ctx.risk_score = 80
        with pytest.raises(PolicyViolationError) as exc:
            engine.enforce("fraud-detection", dev_ctx)
        assert "HITL-002" in str(exc.value)

    def test_enforce_ok_returns_warnings(self, engine, dev_ctx):
        warnings = engine.enforce("fraud-detection", dev_ctx)
        # Geen blockers — warnings mogen bestaan
        assert isinstance(warnings, list)

    def test_enforce_with_denied_tool_raises(self, engine, dev_ctx):
        with pytest.raises(PolicyViolationError) as exc:
            engine.enforce("fraud-detection", dev_ctx, tools_requested=["order-db-write"])
        assert "TOOL-001" in str(exc.value)


# ─────────────────────────────────────────────
# ControlPlane.enforce_policy integratie
# ─────────────────────────────────────────────

class TestControlPlaneIntegration:
    def test_control_plane_delegates_to_policy_engine(self, dev_ctx):
        from ollama.control_plane import ControlPlane
        cp = ControlPlane()
        dev_ctx.risk_score = 80
        with pytest.raises(PolicyViolationError):
            cp.enforce_policy("fraud-detection", dev_ctx)

    def test_control_plane_with_tool_check(self, dev_ctx):
        from ollama.control_plane import ControlPlane
        cp = ControlPlane()
        with pytest.raises(PolicyViolationError) as exc:
            cp.enforce_policy("fraud-detection", dev_ctx, tools_requested=["backoffice-write"])
        assert "TOOL-001" in str(exc.value)

    def test_control_plane_clean_context_ok(self, dev_ctx):
        from ollama.control_plane import ControlPlane
        cp = ControlPlane()
        cp.enforce_policy("fraud-detection", dev_ctx)  # geen exception
