"""
VorstersNV Workflow Lanes
Configuratie en validatielogica voor de 4 workflow lanes van het AI platform.

Elke lane heeft specifieke temperature, schema-eisen, review-vereisten en
output validatieregels. Dit module centraliseert alle lane-kennis zodat agents
en orchestrators consistent gedrag kunnen garanderen.

Revisie 4 architectuur — WORKFLOW laag.

Gebruik:
    from ollama.workflow_lanes import get_lane_config, validate_output_for_lane
    from ollama.control_plane import WorkflowLane

    config = get_lane_config(WorkflowLane.ADVISORY)
    valid, errors = validate_output_for_lane(WorkflowLane.ADVISORY, output)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ollama.control_plane import WorkflowLane

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# LaneConfig
# ─────────────────────────────────────────────

@dataclass
class LaneConfig:
    """
    Volledige configuratie voor één workflow lane.

    Bevat temperature, schema-eisen, confidence score vereisten, review
    loops en HITL-vereisten op basis van de lane definitie uit de Revisie 4
    architectuur.
    """
    lane: WorkflowLane
    temperature: float

    # DETERMINISTIC-specifiek
    strict_schema: bool = False
    creativity: bool = True
    requires_confidence_score: bool = False

    # ADVISORY-specifiek
    explainability: bool = False
    confidence_score_required: bool = False
    reviewable: bool = False

    # GENERATIVE-specifiek
    style_rules: bool = False
    seo_check: bool = False
    review_loop: bool = False

    # ACTION-specifiek
    hitl_required_in_prod: bool = False
    audit_logging: bool = False
    idempotent: bool = False


# ─────────────────────────────────────────────
# LaneRegistry
# ─────────────────────────────────────────────

LANE_REGISTRY: dict[WorkflowLane, LaneConfig] = {
    WorkflowLane.DETERMINISTIC: LaneConfig(
        lane=WorkflowLane.DETERMINISTIC,
        temperature=0.1,
        strict_schema=True,
        creativity=False,
        requires_confidence_score=False,
    ),
    WorkflowLane.ADVISORY: LaneConfig(
        lane=WorkflowLane.ADVISORY,
        temperature=0.3,
        explainability=True,
        confidence_score_required=True,
        reviewable=True,
        requires_confidence_score=True,
    ),
    WorkflowLane.GENERATIVE: LaneConfig(
        lane=WorkflowLane.GENERATIVE,
        temperature=0.7,
        style_rules=True,
        seo_check=True,
        review_loop=True,
    ),
    WorkflowLane.ACTION: LaneConfig(
        lane=WorkflowLane.ACTION,
        temperature=0.1,
        hitl_required_in_prod=True,
        audit_logging=True,
        idempotent=True,
    ),
}


# ─────────────────────────────────────────────
# Publieke helper functies
# ─────────────────────────────────────────────

def get_lane_config(lane: WorkflowLane) -> LaneConfig:
    """
    Geef de LaneConfig terug voor de opgegeven workflow lane.

    Args:
        lane: WorkflowLane enum waarde.

    Returns:
        LaneConfig voor die lane.

    Raises:
        KeyError als de lane niet geconfigureerd is (zou niet mogen voorkomen).
    """
    config = LANE_REGISTRY.get(lane)
    if config is None:
        raise KeyError(f"Geen LaneConfig gevonden voor lane '{lane}'")
    return config


def get_temperature(lane: WorkflowLane) -> float:
    """
    Geef de aanbevolen LLM temperature terug voor de opgegeven lane.

    Args:
        lane: WorkflowLane enum waarde.

    Returns:
        float temperature waarde (0.0 – 1.0).
    """
    return get_lane_config(lane).temperature


def requires_review_loop(lane: WorkflowLane) -> bool:
    """
    Geeft True terug als de lane een review loop vereist (GENERATIVE lane).

    Args:
        lane: WorkflowLane enum waarde.

    Returns:
        bool
    """
    return get_lane_config(lane).review_loop


def requires_hitl_in_prod(lane: WorkflowLane) -> bool:
    """
    Geeft True terug als de lane HITL vereist in productie (ACTION lane).

    Args:
        lane: WorkflowLane enum waarde.

    Returns:
        bool
    """
    return get_lane_config(lane).hitl_required_in_prod


def validate_output_for_lane(
    lane: WorkflowLane,
    output: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Valideer of de output voldoet aan de eisen van de opgegeven lane.

    Validatieregels per lane:
    - DETERMINISTIC: output mag niet leeg zijn (schema valid)
    - ADVISORY: vereist 'confidence_score' key in output
    - GENERATIVE: vereist 'description' key met minimaal 50 karakters
    - ACTION: vereist 'trace_id' key en 'audit_logged' == True

    Args:
        lane: WorkflowLane om tegen te valideren.
        output: dict met de agent output.

    Returns:
        tuple (is_valid: bool, errors: list[str]) waarbij errors leeg is
        als is_valid True is.
    """
    errors: list[str] = []

    if lane == WorkflowLane.DETERMINISTIC:
        if not output:
            errors.append("DETERMINISTIC lane vereist een niet-lege output (schema valid)")

    elif lane == WorkflowLane.ADVISORY:
        if "confidence_score" not in output:
            errors.append(
                "ADVISORY lane vereist 'confidence_score' in output"
            )

    elif lane == WorkflowLane.GENERATIVE:
        description = output.get("description", "")
        if not isinstance(description, str) or len(description) < 50:
            errors.append(
                "GENERATIVE lane vereist 'description' met minimaal 50 karakters"
                f" (huidig: {len(description) if isinstance(description, str) else 0})"
            )

    elif lane == WorkflowLane.ACTION:
        if "trace_id" not in output:
            errors.append("ACTION lane vereist 'trace_id' in output")
        if not output.get("audit_logged", False):
            errors.append("ACTION lane vereist 'audit_logged' == True in output")

    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(
            "Output validatie mislukt voor lane=%s: %s",
            lane.value, "; ".join(errors),
        )
    return is_valid, errors
