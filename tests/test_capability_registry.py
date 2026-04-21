"""Tests voor ollama/capability_registry.py — minstens 20 tests."""
from __future__ import annotations

import pytest
from pathlib import Path

from ollama.capability_registry import (
    CapabilityDefinition,
    CapabilityMaturity,
    CapabilityOperational,
    CapabilityRelease,
    CapabilityRegistry,
    get_capability_registry,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _make_cap(
    name: str = "test-cap",
    lane: str = "advisory",
    level: str = "L3",
    human_approval: bool = False,
    ring: str = "ring-2",
    agents: list[str] | None = None,
    contract: str | None = None,
    chain: str | None = None,
) -> CapabilityDefinition:
    return CapabilityDefinition(
        name=name,
        version="1.0",
        description="Test capability",
        lane=lane,
        audience="internal",
        risk="medium",
        maturity=CapabilityMaturity(
            level=level,
            label="team-production",
            eval_required=True,
            human_approval_required=human_approval,
            min_first_pass_score=0.85,
        ),
        operational=CapabilityOperational(
            owner="team-test",
            sla_tier="gold",
            cost_budget_monthly_eur=100.0,
            preferred_model="llama3",
            escalation_model="llama3.1",
        ),
        release=CapabilityRelease(
            rollout_ring=ring,
            feature_flag=f"ai.capability.{name}",
        ),
        agents=agents or [],
        contract=contract,
        chain=chain,
    )


# ─────────────────────────────────────────────
# Registry instantiation
# ─────────────────────────────────────────────

def test_registry_instantiation_no_crash():
    registry = CapabilityRegistry()
    assert registry is not None


def test_registry_with_custom_dir(tmp_path):
    registry = CapabilityRegistry(capabilities_dir=tmp_path)
    assert registry.list_all() == []


def test_registry_list_all_empty_for_missing_dir(tmp_path):
    non_existent = tmp_path / "does_not_exist"
    registry = CapabilityRegistry(capabilities_dir=non_existent)
    assert registry.list_all() == []


# ─────────────────────────────────────────────
# register() + get()
# ─────────────────────────────────────────────

def test_register_and_get():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    cap = _make_cap("my-cap")
    registry.register(cap)
    result = registry.get("my-cap")
    assert result is not None
    assert result.name == "my-cap"


def test_register_overwrites_existing():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    cap_v1 = _make_cap("my-cap", level="L2")
    cap_v2 = _make_cap("my-cap", level="L3")
    registry.register(cap_v1)
    registry.register(cap_v2)
    assert registry.get("my-cap").maturity.level == "L3"


def test_get_nonexistent_returns_none():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    assert registry.get("nonexistent") is None


# ─────────────────────────────────────────────
# list_all()
# ─────────────────────────────────────────────

def test_list_all_contains_registered_names():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("cap-a"))
    registry.register(_make_cap("cap-b"))
    names = registry.list_all()
    assert "cap-a" in names
    assert "cap-b" in names


def test_list_all_returns_list_of_strings():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("my-cap"))
    result = registry.list_all()
    assert isinstance(result, list)
    assert all(isinstance(n, str) for n in result)


# ─────────────────────────────────────────────
# list_by_lane()
# ─────────────────────────────────────────────

def test_list_by_lane_advisory():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("fraud", lane="advisory"))
    registry.register(_make_cap("orders", lane="deterministic"))
    result = registry.list_by_lane("advisory")
    assert len(result) == 1
    assert result[0].name == "fraud"


def test_list_by_lane_returns_empty_for_unknown_lane():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("fraud", lane="advisory"))
    assert registry.list_by_lane("action") == []


def test_list_by_lane_multiple_results():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("cap-a", lane="generative"))
    registry.register(_make_cap("cap-b", lane="generative"))
    registry.register(_make_cap("cap-c", lane="advisory"))
    result = registry.list_by_lane("generative")
    assert len(result) == 2


# ─────────────────────────────────────────────
# list_production_ready()
# ─────────────────────────────────────────────

def test_list_production_ready_includes_l3():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("prod-cap", level="L3"))
    ready = registry.list_production_ready()
    assert any(c.name == "prod-cap" for c in ready)


def test_list_production_ready_includes_l4():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("biz-cap", level="L4"))
    ready = registry.list_production_ready()
    assert any(c.name == "biz-cap" for c in ready)


def test_list_production_ready_excludes_l1_l2():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("exp-cap", level="L1"))
    registry.register(_make_cap("beta-cap", level="L2"))
    ready = [c.name for c in registry.list_production_ready()]
    assert "exp-cap" not in ready
    assert "beta-cap" not in ready


# ─────────────────────────────────────────────
# get_by_agent()
# ─────────────────────────────────────────────

def test_get_by_agent_finds_correct_capability():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    cap = _make_cap("fraud-detection", agents=["fraud-advisor"])
    registry.register(cap)
    results = registry.get_by_agent("fraud-advisor")
    assert len(results) == 1
    assert results[0].name == "fraud-detection"


def test_get_by_agent_returns_empty_for_unknown_agent():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("my-cap", agents=["agent-a"]))
    assert registry.get_by_agent("agent-z") == []


