"""
VorstersNV Deployment Rings Governance
Extra governance logica bovenop de DeploymentRing enum uit control_plane.py.

Elke ring heeft een RingPolicy met toegestane maturity levels, gate-vereisten,
traffic limieten en auto-rollback drempels. De RingGateChecker beslist of een
capability gepromoveerd mag worden naar een hogere ring.

Revisie 4 architectuur — GOVERNANCE laag.

Gebruik:
    from ollama.deployment_rings import RingGateChecker, RING_POLICIES, get_ring_policy
    from ollama.control_plane import DeploymentRing

    checker = RingGateChecker()
    ok, reasons = checker.can_promote(
        "fraud-detection",
        DeploymentRing.AI_TEAM,
        DeploymentRing.INTERNAL_USERS,
        gate_results={
            "evals_passed": True,
            "policy_passed": True,
            "observability_ok": True,
            "rollback_plan": True,
            "error_rate": 0.01,
        },
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .control_plane import DeploymentRing, MaturityLevel

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# RingPolicy
# ─────────────────────────────────────────────

@dataclass
class RingPolicy:
    """
    Governance policy voor één deployment ring.

    Beschrijft welke capability maturity levels toegestaan zijn, welke gates
    doorlopen moeten worden voor promotie, en wat de traffic- en rollback-
    limieten zijn.
    """
    ring: DeploymentRing
    name: str
    allowed_maturity_levels: list[MaturityLevel]
    requires_eval_pass: bool
    requires_policy_pass: bool
    requires_observability: bool
    requires_rollback_plan: bool
    max_traffic_percent: int    # percentage van verkeer dat naar deze ring gaat
    auto_rollback_on_error_rate: float  # bijv. 0.05 = 5% foutrate triggert rollback


# ─────────────────────────────────────────────
# RING_POLICIES — pre-configured voor alle 5 rings
# ─────────────────────────────────────────────

RING_POLICIES: dict[DeploymentRing, RingPolicy] = {
    DeploymentRing.LOCAL: RingPolicy(
        ring=DeploymentRing.LOCAL,
        name="lokaal",
        allowed_maturity_levels=[
            MaturityLevel.L1_EXPERIMENTAL,
            MaturityLevel.L2_INTERNAL_BETA,
            MaturityLevel.L3_TEAM_PRODUCTION,
            MaturityLevel.L4_BUSINESS_CRITICAL,
        ],
        requires_eval_pass=False,
        requires_policy_pass=False,
        requires_observability=False,
        requires_rollback_plan=False,
        max_traffic_percent=100,
        auto_rollback_on_error_rate=1.0,  # geen auto-rollback lokaal
    ),
    DeploymentRing.AI_TEAM: RingPolicy(
        ring=DeploymentRing.AI_TEAM,
        name="AI team",
        allowed_maturity_levels=[
            MaturityLevel.L2_INTERNAL_BETA,
            MaturityLevel.L3_TEAM_PRODUCTION,
            MaturityLevel.L4_BUSINESS_CRITICAL,
        ],
        requires_eval_pass=True,
        requires_policy_pass=True,
        requires_observability=False,
        requires_rollback_plan=False,
        max_traffic_percent=100,
        auto_rollback_on_error_rate=0.20,
    ),
    DeploymentRing.INTERNAL_USERS: RingPolicy(
        ring=DeploymentRing.INTERNAL_USERS,
        name="interne users",
        allowed_maturity_levels=[
            MaturityLevel.L3_TEAM_PRODUCTION,
            MaturityLevel.L4_BUSINESS_CRITICAL,
        ],
        requires_eval_pass=True,
        requires_policy_pass=True,
        requires_observability=True,
        requires_rollback_plan=False,
        max_traffic_percent=100,
        auto_rollback_on_error_rate=0.10,
    ),
    DeploymentRing.LIMITED_PRODUCTION: RingPolicy(
        ring=DeploymentRing.LIMITED_PRODUCTION,
        name="beperkte productie",
        allowed_maturity_levels=[
            MaturityLevel.L3_TEAM_PRODUCTION,
            MaturityLevel.L4_BUSINESS_CRITICAL,
        ],
        requires_eval_pass=True,
        requires_policy_pass=True,
        requires_observability=True,
        requires_rollback_plan=True,
        max_traffic_percent=10,
        auto_rollback_on_error_rate=0.05,
    ),
    DeploymentRing.FULL_PRODUCTION: RingPolicy(
        ring=DeploymentRing.FULL_PRODUCTION,
        name="full productie",
        allowed_maturity_levels=[
            MaturityLevel.L4_BUSINESS_CRITICAL,
        ],
        requires_eval_pass=True,
        requires_policy_pass=True,
        requires_observability=True,
        requires_rollback_plan=True,
        max_traffic_percent=100,
        auto_rollback_on_error_rate=0.05,
    ),
}


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def get_ring_policy(ring: DeploymentRing) -> RingPolicy:
    """
    Geef de RingPolicy terug voor de opgegeven deployment ring.

    Args:
        ring: DeploymentRing enum waarde.

    Returns:
        RingPolicy voor die ring.

    Raises:
        KeyError als de ring niet geconfigureerd is.
    """
    policy = RING_POLICIES.get(ring)
    if policy is None:
        raise KeyError(f"Geen RingPolicy gevonden voor ring '{ring}'")
    return policy


# ─────────────────────────────────────────────
# RingGateChecker
# ─────────────────────────────────────────────

class RingGateChecker:
    """
    Controleert of een capability gepromoveerd mag worden naar een hogere ring.

    Gebruik gate_results om de uitkomst van evaluaties, policy checks,
    observability controles en rollback planning door te geven.

    gate_results verwachte keys:
        evals_passed (bool): evaluaties geslaagd
        policy_passed (bool): policy checks geslaagd
        observability_ok (bool): observability aanwezig
        rollback_plan (bool): rollback plan aanwezig
        error_rate (float): huidige foutrate (0.0 – 1.0)
    """

    def can_promote(
        self,
        capability_name: str,
        current_ring: DeploymentRing,
        to_ring: DeploymentRing,
        gate_results: dict,
    ) -> tuple[bool, list[str]]:
        """
        Beslis of een capability gepromoveerd mag worden naar de doelring.

        Controleert:
        1. Rings moeten aaneengesloten zijn (geen skip van 2+ rings)
        2. Alle vereiste gates van de doelring moeten geslaagd zijn
        3. Huidige foutrate mag niet boven de auto-rollback drempel liggen

        Args:
            capability_name: naam van de capability.
            current_ring: huidige deployment ring.
            to_ring: gewenste doelring.
            gate_results: dict met gate resultaten (zie klasse docstring).

        Returns:
            tuple (can_promote: bool, blocking_reasons: list[str])
        """
        blocking: list[str] = []

        # Ring moet één stap hoger zijn
        if to_ring.value != current_ring.value + 1:
            blocking.append(
                f"Kan niet van ring-{current_ring.value} naar ring-{to_ring.value} "
                f"springen — rings moeten sequentieel gepromoveerd worden"
            )
            return False, blocking

        target_policy = RING_POLICIES[to_ring]

        if target_policy.requires_eval_pass and not gate_results.get("evals_passed", False):
            blocking.append(
                f"Ring-{to_ring.value} ({target_policy.name}) vereist geslaagde evaluaties"
            )

        if target_policy.requires_policy_pass and not gate_results.get("policy_passed", False):
            blocking.append(
                f"Ring-{to_ring.value} ({target_policy.name}) vereist geslaagde policy checks"
            )

        if target_policy.requires_observability and not gate_results.get("observability_ok", False):
            blocking.append(
                f"Ring-{to_ring.value} ({target_policy.name}) vereist observability"
            )

        if target_policy.requires_rollback_plan and not gate_results.get("rollback_plan", False):
            blocking.append(
                f"Ring-{to_ring.value} ({target_policy.name}) vereist een rollback plan"
            )

        error_rate = gate_results.get("error_rate", 0.0)
        if error_rate >= target_policy.auto_rollback_on_error_rate:
            blocking.append(
                f"Foutrate {error_rate:.1%} overschrijdt drempel "
                f"{target_policy.auto_rollback_on_error_rate:.1%} voor ring-{to_ring.value}"
            )

        can = len(blocking) == 0
        if can:
            logger.info(
                "Promotie goedgekeurd: capability=%s ring-%d → ring-%d",
                capability_name, current_ring.value, to_ring.value,
            )
        else:
            logger.warning(
                "Promotie geblokkeerd: capability=%s ring-%d → ring-%d, redenen: %s",
                capability_name, current_ring.value, to_ring.value, blocking,
            )
        return can, blocking

    def get_promotion_requirements(
        self,
        from_ring: DeploymentRing,
        to_ring: DeploymentRing,
    ) -> list[str]:
        """
        Geef een lijst van vereisten terug voor promotie van from_ring naar to_ring.

        Args:
            from_ring: huidige ring.
            to_ring: doelring.

        Returns:
            lijst van vereisten als leesbare strings.
        """
        if to_ring.value != from_ring.value + 1:
            return [
                f"Ongeldige ringsprong: ring-{from_ring.value} → ring-{to_ring.value} "
                "(alleen één stap per keer)"
            ]

        policy = RING_POLICIES[to_ring]
        requirements: list[str] = []

        if policy.requires_eval_pass:
            requirements.append("evals_passed: evaluaties moeten slagen")
        if policy.requires_policy_pass:
            requirements.append("policy_passed: policy checks moeten slagen")
        if policy.requires_observability:
            requirements.append("observability_ok: observability moet geconfigureerd zijn")
        if policy.requires_rollback_plan:
            requirements.append("rollback_plan: rollback plan moet aanwezig zijn")

        requirements.append(
            f"error_rate < {policy.auto_rollback_on_error_rate:.1%}: "
            f"foutrate moet onder de drempel blijven"
        )
        requirements.append(
            f"max_traffic: {policy.max_traffic_percent}% van productieverkeer"
        )

        return requirements

    def validate_ring_config(self, ring: DeploymentRing) -> bool:
        """
        Valideer of de RingPolicy correct geconfigureerd is.

        Controleert:
        - ring is aanwezig in RING_POLICIES
        - max_traffic_percent is 1-100
        - auto_rollback_on_error_rate is 0.0-1.0
        - allowed_maturity_levels is niet leeg

        Args:
            ring: DeploymentRing om te valideren.

        Returns:
            True als de configuratie geldig is, False anders.
        """
        policy = RING_POLICIES.get(ring)
        if policy is None:
            logger.error("Ring %s ontbreekt in RING_POLICIES", ring)
            return False

        if not (1 <= policy.max_traffic_percent <= 100):
            logger.error(
                "Ongeldige max_traffic_percent=%d voor ring %s",
                policy.max_traffic_percent, ring,
            )
            return False

        if not (0.0 <= policy.auto_rollback_on_error_rate <= 1.0):
            logger.error(
                "Ongeldige auto_rollback_on_error_rate=%.3f voor ring %s",
                policy.auto_rollback_on_error_rate, ring,
            )
            return False

        if not policy.allowed_maturity_levels:
            logger.error("allowed_maturity_levels is leeg voor ring %s", ring)
            return False

        return True
