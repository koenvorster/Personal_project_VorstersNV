"""Tests voor ollama/deployment_rings.py"""
from __future__ import annotations

import pytest

from ollama.control_plane import DeploymentRing, MaturityLevel
from ollama.deployment_rings import (
    RingGateChecker,
    RingPolicy,
    RING_POLICIES,
    get_ring_policy,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def checker() -> RingGateChecker:
    return RingGateChecker()


@pytest.fixture
def all_gates_pass() -> dict:
    return {
        "evals_passed": True,
        "policy_passed": True,
        "observability_ok": True,
        "rollback_plan": True,
        "error_rate": 0.01,
    }


@pytest.fixture
def all_gates_fail() -> dict:
    return {
        "evals_passed": False,
        "policy_passed": False,
        "observability_ok": False,
        "rollback_plan": False,
        "error_rate": 0.50,
    }


# ─────────────────────────────────────────────
# RING_POLICIES volledigheid
# ─────────────────────────────────────────────

class TestRingPoliciesCompleteness:
    def test_all_rings_have_policy(self):
        for ring in DeploymentRing:
            assert ring in RING_POLICIES, f"Ring {ring} ontbreekt in RING_POLICIES"

    def test_ring_policies_are_ring_policy_instances(self):
        for ring, policy in RING_POLICIES.items():
            assert isinstance(policy, RingPolicy), f"{ring} heeft geen RingPolicy"

    def test_local_ring_has_all_maturity_levels(self):
        policy = RING_POLICIES[DeploymentRing.LOCAL]
        assert len(policy.allowed_maturity_levels) == 4

    def test_full_production_only_l4(self):
        policy = RING_POLICIES[DeploymentRing.FULL_PRODUCTION]
        assert policy.allowed_maturity_levels == [MaturityLevel.L4_BUSINESS_CRITICAL]

    def test_limited_production_max_traffic_10_percent(self):
        policy = RING_POLICIES[DeploymentRing.LIMITED_PRODUCTION]
        assert policy.max_traffic_percent == 10


# ─────────────────────────────────────────────
# get_ring_policy
# ─────────────────────────────────────────────

class TestGetRingPolicy:
    def test_returns_correct_policy(self):
        policy = get_ring_policy(DeploymentRing.AI_TEAM)
        assert policy.ring == DeploymentRing.AI_TEAM
        assert policy.name == "AI team"

    def test_local_ring_no_gates_required(self):
        policy = get_ring_policy(DeploymentRing.LOCAL)
        assert policy.requires_eval_pass is False
        assert policy.requires_policy_pass is False
        assert policy.requires_observability is False
        assert policy.requires_rollback_plan is False

    def test_full_production_all_gates_required(self):
        policy = get_ring_policy(DeploymentRing.FULL_PRODUCTION)
        assert policy.requires_eval_pass is True
        assert policy.requires_policy_pass is True
        assert policy.requires_observability is True
        assert policy.requires_rollback_plan is True


# ─────────────────────────────────────────────
# validate_ring_config
# ─────────────────────────────────────────────

class TestValidateRingConfig:
    def test_all_rings_have_valid_config(self, checker):
        for ring in DeploymentRing:
            assert checker.validate_ring_config(ring) is True, f"Ring {ring} heeft ongeldige config"


# ─────────────────────────────────────────────
# can_promote — succescases
# ─────────────────────────────────────────────

class TestCanPromoteSuccess:
    def test_local_to_ai_team_with_all_gates(self, checker, all_gates_pass):
        ok, reasons = checker.can_promote(
            "fraud-detection",
            DeploymentRing.LOCAL,
            DeploymentRing.AI_TEAM,
            all_gates_pass,
        )
        assert ok is True
        assert reasons == []

    def test_ai_team_to_internal_users(self, checker, all_gates_pass):
        ok, reasons = checker.can_promote(
            "fraud-detection",
            DeploymentRing.AI_TEAM,
            DeploymentRing.INTERNAL_USERS,
            all_gates_pass,
        )
        assert ok is True

    def test_internal_to_limited_production(self, checker, all_gates_pass):
        ok, reasons = checker.can_promote(
            "order-validation",
            DeploymentRing.INTERNAL_USERS,
            DeploymentRing.LIMITED_PRODUCTION,
            all_gates_pass,
        )
        assert ok is True

    def test_limited_to_full_production(self, checker, all_gates_pass):
        ok, reasons = checker.can_promote(
            "product-content",
            DeploymentRing.LIMITED_PRODUCTION,
            DeploymentRing.FULL_PRODUCTION,
            all_gates_pass,
        )
        assert ok is True


# ─────────────────────────────────────────────
# can_promote — blokkerende cases
# ─────────────────────────────────────────────

class TestCanPromoteBlocked:
    def test_ring_skip_is_blocked(self, checker, all_gates_pass):
        ok, reasons = checker.can_promote(
            "test-cap",
            DeploymentRing.LOCAL,
            DeploymentRing.INTERNAL_USERS,  # skip ring-1
            all_gates_pass,
        )
        assert ok is False
        assert len(reasons) > 0

    def test_evals_failed_blocks_promotion(self, checker):
        gates = {
            "evals_passed": False,
            "policy_passed": True,
            "observability_ok": True,
            "rollback_plan": True,
            "error_rate": 0.01,
        }
        ok, reasons = checker.can_promote(
            "fraud-detection",
            DeploymentRing.LOCAL,
            DeploymentRing.AI_TEAM,
            gates,
        )
        assert ok is False
        assert any("evaluaties" in r for r in reasons)

    def test_high_error_rate_blocks_promotion(self, checker):
        gates = {
            "evals_passed": True,
            "policy_passed": True,
            "observability_ok": True,
            "rollback_plan": True,
            "error_rate": 0.30,  # boven 20% drempel voor ring-1
        }
        ok, reasons = checker.can_promote(
            "fraud-detection",
            DeploymentRing.LOCAL,
            DeploymentRing.AI_TEAM,
            gates,
        )
        assert ok is False
        assert any("foutrate" in r.lower() for r in reasons)

    def test_missing_rollback_plan_blocks_limited_production(self, checker):
        gates = {
            "evals_passed": True,
            "policy_passed": True,
            "observability_ok": True,
            "rollback_plan": False,  # vereist voor ring-3
            "error_rate": 0.01,
        }
        ok, reasons = checker.can_promote(
            "order-validation",
            DeploymentRing.INTERNAL_USERS,
            DeploymentRing.LIMITED_PRODUCTION,
            gates,
        )
        assert ok is False
        assert any("rollback" in r.lower() for r in reasons)


# ─────────────────────────────────────────────
# get_promotion_requirements
# ─────────────────────────────────────────────

class TestGetPromotionRequirements:
    def test_requirements_for_ai_team(self, checker):
        reqs = checker.get_promotion_requirements(
            DeploymentRing.LOCAL, DeploymentRing.AI_TEAM
        )
        assert any("evals_passed" in r for r in reqs)
        assert any("policy_passed" in r for r in reqs)

    def test_requirements_for_full_production(self, checker):
        reqs = checker.get_promotion_requirements(
            DeploymentRing.LIMITED_PRODUCTION, DeploymentRing.FULL_PRODUCTION
        )
        assert any("rollback_plan" in r for r in reqs)
        assert any("observability_ok" in r for r in reqs)

    def test_invalid_ring_jump_returns_error_message(self, checker):
        reqs = checker.get_promotion_requirements(
            DeploymentRing.LOCAL, DeploymentRing.FULL_PRODUCTION
        )
        assert len(reqs) == 1
        assert "één stap" in reqs[0]