def test_get_by_agent_multiple_capabilities():
    registry = CapabilityRegistry(capabilities_dir=Path("/nonexistent"))
    registry.register(_make_cap("cap-a", agents=["shared-agent"]))
    registry.register(_make_cap("cap-b", agents=["shared-agent"]))
    results = registry.get_by_agent("shared-agent")
    assert len(results) == 2


# ─────────────────────────────────────────────
# CapabilityDefinition helpers
# ─────────────────────────────────────────────

def test_is_production_ready_l1_false():
    cap = _make_cap(level="L1")
    assert cap.is_production_ready() is False


def test_is_production_ready_l2_false():
    cap = _make_cap(level="L2")
    assert cap.is_production_ready() is False


def test_is_production_ready_l3_true():
    cap = _make_cap(level="L3")
    assert cap.is_production_ready() is True


def test_is_production_ready_l4_true():
    cap = _make_cap(level="L4")
    assert cap.is_production_ready() is True


def test_requires_human_approval_true():
    cap = _make_cap(human_approval=True)
    assert cap.requires_human_approval() is True


def test_requires_human_approval_false():
    cap = _make_cap(human_approval=False)
    assert cap.requires_human_approval() is False


def test_get_ring_number_ring_2():
    cap = _make_cap(ring="ring-2")
    assert cap.get_ring_number() == 2


def test_get_ring_number_ring_0():
    cap = _make_cap(ring="ring-0")
    assert cap.get_ring_number() == 0


def test_get_ring_number_ring_4():
    cap = _make_cap(ring="ring-4")
    assert cap.get_ring_number() == 4


# ─────────────────────────────────────────────
# Dataclass field integrity
# ─────────────────────────────────────────────

def test_capability_maturity_fields():
    mat = CapabilityMaturity(
        level="L3",
        label="team-production",
        eval_required=True,
        human_approval_required=False,
        min_first_pass_score=0.85,
    )
    assert mat.level == "L3"
    assert mat.label == "team-production"
    assert mat.eval_required is True
    assert mat.human_approval_required is False
    assert mat.min_first_pass_score == 0.85


def test_capability_operational_fields():
    op = CapabilityOperational(
        owner="team-ai",
        sla_tier="gold",
        cost_budget_monthly_eur=100.0,
        preferred_model="llama3",
        escalation_model="llama3.1",
    )
    assert op.owner == "team-ai"
    assert op.sla_tier == "gold"
    assert op.cost_budget_monthly_eur == 100.0
    assert op.preferred_model == "llama3"
    assert op.escalation_model == "llama3.1"


def test_capability_release_fields():
    rel = CapabilityRelease(
        rollout_ring="ring-3",
        feature_flag="ai.capability.test.v1",
    )
    assert rel.rollout_ring == "ring-3"
    assert rel.feature_flag == "ai.capability.test.v1"


# ─────────────────────────────────────────────
# Contract and chain fields
# ─────────────────────────────────────────────

def test_capability_contract_and_chain():
    cap = _make_cap(contract="FraudContract", chain="prc-decision-support")
    assert cap.contract == "FraudContract"
    assert cap.chain == "prc-decision-support"


def test_capability_chain_none():
    cap = _make_cap(chain=None)
    assert cap.chain is None


# ─────────────────────────────────────────────
# Loads from YAML files (integration with real capabilities dir)
# ─────────────────────────────────────────────

def test_registry_loads_fraud_detection_from_yaml():
    registry = CapabilityRegistry()
    cap = registry.get("fraud-detection")
    assert cap is not None
    assert cap.lane == "advisory"
    assert cap.maturity.level == "L3"
    assert "fraud-advisor" in cap.agents


def test_registry_loads_order_validation_from_yaml():
    registry = CapabilityRegistry()
    cap = registry.get("order-validation")
    assert cap is not None
    assert cap.lane == "deterministic"
    assert cap.contract == "OrderAnalysisContract"


def test_registry_loads_audit_reporting_from_yaml():
    registry = CapabilityRegistry()
    cap = registry.get("audit-reporting")
    assert cap is not None
    assert cap.maturity.level == "L4"
    assert cap.maturity.eval_required is True
    assert cap.maturity.human_approval_required is True


def test_registry_loads_content_generation_from_yaml():
    registry = CapabilityRegistry()
    cap = registry.get("content-generation")
    assert cap is not None
    assert cap.lane == "generative"
    assert cap.maturity.level == "L2"


def test_registry_loads_customer_service_from_yaml():
    registry = CapabilityRegistry()
    cap = registry.get("customer-service")
    assert cap is not None
    assert "klantenservice-coach" in cap.agents


def test_registry_reload_clears_and_reloads():
    registry = CapabilityRegistry()
    registry.register(_make_cap("temp-cap"))
    assert registry.get("temp-cap") is not None
    registry.reload()
    # temp-cap was not in YAML files, so after reload it should be gone
    assert registry.get("temp-cap") is None


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

def test_get_capability_registry_singleton():
    r1 = get_capability_registry()
    r2 = get_capability_registry()
    assert r1 is r2
