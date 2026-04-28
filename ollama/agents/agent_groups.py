"""
Agent Group Taxonomy — organiseert de agent fleet in 6 functionele groepen.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AgentGroup(Enum):
    DEV_INTELLIGENCE = "dev-intelligence"
    TEST_INTELLIGENCE = "test-intelligence"
    ECOMMERCE_VALIDATION = "ecommerce-validation"
    RISK_DECISION = "risk-decision"
    EXPLANATION = "explanation"
    AUDIT = "audit"


@dataclass
class AgentGroupDefinition:
    group: AgentGroup
    label: str
    goal: str
    agents: list[str]
    skills: list[str]
    lane: str        # deterministic | advisory | generative | action

    def contains_agent(self, agent_name: str) -> bool:
        return agent_name in self.agents

    def contains_skill(self, skill_name: str) -> bool:
        return skill_name in self.skills


# Registry van alle 6 groepen
AGENT_GROUP_REGISTRY: dict[AgentGroup, AgentGroupDefinition] = {
    AgentGroup.DEV_INTELLIGENCE: AgentGroupDefinition(
        group=AgentGroup.DEV_INTELLIGENCE,
        label="DEV Intelligence",
        goal="Begrijpen wat er verandert in de codebase",
        agents=["ai-architect", "feature-worker", "fastapi-developer", "nextjs-developer", "ollama-agent-designer"],
        skills=["analyze_code_changes", "map_changes_to_business_logic", "detect_regression_scope", "explain_code_to_non_dev"],
        lane="advisory",
    ),
    AgentGroup.TEST_INTELLIGENCE: AgentGroupDefinition(
        group=AgentGroup.TEST_INTELLIGENCE,
        label="Test Intelligence",
        goal="Testen verbeteren en versnellen",
        agents=["test-orchestrator", "ci-debugger"],
        skills=["validate_acceptance_criteria", "generate_advanced_test_cases", "detect_regression_risk", "generate_test_documentation"],
        lane="deterministic",
    ),
    AgentGroup.ECOMMERCE_VALIDATION: AgentGroupDefinition(
        group=AgentGroup.ECOMMERCE_VALIDATION,
        label="E-Commerce Validation",
        goal="Output controleren en valideren",
        agents=["order-analyst", "fraud-advisor"],
        skills=["compare_with_previous_run", "detect_salary_anomalies", "validate_legal_rules", "detect_missing_mutations"],
        lane="deterministic",
    ),
    AgentGroup.RISK_DECISION: AgentGroupDefinition(
        group=AgentGroup.RISK_DECISION,
        label="Risk & Decision",
        goal="Prioritiseren en beslissen",
        agents=["fraud-advisor", "lead-orchestrator"],
        skills=["classify_payroll_risk", "assess_release_risk", "suggest_prc_actions"],
        lane="advisory",
    ),
    AgentGroup.EXPLANATION: AgentGroupDefinition(
        group=AgentGroup.EXPLANATION,
        label="Explanation",
        goal="Vertrouwen en begrijpbaarheid voor klant en merchant",
        agents=["klantenservice-coach", "product-writer", "mr-reviewer"],
        skills=["explain_salary_difference", "explain_code_to_non_dev"],
        lane="generative",
    ),
    AgentGroup.AUDIT: AgentGroupDefinition(
        group=AgentGroup.AUDIT,
        label="Audit",
        goal="Compliance, GDPR en traceability",
        agents=["audit-reporter", "gdpr-advisor", "db-explorer"],
        skills=["audit_trace_generator", "decision_logging"],
        lane="deterministic",
    ),
}


def get_groups_for_agent(agent_name: str) -> list[AgentGroup]:
    """Returns all groups an agent belongs to (agents can be in multiple groups)."""
    return [
        group for group, definition in AGENT_GROUP_REGISTRY.items()
        if definition.contains_agent(agent_name)
    ]


def get_group_for_skill(skill_name: str) -> Optional[AgentGroup]:
    """Returns the primary group for a skill."""
    for group, definition in AGENT_GROUP_REGISTRY.items():
        if definition.contains_skill(skill_name):
            return group
    return None


def get_agents_for_lane(lane: str) -> list[str]:
    """Returns all agents in groups with the given lane."""
    agents = []
    for definition in AGENT_GROUP_REGISTRY.values():
        if definition.lane == lane:
            agents.extend(definition.agents)
    return list(set(agents))


def get_group_definition(group: AgentGroup) -> AgentGroupDefinition:
    return AGENT_GROUP_REGISTRY[group]


def list_all_agents() -> list[str]:
    """Returns all unique agent names across all groups."""
    all_agents = []
    for definition in AGENT_GROUP_REGISTRY.values():
        all_agents.extend(definition.agents)
    return list(set(all_agents))
