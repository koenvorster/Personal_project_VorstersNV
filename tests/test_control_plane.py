"""Tests voor ollama/control_plane.py"""
import pytest

from ollama.control_plane import (
    ControlPlane,
    DeploymentRing,
    Environment,
    ExecutionContext,
    MaturityLevel,
    PolicyViolationError,
    WorkflowLane,
)
from ollama.events import EventType


@pytest.fixture
def cp() -> ControlPlane:
    return ControlPlane()


@pytest.fixture
def dev_context() -> ExecutionContext:
    return ExecutionContext(
        environment=Environment.DEV,
        risk_score=20,
        maturity_level=MaturityLevel.L3_TEAM_PRODUCTION,
        available_models=["llama3", "mistral", "codellama"],
    )


@pytest.fixture
def prod_context() -> ExecutionContext:
    return ExecutionContext(
        environment=Environment.PROD,
        risk_score=30,
        maturity_level=MaturityLevel.L4_BUSINESS_CRITICAL,
        available_models=["llama3", "mistral"],
    )


# ─────────────────────────────────────────────
# select_capability
# ─────────────────────────────────────────────

class TestSelectCapability:
    def test_order_created_maps_to_order_validation(self, cp):
        cap = cp.select_capability(EventType.ORDER_CREATED)
        assert cap == "order-validation"

    def test_payment_failed_maps_to_payment_retry(self, cp):
        cap = cp.select_capability(EventType.PAYMENT_FAILED)
        assert cap == "payment-retry"

    def test_fraud_detected_maps_to_risk_classification(self, cp):
        cap = cp.select_capability(EventType.FRAUD_DETECTED)
        assert cap == "risk-classification"

    def test_inventory_low_maps_to_inventory_reorder(self, cp):
        cap = cp.select_capability(EventType.INVENTORY_LOW)
        assert cap == "inventory-reorder"

    def test_code_released_maps_to_regression_analysis(self, cp):
        cap = cp.select_capability(EventType.CODE_RELEASED)
        assert cap == "regression-analysis"

    def test_unknown_event_falls_back_to_risk_classification(self, cp):
        # ORDER_SHIPPED is niet in de map
        cap = cp.select_capability(EventType.ORDER_SHIPPED)
        assert cap == "risk-classification"


# ─────────────────────────────────────────────
# select_execution_path
# ─────────────────────────────────────────────

class TestSelectExecutionPath:
    def test_fraud_detection_advisory_lane(self, cp, dev_context):
        path = cp.select_execution_path("fraud-detection", dev_context)
        assert path.lane == WorkflowLane.ADVISORY

    def test_order_validation_deterministic_lane(self, cp, dev_context):
        path = cp.select_execution_path("order-validation", dev_context)
        assert path.lane == WorkflowLane.DETERMINISTIC

    def test_product_content_generative_lane(self, cp, dev_context):
        path = cp.select_execution_path("product-content", dev_context)
        assert path.lane == WorkflowLane.GENERATIVE

    def test_order_blocking_action_lane(self, cp, dev_context):
        path = cp.select_execution_path("order-blocking", dev_context)
        assert path.lane == WorkflowLane.ACTION

    def test_high_risk_triggers_hitl(self, cp):
        ctx = ExecutionContext(risk_score=80, environment=Environment.DEV)
        path = cp.select_execution_path("fraud-detection", ctx)
        assert path.requires_hitl is True

    def test_low_risk_no_hitl_in_dev(self, cp, dev_context):
        path = cp.select_execution_path("fraud-detection", dev_context)
        assert path.requires_hitl is False

    def test_action_lane_in_prod_requires_hitl(self, cp, prod_context):
        path = cp.select_execution_path("order-blocking", prod_context)
        assert path.requires_hitl is True

    def test_unavailable_model_uses_fallback(self, cp):
        ctx = ExecutionContext(
            risk_score=80,
            available_models=["llama3"],  # mistral niet beschikbaar
            environment=Environment.DEV,
        )
        path = cp.select_execution_path("customer-service", ctx)
        assert path.primary_model in ctx.available_models

    def test_selection_reason_contains_key_info(self, cp, dev_context):
        path = cp.select_execution_path("fraud-detection", dev_context)
        assert "lane=" in path.selection_reason
        assert "risk=" in path.selection_reason

    def test_chain_name_for_order_created(self, cp):
        ctx = ExecutionContext(event_type=EventType.ORDER_CREATED)
        path = cp.select_execution_path("order-validation", ctx)
        assert path.chain_name == "ORDER_VALIDATION"

    def test_chain_name_for_payment_failed(self, cp):
        ctx = ExecutionContext(event_type=EventType.PAYMENT_FAILED)
        path = cp.select_execution_path("payment-retry", ctx)
        assert path.chain_name == "PAYMENT_RECOVERY"


# ─────────────────────────────────────────────
# enforce_policy
# ─────────────────────────────────────────────

