"""
VorstersNV AI Control Plane
Centraal beslissingsmechanisme voor capability routing, policy enforcement,
model selectie, budget controle en HITL-beslissingen.

Revisie 4 architectuur — CONTROL PLANE laag.

Gebruik:
    from ollama.control_plane import ControlPlane, ExecutionContext

    cp = ControlPlane()
    context = ExecutionContext(
        event_type=EventType.ORDER_CREATED,
        environment="prod",
        risk_score=80,
    )
    path = cp.select_execution_path("fraud-detection", context)
    cp.enforce_policy("fraud-detection", context)  # raises PolicyViolationError
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ollama.events import EventType

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Enums & Constants
# ─────────────────────────────────────────────

class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    TEST = "test"
    STAGING = "staging"
    PROD = "prod"


class WorkflowLane(str, Enum):
    """4 workflow lanes — elke capability hoort in precies 1 lane."""
    DETERMINISTIC = "deterministic"   # schema validatie, contract mapping
    ADVISORY = "advisory"             # impact analyse, fraude detectie
    GENERATIVE = "generative"         # content, e-mails, beschrijvingen
    ACTION = "action"                 # tool calls, order blokkeren


class MaturityLevel(str, Enum):
    L1_EXPERIMENTAL = "L1"
    L2_INTERNAL_BETA = "L2"
    L3_TEAM_PRODUCTION = "L3"
    L4_BUSINESS_CRITICAL = "L4"


class DeploymentRing(int, Enum):
    LOCAL = 0
    AI_TEAM = 1
    INTERNAL_USERS = 2
    LIMITED_PRODUCTION = 3
    FULL_PRODUCTION = 4


# ─────────────────────────────────────────────
# Execution Context
# ─────────────────────────────────────────────

@dataclass
class ExecutionContext:
    """
    Alle dimensies die de control plane gebruikt voor routing.
    8 routing dimensies conform Revisie 4 architectuur.
    """
    # Dimensie 1: event type
    event_type: EventType = EventType.ORDER_CREATED

    # Dimensie 2: omgeving
    environment: Environment = Environment.LOCAL

    # Dimensie 3: risico
    risk_score: int = 0           # 0-100

    # Dimensie 4: cost budget
    remaining_budget_eur: float = 100.0

    # Dimensie 5: latency budget (ms)
    max_latency_ms: int = 5000

    # Dimensie 6: capability maturity
    maturity_level: MaturityLevel = MaturityLevel.L1_EXPERIMENTAL

    # Dimensie 7: beschikbare modellen
    available_models: list[str] = field(default_factory=lambda: ["llama3", "mistral"])

    # Dimensie 8: tenant / gebruiker context
    tenant_id: str = ""
    user_id: str = ""
    trace_id: str = ""

    # Extra context
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PROD

    @property
    def risk_level(self) -> str:
        if self.risk_score < 40:
            return "LOW"
        if self.risk_score < 75:
            return "MEDIUM"
        if self.risk_score < 90:
            return "HIGH"
        return "CRITICAL"


# ─────────────────────────────────────────────
# Execution Path
# ─────────────────────────────────────────────

@dataclass
class ExecutionPath:
    """Resultaat van control plane routing — wat uitvoeren en hoe."""
    capability: str
    lane: WorkflowLane
    primary_model: str
    fallback_model: str | None
    max_tokens_input: int
    max_tokens_output: int
    max_tool_calls: int
    chain_name: str
    requires_hitl: bool
    deployment_ring: DeploymentRing
    selection_reason: str


# ─────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────

class PolicyViolationError(Exception):
    """Raised wanneer een policy regel geschonden wordt."""
    def __init__(self, rule_id: str, message: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"[{rule_id}] {message}")


# ─────────────────────────────────────────────
# Capability Registry
# ─────────────────────────────────────────────

# Capability → lane mapping
_CAPABILITY_LANES: dict[str, WorkflowLane] = {
    "order-validation":    WorkflowLane.DETERMINISTIC,
    "schema-validation":   WorkflowLane.DETERMINISTIC,
    "contract-mapping":    WorkflowLane.DETERMINISTIC,
    "fraud-detection":     WorkflowLane.ADVISORY,
    "risk-classification": WorkflowLane.ADVISORY,
    "architecture-review": WorkflowLane.ADVISORY,
    "regression-analysis": WorkflowLane.ADVISORY,
    "product-content":     WorkflowLane.GENERATIVE,
    "email-generation":    WorkflowLane.GENERATIVE,
    "customer-service":    WorkflowLane.GENERATIVE,
    "order-blocking":      WorkflowLane.ACTION,
    "account-management":  WorkflowLane.ACTION,
    "payment-retry":       WorkflowLane.ACTION,
    "inventory-reorder":   WorkflowLane.ACTION,
}

# Capability → model preferences (goedkoop eerst, duur bij escalatie)
_CAPABILITY_MODELS: dict[str, dict[str, str]] = {
    "fraud-detection":     {"preferred": "llama3", "escalation": "mistral"},
    "order-validation":    {"preferred": "llama3", "escalation": "llama3"},
    "product-content":     {"preferred": "mistral", "escalation": "mistral"},
    "customer-service":    {"preferred": "mistral", "escalation": "mistral"},
    "architecture-review": {"preferred": "codellama", "escalation": "codellama"},
    "risk-classification": {"preferred": "llama3", "escalation": "mistral"},
    "regression-analysis": {"preferred": "codellama", "escalation": "codellama"},
}
_DEFAULT_MODELS = {"preferred": "llama3", "escalation": "mistral"}

# Capability → token budgets
_CAPABILITY_TOKENS: dict[str, dict[str, int]] = {
    "fraud-detection":     {"max_input": 8000,  "max_output": 1000, "max_tools": 3},
    "order-validation":    {"max_input": 4000,  "max_output": 500,  "max_tools": 2},
    "product-content":     {"max_input": 6000,  "max_output": 2000, "max_tools": 1},
    "customer-service":    {"max_input": 8000,  "max_output": 1500, "max_tools": 2},
    "architecture-review": {"max_input": 12000, "max_output": 3000, "max_tools": 0},
}
_DEFAULT_TOKENS = {"max_input": 8000, "max_output": 1000, "max_tools": 3}

# Event type → capability chain mapping
_EVENT_TO_CHAIN: dict[EventType, tuple[str, str]] = {
    EventType.ORDER_CREATED:    ("order-validation",    "ORDER_VALIDATION"),
    EventType.PAYMENT_FAILED:   ("payment-retry",       "PAYMENT_RECOVERY"),
    EventType.FRAUD_DETECTED:   ("risk-classification", "FRAUD_EXPLANATION"),
    EventType.INVENTORY_LOW:    ("inventory-reorder",   "REORDER_NOTIFICATION"),
    EventType.CODE_RELEASED:    ("regression-analysis", "DEV_INTELLIGENCE"),
    EventType.ANOMALY_DETECTED: ("risk-classification", "ANOMALY_ACTION"),
    EventType.HITL_REQUIRED:    ("order-blocking",      "HITL_ESCALATION"),
}


# ─────────────────────────────────────────────
# Control Plane
# ─────────────────────────────────────────────

class ControlPlane:
    """
    AI Control Plane — centraal routings- en governance-mechanisme.

    Beslist op basis van 8 dimensies:
      1. event_type
      2. environment
      3. risk_score
      4. remaining_budget_eur
      5. max_latency_ms
      6. maturity_level
      7. available_models
      8. policy_rules (intern)
    """

    def select_capability(self, event_type: EventType) -> str:
        """
        Kies de capability die hoort bij dit event type.

        Returns:
            capability naam (str)
        """
        if event_type in _EVENT_TO_CHAIN:
            capability, _ = _EVENT_TO_CHAIN[event_type]
            logger.debug("Event %s → capability %s", event_type.value, capability)
            return capability

        # Fallback: advisory voor onbekende events
        logger.warning("Onbekend event type %s — fallback naar risk-classification", event_type.value)
        return "risk-classification"

    def select_execution_path(
        self,
        capability: str,
        context: ExecutionContext,
    ) -> ExecutionPath:
        """
        Bepaal het volledige execution pad: lane, model, tokens, chain.

        Routing criteria:
        - Maturity L1/L2 → nooit in prod → ring-0/ring-1
        - High risk + prod → escalation model
        - Lage budget → goedkoopste model
        - ACTION lane in prod → HITL verplicht
        """
        lane = _CAPABILITY_LANES.get(capability, WorkflowLane.ADVISORY)
        models = _CAPABILITY_MODELS.get(capability, _DEFAULT_MODELS)
        tokens = _CAPABILITY_TOKENS.get(capability, _DEFAULT_TOKENS)

        # Model selectie op basis van risico en budget
        # Budget-check: gebruik goedkoper model als budget bijna op is
        budget_constrained = context.remaining_budget_eur < 10
        use_escalation = (
            not budget_constrained
            and (context.risk_score >= 75 or context.is_production)
        )
        primary_model = (
            models["escalation"] if use_escalation else models["preferred"]
        )
        # Controleer model beschikbaarheid
        if primary_model not in context.available_models:
            available_fallback = next(
                (m for m in [models["preferred"], "llama3"] if m in context.available_models),
                context.available_models[0] if context.available_models else "llama3",
            )
            logger.warning(
                "Model %s niet beschikbaar — fallback naar %s",
                primary_model, available_fallback,
            )
            primary_model = available_fallback

        # Deployment ring
        ring = self.determine_rollout_ring(context)

        # HITL vereiste
        hitl_required = self.requires_human_approval(capability, context)

        # Chain naam
        _, chain_name = _EVENT_TO_CHAIN.get(
            context.event_type,
            (capability, capability.upper().replace("-", "_")),
        )

        reason = (
            f"lane={lane.value}, model={primary_model}, "
            f"ring={ring.value}, risk={context.risk_level}, "
            f"env={context.environment.value}, maturity={context.maturity_level.value}"
        )

        return ExecutionPath(
            capability=capability,
            lane=lane,
            primary_model=primary_model,
            fallback_model=models["preferred"] if primary_model != models["preferred"] else None,
            max_tokens_input=tokens["max_input"],
            max_tokens_output=tokens["max_output"],
            max_tool_calls=tokens["max_tools"],
            chain_name=chain_name,
            requires_hitl=hitl_required,
            deployment_ring=ring,
            selection_reason=reason,
        )

    def enforce_policy(
        self,
        capability: str,
        context: ExecutionContext,
        tools_requested: list[str] | None = None,
    ) -> None:
        """
        Controleer alle policy regels via de YAML-gedreven PolicyEngine.

        Delegeert naar ollama/policy_engine.py die hitl-, maturity- en
        tool-policies laadt uit /policies/*.yaml.

        Raises:
            PolicyViolationError als een BLOCKER rule geschonden wordt.
        """
        from ollama.policy_engine import get_policy_engine

        lane = _CAPABILITY_LANES.get(capability)
        engine = get_policy_engine()
        engine.enforce(capability, context, tools_requested=tools_requested, lane=lane)

        logger.debug(
            "Policy OK voor capability=%s env=%s risk=%d",
            capability, context.environment.value, context.risk_score,
        )

    def check_budget(self, capability: str, usage: dict[str, Any]) -> bool:
        """
        Controleer of het token/kostenbudget niet overschreden is.

        Args:
            capability: capability naam
            usage: {"tokens_used": int, "cost_eur": float, "tool_calls": int}

        Returns:
            True als binnen budget, False als overschreden.
        """
        tokens = _CAPABILITY_TOKENS.get(capability, _DEFAULT_TOKENS)
        tokens_used = usage.get("tokens_used", 0)
        tool_calls = usage.get("tool_calls", 0)

        if tokens_used > tokens["max_input"] + tokens["max_output"]:
            logger.warning(
                "Budget overschreden voor %s: %d tokens gebruikt (max %d)",
                capability, tokens_used, tokens["max_input"] + tokens["max_output"],
            )
            return False

        if tool_calls > tokens["max_tools"]:
            logger.warning(
                "Tool call budget overschreden voor %s: %d calls (max %d)",
                capability, tool_calls, tokens["max_tools"],
            )
            return False

        return True

    def determine_rollout_ring(self, context: ExecutionContext) -> DeploymentRing:
        """
        Bepaal deployment ring op basis van maturity en omgeving.

        Regel: capability gaat pas naar hogere ring als:
          - evals OK
          - policy OK
          - observability OK
          - rollback mogelijk
        """
        maturity = context.maturity_level
        env = context.environment

        if maturity == MaturityLevel.L1_EXPERIMENTAL:
            return DeploymentRing.LOCAL
        if maturity == MaturityLevel.L2_INTERNAL_BETA:
            return DeploymentRing.AI_TEAM
        if maturity == MaturityLevel.L3_TEAM_PRODUCTION:
            if env in (Environment.LOCAL, Environment.DEV, Environment.TEST):
                return DeploymentRing.INTERNAL_USERS
            return DeploymentRing.LIMITED_PRODUCTION
        # L4 business critical
        return DeploymentRing.FULL_PRODUCTION

    def requires_human_approval(
        self,
        capability: str,
        context: ExecutionContext,
    ) -> bool:
        """
        Beslis of menselijke goedkeuring vereist is.

        Regels:
        - HITL-001: ACTION lane in prod → altijd
        - HITL-002: risk_score >= 75 → altijd
        - HITL-003: CRITICAL risico → altijd
        - HITL-004: L1/L2 maturity in prod → altijd
        """
        lane = _CAPABILITY_LANES.get(capability)

        if lane == WorkflowLane.ACTION and context.is_production:
            return True
        if context.risk_score >= 75:
            return True
        if context.risk_level == "CRITICAL":
            return True
        if context.maturity_level in (
            MaturityLevel.L1_EXPERIMENTAL,
            MaturityLevel.L2_INTERNAL_BETA,
        ) and context.is_production:
            return True

        return False
