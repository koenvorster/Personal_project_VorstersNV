"""
Tests voor de LLM-as-Judge evaluation pipeline (ollama/evals/judge.py).
Gebruikt MockJudgeBackend — geen externe services vereist.
"""
import os
import pytest

from ollama.evals.judge import (
    EvalCase,
    EvalMetric,
    EvalPipeline,
    EvalResult,
    EvalScore,
    MockJudgeBackend,
    OllamaJudgeBackend,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

EVALS_DIR = os.path.join(os.path.dirname(__file__), "evals")


def make_case(
    case_id="test-001",
    agent_name="test-agent",
    input_prompt="Analyseer dit",
    expected_output="Verwachte output tekst",
    actual_output="",
    metadata=None,
) -> EvalCase:
    kwargs = dict(
        case_id=case_id,
        agent_name=agent_name,
        input_prompt=input_prompt,
        expected_output=expected_output,
        actual_output=actual_output,
    )
    if metadata is not None:
        kwargs["metadata"] = metadata
    return EvalCase(**kwargs)


# ── EvalCase ──────────────────────────────────────────────────────────────────

class TestEvalCase:
    def test_required_fields_stored(self):
        case = make_case(case_id="c1", agent_name="agent-x", input_prompt="Q", expected_output="A")
        assert case.case_id == "c1"
        assert case.agent_name == "agent-x"
        assert case.input_prompt == "Q"
        assert case.expected_output == "A"

    def test_default_actual_output_empty_string(self):
        case = make_case()
        assert case.actual_output == ""

    def test_actual_output_can_be_set(self):
        case = make_case(actual_output="echte output")
        assert case.actual_output == "echte output"

    def test_metadata_defaults_to_empty_dict(self):
        case = make_case()
        assert case.metadata == {}

    def test_metadata_stored_when_provided(self):
        case = make_case(metadata={"risk_level": "high"})
        assert case.metadata["risk_level"] == "high"


# ── EvalScore ─────────────────────────────────────────────────────────────────

class TestEvalScore:
    def test_passed_true_when_score_above_threshold(self):
        s = EvalScore(metric=EvalMetric.RELEVANCE, score=0.9, rationale="goed")
        assert s.passed is True

    def test_passed_true_when_score_exactly_threshold(self):
        s = EvalScore(metric=EvalMetric.RELEVANCE, score=0.7, rationale="net genoeg")
        assert s.passed is True

    def test_passed_false_when_score_below_threshold(self):
        s = EvalScore(metric=EvalMetric.SAFETY, score=0.69, rationale="te laag")
        assert s.passed is False

    def test_passed_false_when_score_zero(self):
        s = EvalScore(metric=EvalMetric.FAITHFULNESS, score=0.0, rationale="leeg")
        assert s.passed is False

    def test_all_metrics_accepted(self):
        for metric in EvalMetric:
            s = EvalScore(metric=metric, score=0.8, rationale="ok")
            assert s.metric == metric


# ── EvalResult ────────────────────────────────────────────────────────────────

class TestEvalResult:
    def _make_result(self, score: float) -> EvalResult:
        scores = [EvalScore(metric=EvalMetric.RELEVANCE, score=score, rationale="test")]
        return EvalResult(case_id="r1", agent_name="agent", scores=scores)

    def test_verdict_pass_when_score_at_least_08(self):
        result = self._make_result(0.85)
        assert result.verdict == "PASS"

    def test_verdict_pass_when_score_exactly_08(self):
        result = self._make_result(0.8)
        assert result.verdict == "PASS"

    def test_verdict_needs_review_when_score_between_06_and_08(self):
        result = self._make_result(0.7)
        assert result.verdict == "NEEDS_REVIEW"

    def test_verdict_needs_review_when_score_exactly_06(self):
        result = self._make_result(0.6)
        assert result.verdict == "NEEDS_REVIEW"

    def test_verdict_fail_when_score_below_06(self):
        result = self._make_result(0.5)
        assert result.verdict == "FAIL"

    def test_verdict_fail_when_score_zero(self):
        result = self._make_result(0.0)
        assert result.verdict == "FAIL"

    def test_overall_score_calculated_as_average(self):
        scores = [
            EvalScore(metric=EvalMetric.FAITHFULNESS, score=0.8, rationale=""),
            EvalScore(metric=EvalMetric.RELEVANCE, score=0.6, rationale=""),
        ]
        result = EvalResult(case_id="r2", agent_name="a", scores=scores)
        assert abs(result.overall_score - 0.7) < 1e-9

    def test_overall_score_zero_when_no_scores(self):
        result = EvalResult(case_id="r3", agent_name="a", scores=[])
        assert result.overall_score == 0.0

    def test_verdict_fail_when_no_scores(self):
        result = EvalResult(case_id="r4", agent_name="a", scores=[])
        assert result.verdict == "FAIL"


# ── MockJudgeBackend ──────────────────────────────────────────────────────────

class TestMockJudgeBackend:
    def test_evaluate_returns_eval_score(self):
        backend = MockJudgeBackend()
        case = make_case(expected_output="abc", actual_output="abc")
        score = backend.evaluate(case, EvalMetric.FAITHFULNESS)
        assert isinstance(score, EvalScore)

    def test_score_is_one_when_outputs_equal_length(self):
        backend = MockJudgeBackend()
        case = make_case(expected_output="hello", actual_output="world")
        score = backend.evaluate(case, EvalMetric.COMPLETENESS)
        assert score.score == 1.0

    def test_score_is_zero_when_actual_output_empty(self):
        backend = MockJudgeBackend()
        case = make_case(expected_output="something", actual_output="")
        score = backend.evaluate(case, EvalMetric.RELEVANCE)
        assert score.score == 0.0

    def test_score_capped_at_one(self):
        backend = MockJudgeBackend()
        # actual longer than expected → should be capped at 1.0
        case = make_case(expected_output="short", actual_output="much longer output text here")
        score = backend.evaluate(case, EvalMetric.SAFETY)
        assert score.score <= 1.0

    def test_evaluate_metric_stored_in_score(self):
        backend = MockJudgeBackend()
        case = make_case(expected_output="x", actual_output="x")
        score = backend.evaluate(case, EvalMetric.SAFETY)
        assert score.metric == EvalMetric.SAFETY

    def test_rationale_is_non_empty_string(self):
        backend = MockJudgeBackend()
        case = make_case(expected_output="y", actual_output="y")
        score = backend.evaluate(case, EvalMetric.FAITHFULNESS)
        assert isinstance(score.rationale, str)
        assert len(score.rationale) > 0


# ── EvalPipeline ──────────────────────────────────────────────────────────────

class TestEvalPipeline:
    def test_default_backend_is_mock(self):
        pipeline = EvalPipeline()
        assert isinstance(pipeline.backend, MockJudgeBackend)

    def test_evaluate_case_returns_eval_result(self):
        pipeline = EvalPipeline()
        case = make_case()
        result = pipeline.evaluate_case(case)
        assert isinstance(result, EvalResult)

    def test_evaluate_case_with_all_metrics_produces_four_scores(self):
        pipeline = EvalPipeline()
        case = make_case()
        result = pipeline.evaluate_case(case)
        assert len(result.scores) == len(EvalMetric)

    def test_evaluate_case_with_single_metric(self):
        pipeline = EvalPipeline()
        case = make_case()
        result = pipeline.evaluate_case(case, metrics=[EvalMetric.SAFETY])
        assert len(result.scores) == 1
        assert result.scores[0].metric == EvalMetric.SAFETY

    def test_evaluate_case_stores_result_internally(self):
        pipeline = EvalPipeline()
        case = make_case()
        pipeline.evaluate_case(case)
        assert len(pipeline._results) == 1

    def test_load_jsonl_returns_cases(self):
        pipeline = EvalPipeline()
        path = os.path.join(EVALS_DIR, "fraud_advisor.jsonl")
        cases = pipeline.load_jsonl(path)
        assert len(cases) == 3
        assert all(isinstance(c, EvalCase) for c in cases)

    def test_load_jsonl_fields_correct(self):
        pipeline = EvalPipeline()
        path = os.path.join(EVALS_DIR, "fraud_advisor.jsonl")
        cases = pipeline.load_jsonl(path)
        assert cases[0].case_id == "fa-001"
        assert cases[0].agent_name == "fraud-advisor"

    def test_load_jsonl_metadata_parsed(self):
        pipeline = EvalPipeline()
        path = os.path.join(EVALS_DIR, "fraud_advisor.jsonl")
        cases = pipeline.load_jsonl(path)
        assert cases[0].metadata.get("risk_level") == "high"

    def test_load_jsonl_empty_for_nonexistent_file(self):
        pipeline = EvalPipeline()
        cases = pipeline.load_jsonl("/nonexistent/path/file.jsonl")
        assert cases == []

    def test_run_from_jsonl_returns_results(self):
        pipeline = EvalPipeline()
        path = os.path.join(EVALS_DIR, "fraud_advisor.jsonl")
        results = pipeline.run_from_jsonl(path)
        assert len(results) == 3
        assert all(isinstance(r, EvalResult) for r in results)

    def test_run_from_jsonl_order_analyst(self):
        pipeline = EvalPipeline()
        path = os.path.join(EVALS_DIR, "order_analyst.jsonl")
        results = pipeline.run_from_jsonl(path)
        assert len(results) == 2

    def test_get_summary_contains_all_keys(self):
        pipeline = EvalPipeline()
        pipeline.evaluate_case(make_case(actual_output="x" * 200, expected_output="y" * 10))
        summary = pipeline.get_summary()
        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "needs_review" in summary
        assert "avg_score" in summary

    def test_get_summary_empty_pipeline(self):
        pipeline = EvalPipeline()
        summary = pipeline.get_summary()
        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["needs_review"] == 0

    def test_get_summary_counts_correct(self):
        pipeline = EvalPipeline()
        # actual_output="" → score 0.0 → FAIL
        pipeline.evaluate_case(make_case(case_id="x1", expected_output="abc", actual_output=""))
        summary = pipeline.get_summary()
        assert summary["total"] == 1
        assert summary["failed"] == 1

    def test_get_agent_scores_filters_by_agent(self):
        pipeline = EvalPipeline()
        pipeline.evaluate_case(make_case(case_id="a1", agent_name="agent-A"))
        pipeline.evaluate_case(make_case(case_id="b1", agent_name="agent-B"))
        pipeline.evaluate_case(make_case(case_id="a2", agent_name="agent-A"))
        results = pipeline.get_agent_scores("agent-A")
        assert len(results) == 2
        assert all(r.agent_name == "agent-A" for r in results)

    def test_get_agent_scores_returns_empty_for_unknown_agent(self):
        pipeline = EvalPipeline()
        pipeline.evaluate_case(make_case(agent_name="agent-A"))
        results = pipeline.get_agent_scores("nonexistent")
        assert results == []

    def test_clear_resets_results(self):
        pipeline = EvalPipeline()
        pipeline.evaluate_case(make_case())
        pipeline.evaluate_case(make_case())
        assert len(pipeline._results) == 2
        pipeline.clear()
        assert len(pipeline._results) == 0

    def test_clear_then_summary_empty(self):
        pipeline = EvalPipeline()
        pipeline.evaluate_case(make_case())
        pipeline.clear()
        summary = pipeline.get_summary()
        assert summary["total"] == 0


# ── EvalMetric ────────────────────────────────────────────────────────────────

class TestEvalMetric:
    def test_all_four_metrics_exist(self):
        assert EvalMetric.FAITHFULNESS.value == "faithfulness"
        assert EvalMetric.RELEVANCE.value == "relevance"
        assert EvalMetric.COMPLETENESS.value == "completeness"
        assert EvalMetric.SAFETY.value == "safety"

    def test_metric_count(self):
        assert len(list(EvalMetric)) == 4


# ── OllamaJudgeBackend ────────────────────────────────────────────────────────

class TestOllamaJudgeBackend:
    def test_evaluate_raises_not_implemented(self):
        backend = OllamaJudgeBackend()
        case = make_case()
        with pytest.raises(NotImplementedError):
            backend.evaluate(case, EvalMetric.FAITHFULNESS)

    def test_default_model_is_llama3(self):
        backend = OllamaJudgeBackend()
        assert backend.model == "llama3"
