"""
Tests for ollama/agent_groups.py — Agent Group Taxonomy.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from ollama.agent_groups import (
    AgentGroup,
    AgentGroupDefinition,
    AGENT_GROUP_REGISTRY,
    get_groups_for_agent,
    get_group_for_skill,
    get_agents_for_lane,
    get_group_definition,
    list_all_agents,
)

VALID_LANES = {"deterministic", "advisory", "generative", "action"}


# --- AgentGroup enum ---

def test_enum_has_six_values():
    assert len(AgentGroup) == 6


def test_enum_dev_intelligence():
    assert AgentGroup.DEV_INTELLIGENCE.value == "dev-intelligence"


def test_enum_test_intelligence():
    assert AgentGroup.TEST_INTELLIGENCE.value == "test-intelligence"


def test_enum_ecommerce_validation():
    assert AgentGroup.ECOMMERCE_VALIDATION.value == "ecommerce-validation"


def test_enum_risk_decision():
    assert AgentGroup.RISK_DECISION.value == "risk-decision"


def test_enum_explanation():
    assert AgentGroup.EXPLANATION.value == "explanation"


def test_enum_audit():
    assert AgentGroup.AUDIT.value == "audit"


# --- AGENT_GROUP_REGISTRY ---

def test_registry_has_six_groups():
    assert len(AGENT_GROUP_REGISTRY) == 6


def test_registry_contains_all_enum_values():
    for group in AgentGroup:
        assert group in AGENT_GROUP_REGISTRY


# --- get_group_definition ---

def test_get_group_definition_returns_correct_label():
    defn = get_group_definition(AgentGroup.DEV_INTELLIGENCE)
    assert defn.label == "DEV Intelligence"


def test_get_group_definition_returns_correct_group():
    defn = get_group_definition(AgentGroup.AUDIT)
    assert defn.group == AgentGroup.AUDIT


# --- contains_agent ---

def test_contains_agent_true():
    defn = get_group_definition(AgentGroup.DEV_INTELLIGENCE)
    assert defn.contains_agent("ai-architect") is True


def test_contains_agent_false():
    defn = get_group_definition(AgentGroup.DEV_INTELLIGENCE)
    assert defn.contains_agent("nonexistent") is False


def test_contains_agent_audit_reporter():
    defn = get_group_definition(AgentGroup.AUDIT)
    assert defn.contains_agent("audit-reporter") is True


# --- contains_skill ---

def test_contains_skill_true():
    defn = get_group_definition(AgentGroup.DEV_INTELLIGENCE)
    assert defn.contains_skill("analyze_code_changes") is True


def test_contains_skill_false():
    defn = get_group_definition(AgentGroup.DEV_INTELLIGENCE)
    assert defn.contains_skill("nonexistent_skill") is False


# --- get_groups_for_agent ---

def test_fraud_advisor_dual_role():
    groups = get_groups_for_agent("fraud-advisor")
    assert AgentGroup.ECOMMERCE_VALIDATION in groups
    assert AgentGroup.RISK_DECISION in groups


def test_audit_reporter_single_group():
    groups = get_groups_for_agent("audit-reporter")
    assert groups == [AgentGroup.AUDIT]


def test_nonexistent_agent_returns_empty():
    assert get_groups_for_agent("nonexistent-agent") == []


def test_lead_orchestrator_in_risk_decision():
    groups = get_groups_for_agent("lead-orchestrator")
    assert AgentGroup.RISK_DECISION in groups


# --- get_group_for_skill ---

def test_skill_audit_trace_generator():
    assert get_group_for_skill("audit_trace_generator") == AgentGroup.AUDIT


def test_skill_nonexistent_returns_none():
    assert get_group_for_skill("nonexistent_skill") is None


def test_skill_validate_acceptance_criteria():
    assert get_group_for_skill("validate_acceptance_criteria") == AgentGroup.TEST_INTELLIGENCE


def test_skill_classify_payroll_risk():
    assert get_group_for_skill("classify_payroll_risk") == AgentGroup.RISK_DECISION


# --- get_agents_for_lane ---

def test_advisory_lane_contains_ai_architect():
    assert "ai-architect" in get_agents_for_lane("advisory")


def test_generative_lane_contains_product_writer():
    assert "product-writer" in get_agents_for_lane("generative")


def test_nonexistent_lane_returns_empty():
    assert get_agents_for_lane("nonexistent") == []


def test_deterministic_lane_contains_test_orchestrator():
    assert "test-orchestrator" in get_agents_for_lane("deterministic")


# --- list_all_agents ---

def test_list_all_agents_contains_known_agents():
    agents = list_all_agents()
    for expected in ["ai-architect", "fraud-advisor", "audit-reporter", "product-writer", "db-explorer"]:
        assert expected in agents


def test_list_all_agents_no_duplicates():
    agents = list_all_agents()
    assert len(agents) == len(set(agents))


# --- structural integrity per group ---

def test_all_groups_have_nonempty_agents():
    for group, defn in AGENT_GROUP_REGISTRY.items():
        assert len(defn.agents) > 0, f"{group} has no agents"


def test_all_groups_have_nonempty_skills():
    for group, defn in AGENT_GROUP_REGISTRY.items():
        assert len(defn.skills) > 0, f"{group} has no skills"


def test_all_groups_have_valid_lane():
    for group, defn in AGENT_GROUP_REGISTRY.items():
        assert defn.lane in VALID_LANES, f"{group} has invalid lane '{defn.lane}'"
