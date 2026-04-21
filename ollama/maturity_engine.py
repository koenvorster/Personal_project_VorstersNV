"""
Maturity Engine — enforces capability maturity rules per environment.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from enum import Enum


MATURITY_ENV_RULES = {
    "L1": ["dev"],                                         # experimental: alleen lokaal
    "L2": ["dev", "test"],                                 # internal-beta: dev + test
    "L3": ["dev", "test", "staging"],                      # team-production: alles behalve prod
    "L4": ["dev", "test", "staging", "prod"],              # business-critical: overal
}

MATURITY_LABELS = {
    "L1": "experimental",
    "L2": "internal-beta",
    "L3": "team-production",
    "L4": "business-critical",
}


@dataclass
class MaturityCheckResult:
    allowed: bool
    capability: str
    maturity_level: str
    environment: str
    reason: str
    requires_eval: bool = False
    requires_human_approval: bool = False


class MaturityEngine:
    """Checks if a capability can run in a given environment based on maturity level."""

    def check(
        self,
        capability_name: str,
        maturity_level: str,
        environment: str,
        eval_completed: bool = False,
        human_approved: bool = False,
    ) -> MaturityCheckResult:
        allowed_envs = MATURITY_ENV_RULES.get(maturity_level, ["dev"])

        if environment not in allowed_envs:
            return MaturityCheckResult(
                allowed=False,
                capability=capability_name,
                maturity_level=maturity_level,
                environment=environment,
                reason=(
                    f"Maturity {maturity_level} ({MATURITY_LABELS.get(maturity_level)}) "
                    f"not allowed in {environment}. Allowed: {allowed_envs}"
                ),
            )

        # L4 in prod vereist altijd eval + human approval
        if maturity_level == "L4" and environment == "prod":
            if not eval_completed:
                return MaturityCheckResult(
                    allowed=False,
                    capability=capability_name,
                    maturity_level=maturity_level,
                    environment=environment,
                    reason="L4 capability in prod requires completed eval",
                    requires_eval=True,
                )
            if not human_approved:
                return MaturityCheckResult(
                    allowed=False,
                    capability=capability_name,
                    maturity_level=maturity_level,
                    environment=environment,
                    reason="L4 capability in prod requires human approval",
                    requires_human_approval=True,
                )

        return MaturityCheckResult(
            allowed=True,
            capability=capability_name,
            maturity_level=maturity_level,
            environment=environment,
            reason=f"Maturity {maturity_level} allowed in {environment}",
        )

    def get_allowed_environments(self, maturity_level: str) -> list[str]:
        return MATURITY_ENV_RULES.get(maturity_level, ["dev"])

    def get_label(self, maturity_level: str) -> str:
        return MATURITY_LABELS.get(maturity_level, "unknown")

    def can_promote(self, current_level: str, target_level: str) -> tuple[bool, str]:
        levels = ["L1", "L2", "L3", "L4"]
        if current_level not in levels or target_level not in levels:
            return False, "Invalid maturity level"
        curr_idx = levels.index(current_level)
        targ_idx = levels.index(target_level)
        if targ_idx != curr_idx + 1:
            return False, f"Can only promote one level at a time (L{curr_idx+1} → L{targ_idx+1})"
        return True, f"Promotion from {current_level} to {target_level} allowed"


def get_maturity_engine() -> MaturityEngine:
    global _engine
    if _engine is None:
        _engine = MaturityEngine()
    return _engine


_engine: Optional[MaturityEngine] = None
