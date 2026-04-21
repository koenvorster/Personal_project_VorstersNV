"""Tests voor de 4-Level Evaluation Hierarchy (ollama/evals/hierarchy.py)."""
import json
import pytest

from ollama.evals.hierarchy import (
    EvalHierarchy,
    EvalLevel,
    EvalSuite,
    LevelResult,
    HierarchyResult,
    get_eval_hierarchy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def suite():
    return EvalSuite()


@pytest.fixture
def hierarchy():
    return EvalHierarchy()


# ---------------------------------------------------------------------------
# Level 1 — UNIT
# ---------------------------------------------------------------------------

class TestRunUnit:
    def test_valid_output_passes(self, suite):
        result = suite.run_unit("agent_x", output="Dit is geldige output")
        assert result.passed is True
        assert result.score > 0.0
        assert result.level == EvalLevel.UNIT

    def test_empty_output_fails(self, suite):
        result = suite.run_unit("agent_x", output="")
        assert result.passed is False
        assert result.score == 0.0
        assert any("leeg" in e.lower() for e in result.errors)

    def test_whitespace_only_output_fails(self, suite):
        result = suite.run_unit("agent_x", output="   ")
        assert result.passed is False
        assert result.score == 0.0

    def test_valid_json_with_schema_high_score(self, suite):
        payload = json.dumps({"order_id": "123", "status": "OK"})
        schema = {"required": ["order_id", "status"]}
        result = suite.run_unit("agent_x", output=payload, expected_schema=schema)
        assert result.passed is True
        assert result.score >= 0.8
        assert any("order_id" in d for d in result.details)
        assert any("status" in d for d in result.details)

    def test_missing_required_field_lowers_score(self, suite):
        payload = json.dumps({"order_id": "123"})
        schema = {"required": ["order_id", "status"]}
        result = suite.run_unit("agent_x", output=payload, expected_schema=schema)
        # one field missing → score reduced
        assert result.score < 1.0
        assert any("status" in e for e in result.errors)

    def test_two_missing_fields_further_lowers_score(self, suite):
        payload = json.dumps({"other": "value"})
        schema = {"required": ["order_id", "status", "amount"]}
        result_one = suite.run_unit("agent_x", output=json.dumps({"order_id": "1"}), expected_schema=schema)
        result_two = suite.run_unit("agent_x", output=payload, expected_schema=schema)
        assert result_two.score <= result_one.score

    def test_invalid_json_with_schema_adds_error(self, suite):
        result = suite.run_unit("agent_x", output="{not valid json", expected_schema={"required": ["id"]})
        assert any("json" in e.lower() for e in result.errors)
        assert result.score < 1.0

    def test_plain_text_with_schema_not_json_error(self, suite):
        result = suite.run_unit("agent_x", output="plain text", expected_schema={"required": ["id"]})
        assert any("json" in e.lower() for e in result.errors)

    def test_no_schema_plain_text_passes(self, suite):
        result = suite.run_unit("agent_x", output="some output")
        assert result.passed is True
        assert result.score == 1.0

    def test_agent_name_stored(self, suite):
        result = suite.run_unit("my_agent", output="ok")
        assert result.agent_name == "my_agent"


# ---------------------------------------------------------------------------
# Level 2 — CAPABILITY
# ---------------------------------------------------------------------------

class TestRunCapability:
    def test_all_keywords_present_score_one(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="order fraud detection active",
            expected_keywords=["order", "fraud", "detection"],
        )
        assert result.score == 1.0
        assert result.passed is True

    def test_half_keywords_score_half(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="order confirmed",
            expected_keywords=["order", "fraud"],
        )
        assert result.score == 0.5
        assert result.passed is False

    def test_no_keywords_found_score_zero(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="completely unrelated",
            expected_keywords=["order", "fraud", "detection"],
        )
        assert result.score == 0.0

    def test_empty_keywords_list_passes(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="anything",
            expected_keywords=[],
        )
        assert result.passed is True
        assert result.score == 1.0

    def test_correct_tool_in_details(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="check fraud",
            expected_keywords=["fraud"],
            tool_used="fraud_check",
            expected_tool="fraud_check",
        )
        assert any("fraud_check" in d for d in result.details)
        assert result.score == 1.0

    def test_wrong_tool_lowers_score_and_adds_error(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="check fraud",
            expected_keywords=["fraud"],
            tool_used="wrong_tool",
            expected_tool="fraud_check",
        )
        assert result.score < 1.0
        assert any("fraud_check" in e for e in result.errors)

    def test_no_tool_constraint_no_penalty(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="fraud present",
            expected_keywords=["fraud"],
        )
        assert result.score == 1.0

    def test_keyword_case_insensitive(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="FRAUD detected",
            expected_keywords=["fraud"],
        )
        assert result.score == 1.0

    def test_missing_keywords_in_errors(self, suite):
        result = suite.run_capability(
            "agent_x",
            output="only order here",
            expected_keywords=["order", "missing_keyword"],
        )
        assert any("missing_keyword" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Level 3 — CHAIN
# ---------------------------------------------------------------------------

class TestRunChain:
    def test_all_steps_completed_passes(self, suite):
        steps = ["validate", "enrich", "score", "decide"]
        result = suite.run_chain("agent_x", completed_steps=steps, expected_steps=steps)
        assert result.passed is True
        assert result.score == 1.0

    def test_missing_steps_lowers_score(self, suite):
        result = suite.run_chain(
            "agent_x",
            completed_steps=["validate", "score"],
            expected_steps=["validate", "enrich", "score", "decide"],
        )
        assert result.score < 1.0
        assert any("enrich" in e or "decide" in e for e in result.errors)

    def test_wrong_order_adds_error(self, suite):
        result = suite.run_chain(
            "agent_x",
            completed_steps=["score", "validate", "enrich", "decide"],
            expected_steps=["validate", "enrich", "score", "decide"],
        )
        assert any("volgorde" in e.lower() for e in result.errors)

    def test_checkpoint_recovery_bonus(self, suite):
        steps = ["validate", "enrich", "score", "decide"]
        result_no_cp = suite.run_chain("agent_x", completed_steps=steps, expected_steps=steps, checkpoint_recovery_tested=False)
        result_with_cp = suite.run_chain("agent_x", completed_steps=steps, expected_steps=steps, checkpoint_recovery_tested=True)
        assert result_with_cp.score >= result_no_cp.score
        assert any("recovery" in d.lower() for d in result_with_cp.details)

    def test_empty_expected_steps_passes(self, suite):
        result = suite.run_chain("agent_x", completed_steps=["step1"], expected_steps=[])
        assert result.passed is True
        assert result.score == 1.0

    def test_partial_steps_score_proportional(self, suite):
        result = suite.run_chain(
            "agent_x",
            completed_steps=["a", "b"],
            expected_steps=["a", "b", "c", "d"],
        )
        assert result.score == pytest.approx(0.5, abs=0.01)

    def test_correct_order_details_mention(self, suite):
        steps = ["a", "b", "c"]
        result = suite.run_chain("agent_x", completed_steps=steps, expected_steps=steps)
        assert any("volgorde" in d.lower() for d in result.details)

    def test_checkpoint_recovery_capped_at_one(self, suite):
        steps = ["a", "b"]
        result = suite.run_chain("agent_x", completed_steps=steps, expected_steps=steps, checkpoint_recovery_tested=True)
        assert result.score <= 1.0


# ---------------------------------------------------------------------------
# Level 4 — BUSINESS
# ---------------------------------------------------------------------------

class TestRunBusiness:
    def test_perfect_accuracy_score_one(self, suite):
        decisions = [
            {"predicted": "BLOCK", "actual": "BLOCK"},
            {"predicted": "ALLOW", "actual": "ALLOW"},
            {"predicted": "BLOCK", "actual": "BLOCK"},
        ]
        result = suite.run_business("agent_x", decisions=decisions)
        assert result.score == 1.0
        assert result.passed is True

    def test_zero_accuracy_score_zero(self, suite):
        decisions = [
            {"predicted": "BLOCK", "actual": "ALLOW"},
            {"predicted": "ALLOW", "actual": "BLOCK"},
        ]
        result = suite.run_business("agent_x", decisions=decisions)
        assert result.score == 0.0
        assert result.passed is False

    def test_high_fp_rate_lowers_score_and_adds_error(self, suite):
        # 3 out of 10 are false positives → 30% > 10% threshold
        decisions = (
            [{"predicted": "BLOCK", "actual": "ALLOW"}] * 3
            + [{"predicted": "ALLOW", "actual": "ALLOW"}] * 7
        )
        result = suite.run_business("agent_x", decisions=decisions)
        assert any("false positive" in e.lower() for e in result.errors)
        assert result.score < 0.7

    def test_fp_rate_exactly_ten_percent_no_penalty(self, suite):
        # 1 FP out of 10 → exactly 10%, should NOT trigger error
        decisions = (
            [{"predicted": "BLOCK", "actual": "ALLOW"}] * 1
            + [{"predicted": "ALLOW", "actual": "ALLOW"}] * 9
        )
        result = suite.run_business("agent_x", decisions=decisions)
        assert not any("false positive" in e.lower() for e in result.errors)

    def test_empty_decisions_fails(self, suite):
        result = suite.run_business("agent_x", decisions=[])
        assert result.passed is False
        assert result.score == 0.0
        assert any("beslissingen" in e.lower() for e in result.errors)

    def test_mixed_decisions_correct_accuracy(self, suite):
        decisions = [
            {"predicted": "BLOCK", "actual": "BLOCK"},
            {"predicted": "ALLOW", "actual": "BLOCK"},
            {"predicted": "BLOCK", "actual": "BLOCK"},
            {"predicted": "ALLOW", "actual": "ALLOW"},
        ]
        result = suite.run_business("agent_x", decisions=decisions)
        # 3 correct out of 4 = 0.75; no FP (no predicted=BLOCK & actual=ALLOW)
        assert result.score == pytest.approx(0.75, abs=0.01)

    def test_accuracy_in_details(self, suite):
        decisions = [{"predicted": "ALLOW", "actual": "ALLOW"}]
        result = suite.run_business("agent_x", decisions=decisions)
        assert any("accuracy" in d.lower() for d in result.details)

    def test_fp_rate_in_details(self, suite):
        decisions = [{"predicted": "ALLOW", "actual": "ALLOW"}]
        result = suite.run_business("agent_x", decisions=decisions)
        assert any("false positive" in d.lower() for d in result.details)


# ---------------------------------------------------------------------------
# LevelResult.verdict property
# ---------------------------------------------------------------------------

class TestLevelResultVerdict:
    def test_verdict_pass_at_0_85(self):
        r = LevelResult(EvalLevel.UNIT, "a", True, 0.85)
        assert r.verdict == "PASS"

    def test_verdict_pass_above_0_85(self):
        r = LevelResult(EvalLevel.UNIT, "a", True, 1.0)
        assert r.verdict == "PASS"

    def test_verdict_needs_review_at_0_65(self):
        r = LevelResult(EvalLevel.UNIT, "a", False, 0.65)
        assert r.verdict == "NEEDS_REVIEW"

    def test_verdict_needs_review_between_0_65_and_0_85(self):
        r = LevelResult(EvalLevel.UNIT, "a", False, 0.75)
        assert r.verdict == "NEEDS_REVIEW"

    def test_verdict_fail_below_0_65(self):
        r = LevelResult(EvalLevel.UNIT, "a", False, 0.5)
        assert r.verdict == "FAIL"

    def test_verdict_fail_at_zero(self):
        r = LevelResult(EvalLevel.UNIT, "a", False, 0.0)
        assert r.verdict == "FAIL"


# ---------------------------------------------------------------------------
# EvalHierarchy — run_full_hierarchy
# ---------------------------------------------------------------------------

class TestRunFullHierarchy:
    def _all_passing_kwargs(self):
        return dict(
            unit_kwargs={"output": '{"id": "1", "status": "ok"}', "expected_schema": {"required": ["id", "status"]}},
            capability_kwargs={"output": "order confirmed fraud checked", "expected_keywords": ["order", "fraud"]},
            chain_kwargs={"completed_steps": ["validate", "enrich", "score"], "expected_steps": ["validate", "enrich", "score"]},
            business_kwargs={"decisions": [{"predicted": "ALLOW", "actual": "ALLOW"}, {"predicted": "BLOCK", "actual": "BLOCK"}]},
        )

    def test_all_four_levels_run(self, hierarchy):
        result = hierarchy.run_full_hierarchy("agent_x", **self._all_passing_kwargs(), stop_on_fail=False)
        assert len(result.results) == 4
        assert set(result.results.keys()) == {"UNIT", "CAPABILITY", "CHAIN", "BUSINESS"}

    def test_stop_on_fail_stops_after_first_failure(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": ""},          # will FAIL
            capability_kwargs={"output": "fraud order", "expected_keywords": ["fraud"]},
            stop_on_fail=True,
        )
        assert "UNIT" in result.results
        assert "CAPABILITY" not in result.results

    def test_stop_on_fail_false_runs_all(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": ""},          # FAIL
            capability_kwargs={"output": "fraud", "expected_keywords": ["fraud"]},
            stop_on_fail=False,
        )
        assert "UNIT" in result.results
        assert "CAPABILITY" in result.results

    def test_overall_score_is_average(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": "ok"},
            capability_kwargs={"output": "fraud order", "expected_keywords": ["fraud", "order"]},
            stop_on_fail=False,
        )
        expected = sum(r.score for r in result.results.values()) / len(result.results)
        assert result.overall_score == pytest.approx(expected, abs=0.01)

    def test_blocking_level_set_on_first_fail(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": ""},          # FAIL
            capability_kwargs={"output": "fraud", "expected_keywords": ["fraud"]},
            stop_on_fail=False,
        )
        assert result.blocking_level == "UNIT"

    def test_blocking_level_none_when_all_pass(self, hierarchy):
        result = hierarchy.run_full_hierarchy("agent_x", **self._all_passing_kwargs())
        assert result.blocking_level is None

    def test_overall_verdict_pass(self, hierarchy):
        result = hierarchy.run_full_hierarchy("agent_x", **self._all_passing_kwargs())
        assert result.overall_verdict == "PASS"

    def test_overall_verdict_fail_on_poor_scores(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": ""},
            capability_kwargs={"output": "x", "expected_keywords": ["a", "b", "c", "d", "e"]},
            stop_on_fail=False,
        )
        assert result.overall_verdict == "FAIL"

    def test_skipped_level_not_in_results(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": "present"},
            # no chain or business kwargs
        )
        assert "CHAIN" not in result.results
        assert "BUSINESS" not in result.results

    def test_levels_run_list_matches_results(self, hierarchy):
        result = hierarchy.run_full_hierarchy(
            "agent_x",
            unit_kwargs={"output": "ok"},
            chain_kwargs={"completed_steps": ["a"], "expected_steps": ["a"]},
            stop_on_fail=False,
        )
        assert set(r.name for r in result.levels_run) == set(result.results.keys())


# ---------------------------------------------------------------------------
# EvalHierarchy helpers
# ---------------------------------------------------------------------------

class TestHierarchyHelpers:
    def test_get_ci_levels(self, hierarchy):
        assert hierarchy.get_ci_levels() == [EvalLevel.UNIT, EvalLevel.CAPABILITY]

    def test_get_release_levels(self, hierarchy):
        assert hierarchy.get_release_levels() == [EvalLevel.CHAIN, EvalLevel.BUSINESS]

    def test_run_eval_suite_unit(self, hierarchy):
        result = hierarchy.run_eval_suite("agent_x", EvalLevel.UNIT, output="ok")
        assert result.level == EvalLevel.UNIT

    def test_run_eval_suite_invalid_level_raises(self, hierarchy):
        with pytest.raises((ValueError, AttributeError)):
            hierarchy.run_eval_suite("agent_x", "NOT_A_LEVEL", output="ok")


# ---------------------------------------------------------------------------
# Singleton get_eval_hierarchy
# ---------------------------------------------------------------------------

class TestGetEvalHierarchy:
    def test_singleton_returns_same_instance(self):
        import ollama.evals.hierarchy as mod
        mod._hierarchy = None  # reset between test runs
        h1 = get_eval_hierarchy()
        h2 = get_eval_hierarchy()
        assert h1 is h2

    def test_singleton_is_eval_hierarchy(self):
        import ollama.evals.hierarchy as mod
        mod._hierarchy = None
        h = get_eval_hierarchy()
        assert isinstance(h, EvalHierarchy)
