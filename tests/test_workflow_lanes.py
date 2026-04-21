"""Tests voor ollama/workflow_lanes.py"""
from __future__ import annotations

import pytest

from ollama.control_plane import WorkflowLane
from ollama.workflow_lanes import (
    LaneConfig,
    LANE_REGISTRY,
    get_lane_config,
    get_temperature,
    requires_review_loop,
    requires_hitl_in_prod,
    validate_output_for_lane,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def all_lanes() -> list[WorkflowLane]:
    return list(WorkflowLane)


# ─────────────────────────────────────────────
# LaneRegistry volledigheid
# ─────────────────────────────────────────────

class TestLaneRegistry:
    def test_all_lanes_present_in_registry(self, all_lanes):
        for lane in all_lanes:
            assert lane in LANE_REGISTRY, f"Lane {lane} ontbreekt in LANE_REGISTRY"

    def test_registry_values_are_lane_config(self, all_lanes):
        for lane in all_lanes:
            assert isinstance(LANE_REGISTRY[lane], LaneConfig)


# ─────────────────────────────────────────────
# get_lane_config
# ─────────────────────────────────────────────

class TestGetLaneConfig:
    def test_deterministic_config(self):
        config = get_lane_config(WorkflowLane.DETERMINISTIC)
        assert config.temperature == pytest.approx(0.1)
        assert config.strict_schema is True
        assert config.creativity is False

    def test_advisory_config(self):
        config = get_lane_config(WorkflowLane.ADVISORY)
        assert config.temperature == pytest.approx(0.3)
        assert config.explainability is True
        assert config.confidence_score_required is True
        assert config.reviewable is True

    def test_generative_config(self):
        config = get_lane_config(WorkflowLane.GENERATIVE)
        assert config.temperature == pytest.approx(0.7)
        assert config.style_rules is True
        assert config.seo_check is True
        assert config.review_loop is True

    def test_action_config(self):
        config = get_lane_config(WorkflowLane.ACTION)
        assert config.temperature == pytest.approx(0.1)
        assert config.hitl_required_in_prod is True
        assert config.audit_logging is True
        assert config.idempotent is True


# ─────────────────────────────────────────────
# get_temperature
# ─────────────────────────────────────────────

class TestGetTemperature:
    def test_deterministic_temperature(self):
        assert get_temperature(WorkflowLane.DETERMINISTIC) == pytest.approx(0.1)

    def test_advisory_temperature(self):
        assert get_temperature(WorkflowLane.ADVISORY) == pytest.approx(0.3)

    def test_generative_temperature(self):
        assert get_temperature(WorkflowLane.GENERATIVE) == pytest.approx(0.7)

    def test_action_temperature(self):
        assert get_temperature(WorkflowLane.ACTION) == pytest.approx(0.1)


# ─────────────────────────────────────────────
# requires_review_loop / requires_hitl_in_prod
# ─────────────────────────────────────────────

class TestLaneFlags:
    def test_generative_requires_review_loop(self):
        assert requires_review_loop(WorkflowLane.GENERATIVE) is True

    def test_deterministic_no_review_loop(self):
        assert requires_review_loop(WorkflowLane.DETERMINISTIC) is False

    def test_advisory_no_review_loop(self):
        assert requires_review_loop(WorkflowLane.ADVISORY) is False

    def test_action_requires_hitl_in_prod(self):
        assert requires_hitl_in_prod(WorkflowLane.ACTION) is True

    def test_deterministic_no_hitl_in_prod(self):
        assert requires_hitl_in_prod(WorkflowLane.DETERMINISTIC) is False

    def test_generative_no_hitl_in_prod(self):
        assert requires_hitl_in_prod(WorkflowLane.GENERATIVE) is False


# ─────────────────────────────────────────────
# validate_output_for_lane
# ─────────────────────────────────────────────

class TestValidateOutputForLane:
    # DETERMINISTIC
    def test_deterministic_valid_non_empty_output(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.DETERMINISTIC,
            {"schema_valid": True, "mapped_fields": 5},
        )
        assert valid is True
        assert errors == []

    def test_deterministic_invalid_empty_output(self):
        valid, errors = validate_output_for_lane(WorkflowLane.DETERMINISTIC, {})
        assert valid is False
        assert len(errors) > 0

    # ADVISORY
    def test_advisory_valid_with_confidence_score(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.ADVISORY,
            {"confidence_score": 0.87, "explanation": "..."},
        )
        assert valid is True
        assert errors == []

    def test_advisory_invalid_missing_confidence_score(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.ADVISORY,
            {"explanation": "only explanation, no score"},
        )
        assert valid is False
        assert any("confidence_score" in e for e in errors)

    # GENERATIVE
    def test_generative_valid_long_description(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.GENERATIVE,
            {"description": "A" * 50},
        )
        assert valid is True

    def test_generative_valid_exactly_50_chars(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.GENERATIVE,
            {"description": "x" * 50},
        )
        assert valid is True

    def test_generative_invalid_description_too_short(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.GENERATIVE,
            {"description": "Te kort"},
        )
        assert valid is False
        assert any("50" in e for e in errors)

    def test_generative_invalid_missing_description(self):
        valid, errors = validate_output_for_lane(WorkflowLane.GENERATIVE, {})
        assert valid is False

    # ACTION
    def test_action_valid_with_trace_id_and_audit(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.ACTION,
            {"trace_id": "abc-123", "audit_logged": True},
        )
        assert valid is True
        assert errors == []

    def test_action_invalid_missing_trace_id(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.ACTION,
            {"audit_logged": True},
        )
        assert valid is False
        assert any("trace_id" in e for e in errors)

    def test_action_invalid_audit_not_logged(self):
        valid, errors = validate_output_for_lane(
            WorkflowLane.ACTION,
            {"trace_id": "abc-123", "audit_logged": False},
        )
        assert valid is False
        assert any("audit_logged" in e for e in errors)

    def test_action_invalid_both_fields_missing(self):
        valid, errors = validate_output_for_lane(WorkflowLane.ACTION, {})
        assert valid is False
        assert len(errors) == 2
