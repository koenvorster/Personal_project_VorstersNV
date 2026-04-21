"""Tests voor ollama/maturity_engine.py — minstens 20 tests."""
from __future__ import annotations

import pytest

from ollama.maturity_engine import (
    MATURITY_ENV_RULES,
    MATURITY_LABELS,
    MaturityCheckResult,
    MaturityEngine,
    get_maturity_engine,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def engine() -> MaturityEngine:
    return MaturityEngine()


# ─────────────────────────────────────────────
# L1 — experimental: alleen dev
# ─────────────────────────────────────────────

def test_l1_allowed_in_dev(engine):
    result = engine.check("my-cap", "L1", "dev")
    assert result.allowed is True


def test_l1_blocked_in_test(engine):
    result = engine.check("my-cap", "L1", "test")
    assert result.allowed is False


def test_l1_blocked_in_staging(engine):
    result = engine.check("my-cap", "L1", "staging")
    assert result.allowed is False


def test_l1_blocked_in_prod(engine):
    result = engine.check("my-cap", "L1", "prod")
    assert result.allowed is False


# ─────────────────────────────────────────────
# L2 — internal-beta: dev + test
# ─────────────────────────────────────────────

def test_l2_allowed_in_dev(engine):
    result = engine.check("my-cap", "L2", "dev")
    assert result.allowed is True


def test_l2_allowed_in_test(engine):
    result = engine.check("my-cap", "L2", "test")
    assert result.allowed is True


def test_l2_blocked_in_staging(engine):
    result = engine.check("my-cap", "L2", "staging")
    assert result.allowed is False


def test_l2_blocked_in_prod(engine):
    result = engine.check("my-cap", "L2", "prod")
    assert result.allowed is False


# ─────────────────────────────────────────────
# L3 — team-production: dev + test + staging
# ─────────────────────────────────────────────

def test_l3_allowed_in_dev(engine):
    result = engine.check("my-cap", "L3", "dev")
    assert result.allowed is True


def test_l3_allowed_in_test(engine):
    result = engine.check("my-cap", "L3", "test")
    assert result.allowed is True


def test_l3_allowed_in_staging(engine):
    result = engine.check("my-cap", "L3", "staging")
    assert result.allowed is True


def test_l3_blocked_in_prod(engine):
    result = engine.check("my-cap", "L3", "prod")
    assert result.allowed is False


# ─────────────────────────────────────────────
# L4 — business-critical: overal
# ─────────────────────────────────────────────

def test_l4_allowed_in_dev(engine):
    result = engine.check("my-cap", "L4", "dev")
    assert result.allowed is True


def test_l4_allowed_in_test(engine):
    result = engine.check("my-cap", "L4", "test")
    assert result.allowed is True


def test_l4_allowed_in_staging(engine):
    result = engine.check("my-cap", "L4", "staging")
    assert result.allowed is True


def test_l4_in_prod_without_eval_blocked(engine):
    result = engine.check("my-cap", "L4", "prod", eval_completed=False, human_approved=False)
    assert result.allowed is False
    assert result.requires_eval is True


def test_l4_in_prod_with_eval_but_no_human_approval_blocked(engine):
    result = engine.check("my-cap", "L4", "prod", eval_completed=True, human_approved=False)
    assert result.allowed is False
    assert result.requires_human_approval is True
    assert result.requires_eval is False


def test_l4_in_prod_with_eval_and_human_approval_allowed(engine):
    result = engine.check("my-cap", "L4", "prod", eval_completed=True, human_approved=True)
    assert result.allowed is True


# ─────────────────────────────────────────────
# MaturityCheckResult fields
# ─────────────────────────────────────────────

def test_check_result_contains_capability_name(engine):
    result = engine.check("fraud-detection", "L3", "staging")
    assert result.capability == "fraud-detection"


def test_check_result_contains_maturity_level(engine):
    result = engine.check("fraud-detection", "L3", "staging")
    assert result.maturity_level == "L3"


def test_check_result_contains_environment(engine):
    result = engine.check("fraud-detection", "L3", "staging")
    assert result.environment == "staging"


def test_check_result_has_reason(engine):
    result = engine.check("my-cap", "L1", "prod")
    assert isinstance(result.reason, str)
    assert len(result.reason) > 0


def test_check_blocked_reason_includes_allowed_envs(engine):
    result = engine.check("my-cap", "L1", "prod")
    assert "dev" in result.reason


# ─────────────────────────────────────────────
# get_allowed_environments()
# ─────────────────────────────────────────────

def test_get_allowed_environments_l1(engine):
    assert engine.get_allowed_environments("L1") == ["dev"]


def test_get_allowed_environments_l2(engine):
    assert engine.get_allowed_environments("L2") == ["dev", "test"]


def test_get_allowed_environments_l3(engine):
    assert engine.get_allowed_environments("L3") == ["dev", "test", "staging"]


def test_get_allowed_environments_l4(engine):
    assert engine.get_allowed_environments("L4") == ["dev", "test", "staging", "prod"]


def test_get_allowed_environments_unknown(engine):
    # Unknown levels fall back to dev only
    result = engine.get_allowed_environments("L99")
    assert result == ["dev"]


# ─────────────────────────────────────────────
# get_label()
# ─────────────────────────────────────────────

def test_get_label_l1(engine):
    assert engine.get_label("L1") == "experimental"


def test_get_label_l2(engine):
    assert engine.get_label("L2") == "internal-beta"


def test_get_label_l3(engine):
    assert engine.get_label("L3") == "team-production"


def test_get_label_l4(engine):
    assert engine.get_label("L4") == "business-critical"


def test_get_label_unknown(engine):
    assert engine.get_label("L99") == "unknown"


# ─────────────────────────────────────────────
# can_promote()
# ─────────────────────────────────────────────

def test_can_promote_l1_to_l2(engine):
    ok, msg = engine.can_promote("L1", "L2")
    assert ok is True
    assert "L1" in msg or "L2" in msg


def test_can_promote_l2_to_l3(engine):
    ok, _ = engine.can_promote("L2", "L3")
    assert ok is True


def test_can_promote_l3_to_l4(engine):
    ok, _ = engine.can_promote("L3", "L4")
    assert ok is True


def test_cannot_promote_l1_to_l3_skip(engine):
    ok, msg = engine.can_promote("L1", "L3")
    assert ok is False
    assert "one level" in msg


def test_cannot_promote_l1_to_l4_skip(engine):
    ok, _ = engine.can_promote("L1", "L4")
    assert ok is False


def test_cannot_promote_downgrade(engine):
    ok, msg = engine.can_promote("L3", "L2")
    assert ok is False


def test_cannot_promote_invalid_current(engine):
    ok, msg = engine.can_promote("L5", "L6")
    assert ok is False
    assert "Invalid" in msg


def test_cannot_promote_l4_beyond(engine):
    ok, msg = engine.can_promote("L4", "L5")
    assert ok is False


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

def test_get_maturity_engine_singleton():
    e1 = get_maturity_engine()
    e2 = get_maturity_engine()
    assert e1 is e2


def test_get_maturity_engine_is_maturity_engine():
    engine = get_maturity_engine()
    assert isinstance(engine, MaturityEngine)


# ─────────────────────────────────────────────
# Constants integrity
# ─────────────────────────────────────────────

def test_maturity_env_rules_all_levels_present():
    for level in ("L1", "L2", "L3", "L4"):
        assert level in MATURITY_ENV_RULES


def test_maturity_labels_all_levels_present():
    for level in ("L1", "L2", "L3", "L4"):
        assert level in MATURITY_LABELS


def test_l4_allows_prod_in_env_rules():
    assert "prod" in MATURITY_ENV_RULES["L4"]


def test_l1_does_not_allow_prod_in_env_rules():
    assert "prod" not in MATURITY_ENV_RULES["L1"]
