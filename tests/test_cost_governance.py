"""
Tests voor CostGovernanceEngine — ollama/cost_governance.py

Dekt:
- get_policy() geeft default terug voor onbekende capability
- select_model() → cheap bij lage risk, premium bij risk >= 75
- select_model() → escalation_model bij force_escalation=True
- check_budget() → False als input tokens > max
- check_budget() → True als binnen budget
- check_budget() → False als maandbudget zou overschreden worden
- record_usage() + get_monthly_spend() correct
- get_cost_report() groepeert correct per capability
- would_exceed_budget() correct
- Multiple capabilities onafhankelijk getrackt
- ModelTier enum waarden
- CostPolicy dataclass
- UsageRecord dataclass
- Singleton get_cost_governance()
"""
from __future__ import annotations

import pytest

from ollama.cost_governance import (
    CostGovernanceEngine,
    CostPolicy,
    ModelTier,
    UsageRecord,
    get_cost_governance,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def engine() -> CostGovernanceEngine:
    """Verse engine per test — geen gedeelde state."""
    return CostGovernanceEngine()


# ─────────────────────────────────────────────
# 1. ModelTier enum
# ─────────────────────────────────────────────

def test_model_tier_cheap_value():
    assert ModelTier.CHEAP.value == "cheap"


def test_model_tier_standard_value():
    assert ModelTier.STANDARD.value == "standard"


def test_model_tier_premium_value():
    assert ModelTier.PREMIUM.value == "premium"


# ─────────────────────────────────────────────
# 2. CostPolicy.would_exceed_budget()
# ─────────────────────────────────────────────

def test_would_exceed_budget_over():
    policy = CostPolicy("test", 1000, 500, ModelTier.CHEAP, ModelTier.STANDARD, 2, 10.0)
    assert policy.would_exceed_budget(9.5, 1.0) is True


def test_would_exceed_budget_exactly_at_limit():
    policy = CostPolicy("test", 1000, 500, ModelTier.CHEAP, ModelTier.STANDARD, 2, 10.0)
    # 10.0 + 0.0 = 10.0 — niet boven budget
    assert policy.would_exceed_budget(10.0, 0.0) is False


def test_would_exceed_budget_within():
    policy = CostPolicy("test", 1000, 500, ModelTier.CHEAP, ModelTier.STANDARD, 2, 10.0)
    assert policy.would_exceed_budget(3.0, 2.0) is False


def test_would_exceed_budget_zero_spend():
    policy = CostPolicy("test", 1000, 500, ModelTier.CHEAP, ModelTier.STANDARD, 2, 10.0)
    assert policy.would_exceed_budget(0.0, 5.0) is False


# ─────────────────────────────────────────────
# 3. get_policy()
# ─────────────────────────────────────────────

def test_get_policy_known_fraud(engine):
    policy = engine.get_policy("fraud-detection")
    assert policy.capability == "fraud-detection"
    assert policy.max_input_tokens == 8000
    assert policy.preferred_model == ModelTier.CHEAP
    assert policy.escalation_model == ModelTier.PREMIUM


def test_get_policy_known_order_validation(engine):
    policy = engine.get_policy("order-validation")
    assert policy.capability == "order-validation"
    assert policy.max_input_tokens == 4000
    assert policy.monthly_budget_eur == 50.0


def test_get_policy_known_content_generation(engine):
    policy = engine.get_policy("content-generation")
    assert policy.preferred_model == ModelTier.STANDARD
    assert policy.max_output_tokens == 2000


def test_get_policy_known_risk_classification(engine):
    policy = engine.get_policy("risk-classification")
    assert policy.escalation_model == ModelTier.CHEAP
    assert policy.monthly_budget_eur == 30.0


def test_get_policy_unknown_returns_default(engine):
    policy = engine.get_policy("unknown-capability")
    assert policy.capability == "default"
    assert policy.max_input_tokens == 4000


def test_get_policy_default_explicitly(engine):
    policy = engine.get_policy("default")
    assert policy.monthly_budget_eur == 75.0


# ─────────────────────────────────────────────
# 4. select_model()
# ─────────────────────────────────────────────

def test_select_model_cheap_low_risk(engine):
    model = engine.select_model("fraud-detection", risk_score=0)
    assert model == "llama3"


def test_select_model_cheap_risk_74(engine):
    model = engine.select_model("fraud-detection", risk_score=74)
    assert model == "llama3"


def test_select_model_premium_at_risk_75(engine):
    model = engine.select_model("fraud-detection", risk_score=75)
    assert model == "llama3.1:70b"


def test_select_model_premium_high_risk(engine):
    model = engine.select_model("fraud-detection", risk_score=95)
    assert model == "llama3.1:70b"


def test_select_model_force_escalation(engine):
    model = engine.select_model("fraud-detection", risk_score=0, force_escalation=True)
    assert model == "llama3.1:70b"


def test_select_model_content_gen_standard_preferred(engine):
    model = engine.select_model("content-generation", risk_score=0)
    assert model == "llama3.1"


def test_select_model_content_gen_premium_escalation(engine):
    model = engine.select_model("content-generation", risk_score=80)
    assert model == "llama3.1:70b"


def test_select_model_unknown_capability_defaults_cheap(engine):
    model = engine.select_model("unknown-cap", risk_score=0)
    assert model == "llama3"


def test_select_model_unknown_capability_force_escalation(engine):
    model = engine.select_model("unknown-cap", force_escalation=True)
    assert model == "llama3.1"


# ─────────────────────────────────────────────
# 5. check_budget()
# ─────────────────────────────────────────────

def test_check_budget_allowed_within_tokens(engine):
    allowed, reason = engine.check_budget("fraud-detection", 1000)
    assert allowed is True
    assert reason == "OK"


def test_check_budget_blocked_exceeds_max_tokens(engine):
    allowed, reason = engine.check_budget("fraud-detection", 9000)
    assert allowed is False
    assert "8000" in reason


def test_check_budget_blocked_at_max_plus_one(engine):
    allowed, reason = engine.check_budget("order-validation", 4001)
    assert allowed is False


def test_check_budget_allowed_at_exact_max(engine):
    allowed, reason = engine.check_budget("order-validation", 4000)
    assert allowed is True


def test_check_budget_blocked_by_monthly_budget(engine):
    # Registreer genoeg tokens zodat de maandelijkse spend net boven het budget uitkomt.
    # record_usage heeft geen token-limiet — enkel check_budget controleert dat.
    # order-validation budget = 50.0 EUR; 25_000_000 tokens × 0.000002 = 50.0 EUR spend.
    engine.record_usage("order-validation", "llama3", 25_000_000, 0, 0)
    # Volgende aanvraag (1000 tokens = 0.002 EUR): 50.0 + 0.002 > 50.0 → geblokkeerd.
    allowed, reason = engine.check_budget("order-validation", 1000)
    assert allowed is False
    assert "budget" in reason.lower()


def test_check_budget_unknown_capability_uses_default(engine):
    allowed, reason = engine.check_budget("unknown-cap", 1000)
    assert allowed is True


# ─────────────────────────────────────────────
# 6. record_usage() + get_monthly_spend()
# ─────────────────────────────────────────────

def test_record_usage_increases_monthly_spend(engine):
    engine.record_usage("fraud-detection", "llama3", 1000, 200, 1)
    spend = engine.get_monthly_spend("fraud-detection")
    expected = (1000 + 200) * 0.000002
    assert abs(spend - expected) < 1e-10


def test_record_multiple_usages_cumulates(engine):
    engine.record_usage("fraud-detection", "llama3", 1000, 0, 1)
    engine.record_usage("fraud-detection", "llama3", 2000, 0, 1)
    spend = engine.get_monthly_spend("fraud-detection")
    expected = (1000 + 2000) * 0.000002
    assert abs(spend - expected) < 1e-10


def test_get_monthly_spend_zero_for_new_capability(engine):
    assert engine.get_monthly_spend("brand-new-cap") == 0.0


def test_record_usage_stores_timestamp(engine):
    engine.record_usage("test-cap", "llama3", 100, 50, 0)
    records = engine.get_all_usage()
    assert len(records) == 1
    assert records[0].timestamp != ""


def test_record_usage_stores_correct_fields(engine):
    engine.record_usage("order-validation", "llama3.1", 500, 100, 2)
    records = engine.get_all_usage()
    r = records[0]
    assert r.capability == "order-validation"
    assert r.model == "llama3.1"
    assert r.input_tokens == 500
    assert r.output_tokens == 100
    assert r.tool_calls == 2


# ─────────────────────────────────────────────
# 7. get_cost_report()
# ─────────────────────────────────────────────

def test_cost_report_groups_by_capability(engine):
    engine.record_usage("fraud-detection", "llama3", 1000, 200, 1)
    engine.record_usage("order-validation", "llama3", 500, 100, 1)
    report = engine.get_cost_report()
    assert "fraud-detection" in report
    assert "order-validation" in report


def test_cost_report_call_count(engine):
    engine.record_usage("fraud-detection", "llama3", 1000, 0, 1)
    engine.record_usage("fraud-detection", "llama3", 2000, 0, 1)
    report = engine.get_cost_report()
    assert report["fraud-detection"]["calls"] == 2


def test_cost_report_token_sum(engine):
    engine.record_usage("order-validation", "llama3", 300, 100, 0)
    engine.record_usage("order-validation", "llama3", 200, 50, 0)
    report = engine.get_cost_report()
    assert report["order-validation"]["tokens"] == 650


def test_cost_report_total_eur(engine):
    engine.record_usage("content-generation", "llama3.1", 1000, 500, 0)
    report = engine.get_cost_report()
    expected = (1000 + 500) * 0.000002
    assert abs(report["content-generation"]["total_eur"] - expected) < 1e-10


def test_cost_report_empty_when_no_usage(engine):
    report = engine.get_cost_report()
    assert report == {}


def test_cost_report_capabilities_independent(engine):
    engine.record_usage("cap-a", "llama3", 1000, 0, 0)
    engine.record_usage("cap-b", "llama3", 2000, 0, 0)
    report = engine.get_cost_report()
    assert report["cap-a"]["tokens"] == 1000
    assert report["cap-b"]["tokens"] == 2000


# ─────────────────────────────────────────────
# 8. reset_usage()
# ─────────────────────────────────────────────

def test_reset_usage_clears_all_records(engine):
    engine.record_usage("fraud-detection", "llama3", 1000, 0, 1)
    engine.reset_usage()
    assert engine.get_monthly_spend("fraud-detection") == 0.0
    assert engine.get_all_usage() == []


# ─────────────────────────────────────────────
# 9. Multiple capabilities onafhankelijk
# ─────────────────────────────────────────────

def test_multiple_capabilities_independent_spend(engine):
    engine.record_usage("fraud-detection", "llama3", 5000, 0, 0)
    engine.record_usage("order-validation", "llama3", 1000, 0, 0)
    fd_spend = engine.get_monthly_spend("fraud-detection")
    ov_spend = engine.get_monthly_spend("order-validation")
    assert fd_spend > ov_spend
    assert abs(fd_spend - 5000 * 0.000002) < 1e-10
    assert abs(ov_spend - 1000 * 0.000002) < 1e-10


def test_all_known_capabilities_have_policy(engine):
    capabilities = [
        "fraud-detection",
        "order-validation",
        "content-generation",
        "risk-classification",
    ]
    for cap in capabilities:
        policy = engine.get_policy(cap)
        assert policy.capability == cap


# ─────────────────────────────────────────────
# 10. Singleton
# ─────────────────────────────────────────────

def test_get_cost_governance_returns_engine():
    engine = get_cost_governance()
    assert isinstance(engine, CostGovernanceEngine)


def test_get_cost_governance_is_singleton():
    e1 = get_cost_governance()
    e2 = get_cost_governance()
    assert e1 is e2