class TestEnforcePolicy:
    def test_action_in_prod_without_hitl_raises(self, cp, prod_context):
        with pytest.raises(PolicyViolationError) as exc:
            cp.enforce_policy("order-blocking", prod_context)
        assert "HITL-001" in str(exc.value)

    def test_action_in_prod_with_hitl_approved_ok(self, cp):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=30,
            maturity_level=MaturityLevel.L4_BUSINESS_CRITICAL,
            metadata={"hitl_approved": True},
        )
        cp.enforce_policy("order-blocking", ctx)  # geen exception

    def test_high_risk_without_hitl_raises(self, cp, dev_context):
        dev_context.risk_score = 80
        with pytest.raises(PolicyViolationError) as exc:
            cp.enforce_policy("fraud-detection", dev_context)
        assert "HITL-002" in str(exc.value)

    def test_high_risk_with_hitl_approved_ok(self, cp):
        ctx = ExecutionContext(
            risk_score=80,
            environment=Environment.DEV,
            maturity_level=MaturityLevel.L3_TEAM_PRODUCTION,
            metadata={"hitl_approved": True},
        )
        cp.enforce_policy("fraud-detection", ctx)  # geen exception

    def test_l1_in_prod_raises(self, cp):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=10,
            maturity_level=MaturityLevel.L1_EXPERIMENTAL,
            metadata={"hitl_approved": True},  # HITL approved maar nog steeds L1 geblokkeerd
        )
        with pytest.raises(PolicyViolationError) as exc:
            cp.enforce_policy("fraud-detection", ctx)
        assert "MAT-001" in str(exc.value)

    def test_l2_in_prod_raises(self, cp):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=10,
            maturity_level=MaturityLevel.L2_INTERNAL_BETA,
            metadata={"hitl_approved": True},
        )
        with pytest.raises(PolicyViolationError) as exc:
            cp.enforce_policy("fraud-detection", ctx)
        assert "MAT-002" in str(exc.value)

    def test_l3_in_dev_no_violation(self, cp, dev_context):
        cp.enforce_policy("fraud-detection", dev_context)  # geen exception


# ─────────────────────────────────────────────
# check_budget
# ─────────────────────────────────────────────

class TestCheckBudget:
    def test_within_budget(self, cp):
        result = cp.check_budget("fraud-detection", {"tokens_used": 5000, "tool_calls": 2})
        assert result is True

    def test_exceeds_token_budget(self, cp):
        result = cp.check_budget("fraud-detection", {"tokens_used": 99999, "tool_calls": 1})
        assert result is False

    def test_exceeds_tool_calls(self, cp):
        result = cp.check_budget("fraud-detection", {"tokens_used": 100, "tool_calls": 10})
        assert result is False

    def test_unknown_capability_uses_defaults(self, cp):
        result = cp.check_budget("unknown-cap", {"tokens_used": 100, "tool_calls": 1})
        assert result is True


# ─────────────────────────────────────────────
# determine_rollout_ring
# ─────────────────────────────────────────────

class TestDetermineRolloutRing:
    def test_l1_always_local(self, cp):
        ctx = ExecutionContext(maturity_level=MaturityLevel.L1_EXPERIMENTAL, environment=Environment.PROD)
        assert cp.determine_rollout_ring(ctx) == DeploymentRing.LOCAL

    def test_l2_always_ai_team(self, cp):
        ctx = ExecutionContext(maturity_level=MaturityLevel.L2_INTERNAL_BETA, environment=Environment.PROD)
        assert cp.determine_rollout_ring(ctx) == DeploymentRing.AI_TEAM

    def test_l3_in_dev_internal_users(self, cp):
        ctx = ExecutionContext(maturity_level=MaturityLevel.L3_TEAM_PRODUCTION, environment=Environment.DEV)
        assert cp.determine_rollout_ring(ctx) == DeploymentRing.INTERNAL_USERS

    def test_l3_in_prod_limited(self, cp):
        ctx = ExecutionContext(maturity_level=MaturityLevel.L3_TEAM_PRODUCTION, environment=Environment.PROD)
        assert cp.determine_rollout_ring(ctx) == DeploymentRing.LIMITED_PRODUCTION

    def test_l4_full_production(self, cp):
        ctx = ExecutionContext(maturity_level=MaturityLevel.L4_BUSINESS_CRITICAL, environment=Environment.PROD)
        assert cp.determine_rollout_ring(ctx) == DeploymentRing.FULL_PRODUCTION


# ─────────────────────────────────────────────
# requires_human_approval
# ─────────────────────────────────────────────

class TestRequiresHumanApproval:
    def test_action_in_prod_requires_hitl(self, cp, prod_context):
        assert cp.requires_human_approval("order-blocking", prod_context) is True

    def test_action_in_dev_no_hitl(self, cp, dev_context):
        assert cp.requires_human_approval("order-blocking", dev_context) is False

    def test_high_risk_requires_hitl(self, cp, dev_context):
        dev_context.risk_score = 75
        assert cp.requires_human_approval("fraud-detection", dev_context) is True

    def test_low_risk_advisory_no_hitl(self, cp, dev_context):
        assert cp.requires_human_approval("fraud-detection", dev_context) is False

    def test_l1_in_prod_requires_hitl(self, cp):
        ctx = ExecutionContext(
            environment=Environment.PROD,
            risk_score=10,
            maturity_level=MaturityLevel.L1_EXPERIMENTAL,
        )
        assert cp.requires_human_approval("fraud-detection", ctx) is True
