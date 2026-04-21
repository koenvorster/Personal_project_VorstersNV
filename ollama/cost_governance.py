"""
VorstersNV Cost & Model Governance
Tracks en enforceert kostenbeleid per capability.

Gebruik:
    engine = get_cost_governance()
    model = engine.select_model("fraud-detection", risk_score=80)
    allowed, reason = engine.check_budget("fraud-detection", estimated_tokens=3000)
    engine.record_usage("fraud-detection", model, 3000, 500, 2)
    report = engine.get_cost_report()
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ModelTier(Enum):
    CHEAP = "cheap"        # llama3, mistral
    STANDARD = "standard"  # llama3.1
    PREMIUM = "premium"    # llama3.1:70b


@dataclass
class CostPolicy:
    capability: str
    max_input_tokens: int
    max_output_tokens: int
    preferred_model: ModelTier
    escalation_model: ModelTier
    max_tool_calls: int
    monthly_budget_eur: float

    def would_exceed_budget(self, current_spend: float, estimated_cost: float) -> bool:
        return (current_spend + estimated_cost) > self.monthly_budget_eur


@dataclass
class UsageRecord:
    capability: str
    model: str
    input_tokens: int
    output_tokens: int
    tool_calls: int
    cost_eur: float
    timestamp: str


# Token cost per token (both input and output) in EUR — simplified flat rate
_COST_PER_TOKEN = 0.000002

_MODEL_NAMES: dict[ModelTier, str] = {
    ModelTier.CHEAP: "llama3",
    ModelTier.STANDARD: "llama3.1",
    ModelTier.PREMIUM: "llama3.1:70b",
}


class CostGovernanceEngine:
    """Tracks en enforceert kostenbeleid per capability."""

    def __init__(self) -> None:
        self._policies: dict[str, CostPolicy] = {}
        self._usage: list[UsageRecord] = []
        self._load_policies()

    def _load_policies(self) -> None:
        defaults = {
            "fraud-detection": CostPolicy(
                "fraud-detection", 8000, 1000,
                ModelTier.CHEAP, ModelTier.PREMIUM, 3, 100.0,
            ),
            "order-validation": CostPolicy(
                "order-validation", 4000, 500,
                ModelTier.CHEAP, ModelTier.STANDARD, 2, 50.0,
            ),
            "content-generation": CostPolicy(
                "content-generation", 6000, 2000,
                ModelTier.STANDARD, ModelTier.PREMIUM, 1, 150.0,
            ),
            "risk-classification": CostPolicy(
                "risk-classification", 3000, 500,
                ModelTier.CHEAP, ModelTier.CHEAP, 2, 30.0,
            ),
            "default": CostPolicy(
                "default", 4000, 1000,
                ModelTier.CHEAP, ModelTier.STANDARD, 3, 75.0,
            ),
        }
        self._policies = defaults

    # ─── Public API ──────────────────────────────────────────────

    def get_policy(self, capability: str) -> CostPolicy:
        """Geef de policy voor een capability, of de default als onbekend."""
        return self._policies.get(capability, self._policies["default"])

    def select_model(
        self,
        capability: str,
        risk_score: int = 0,
        force_escalation: bool = False,
    ) -> str:
        """
        Selecteer het meest geschikte model.

        Goedkoop model bij normale situatie; escalatie bij hoog risico of geforceerd.

        Args:
            capability: naam van de capability
            risk_score: 0–100 risicoscore
            force_escalation: dwing het escalation model af

        Returns:
            Model naam als string
        """
        policy = self.get_policy(capability)
        if force_escalation or risk_score >= 75:
            return _MODEL_NAMES[policy.escalation_model]
        return _MODEL_NAMES[policy.preferred_model]

    def check_budget(
        self,
        capability: str,
        estimated_tokens: int,
    ) -> tuple[bool, str]:
        """
        Controleer of de aanvraag binnen het budget past.

        Args:
            capability: naam van de capability
            estimated_tokens: geschat aantal input tokens

        Returns:
            (allowed, reason) — False + reden als geblokkeerd
        """
        policy = self.get_policy(capability)

        if estimated_tokens > policy.max_input_tokens:
            return (
                False,
                f"Input tokens {estimated_tokens} exceeds max {policy.max_input_tokens}",
            )

        current = self.get_monthly_spend(capability)
        estimated_cost = estimated_tokens * _COST_PER_TOKEN
        if policy.would_exceed_budget(current, estimated_cost):
            return (
                False,
                f"Would exceed monthly budget of \u20ac{policy.monthly_budget_eur}",
            )

        return True, "OK"

    def record_usage(
        self,
        capability: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tool_calls: int,
    ) -> None:
        """Registreer een usage record voor kostenrapportage."""
        from datetime import datetime
        cost = (input_tokens + output_tokens) * _COST_PER_TOKEN
        self._usage.append(
            UsageRecord(
                capability=capability,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tool_calls=tool_calls,
                cost_eur=cost,
                timestamp=datetime.utcnow().isoformat(),
            )
        )

    def get_monthly_spend(self, capability: str) -> float:
        """Geef totale kosten voor een capability (alle geregistreerde records)."""
        return sum(r.cost_eur for r in self._usage if r.capability == capability)

    def get_cost_report(self) -> dict:
        """
        Geef een overzicht van kosten gegroepeerd per capability.

        Returns:
            dict met per capability: total_eur, calls, tokens
        """
        report: dict[str, dict] = {}
        for r in self._usage:
            if r.capability not in report:
                report[r.capability] = {"total_eur": 0.0, "calls": 0, "tokens": 0}
            report[r.capability]["total_eur"] += r.cost_eur
            report[r.capability]["calls"] += 1
            report[r.capability]["tokens"] += r.input_tokens + r.output_tokens
        return report

    def get_all_usage(self) -> list[UsageRecord]:
        """Geef alle usage records terug (voor auditing)."""
        return list(self._usage)

    def reset_usage(self) -> None:
        """Wis alle usage records (voor testing / maandelijkse reset)."""
        self._usage.clear()


# ─── Singleton ───────────────────────────────────────────────────

_engine: Optional[CostGovernanceEngine] = None


def get_cost_governance() -> CostGovernanceEngine:
    """Singleton accessor voor CostGovernanceEngine."""
    global _engine
    if _engine is None:
        _engine = CostGovernanceEngine()
    return _engine
