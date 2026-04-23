"""
Tests for ollama/auto_promoter.py — AutoPromoter, PromotionDecision, PromoterConfig.
"""
from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from ollama.ab_tester import (
    ABTestConfig,
    ABTestResult,
    PromptABTester,
    PromptVariant,
    VariantStatus,
)
from ollama.auto_promoter import AutoPromoter, PromotionDecision, PromoterConfig, get_auto_promoter
from ollama.decision_journal import DecisionJournal


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_tester() -> PromptABTester:
    return PromptABTester()


def _make_config(agent_name: str = "test-agent", test_id: str = "test-001") -> ABTestConfig:
    return ABTestConfig(
        test_id=test_id,
        agent_name=agent_name,
        capability="test-capability",
        variants=[
            PromptVariant(variant_id="A", prompt_template="Prompt A", weight=0.5),
            PromptVariant(variant_id="B", prompt_template="Prompt B", weight=0.5),
        ],
        min_samples_per_variant=10,
    )


def _add_results(
    tester: PromptABTester,
    test_id: str,
    agent_name: str,
    variant_a_scores: list[float],
    variant_b_scores: list[float],
):
    for score in variant_a_scores:
        tester.record_result(ABTestResult(
            test_id=test_id, variant_id="A", agent_name=agent_name,
            quality_score=score, latency_ms=100.0, success=True,
        ))
    for score in variant_b_scores:
        tester.record_result(ABTestResult(
            test_id=test_id, variant_id="B", agent_name=agent_name,
            quality_score=score, latency_ms=100.0, success=True,
        ))


def _make_promoter_with_tester(tester: PromptABTester, config: PromoterConfig | None = None) -> AutoPromoter:
    """Create an AutoPromoter that uses a specific PromptABTester instance."""
    promoter = AutoPromoter(config)
    with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
        pass
    return promoter


def _mock_feedback_gate_ok() -> MagicMock:
    """
    Maak een mock-FeedbackAnalyzer die de feedback gate altijd goedkeurt.

    Retourneert een analyzer waarvan ``analyseer_agent()`` een profiel teruggeeft
    met score=4.5 (stijgend), 100 beoordelingen — voldoet aan alle gate-drempels.
    Gebruik in ``patch("ollama.auto_promoter.get_feedback_analyzer", return_value=mock)``.
    """
    mock_profiel = MagicMock()
    mock_profiel.algeheel_gemiddelde = 4.5
    mock_profiel.trend = "stabiel"
    mock_profiel.totaal_beoordelingen = 100

    mock_analyzer = MagicMock()
    mock_analyzer.analyseer_agent.return_value = mock_profiel
    return mock_analyzer


# ── PromoterConfig defaults ───────────────────────────────────────────────────


class TestPromoterConfigDefaults:
    def test_min_runs_default(self):
        cfg = PromoterConfig()
        assert cfg.min_runs_per_variant == 10

    def test_min_score_delta_default(self):
        cfg = PromoterConfig()
        assert cfg.min_score_delta == 0.05

    def test_min_winning_score_default(self):
        cfg = PromoterConfig()
        assert cfg.min_winning_score == 0.75

    def test_auto_promote_default(self):
        cfg = PromoterConfig()
        assert cfg.auto_promote is True

    def test_custom_config(self):
        cfg = PromoterConfig(min_runs_per_variant=5, min_score_delta=0.1, auto_promote=False)
        assert cfg.min_runs_per_variant == 5
        assert cfg.min_score_delta == 0.1
        assert cfg.auto_promote is False


# ── PromotionDecision fields ──────────────────────────────────────────────────


class TestPromotionDecision:
    def test_all_fields_accessible(self):
        d = PromotionDecision(
            agent_name="agent",
            test_id="t1",
            winning_variant_id="A",
            losing_variant_id="B",
            winning_score=0.9,
            losing_score=0.7,
            score_delta=0.2,
            promoted=True,
            reason="A won",
            trace_id="trace-123",
            timestamp="2024-01-01T00:00:00+00:00",
        )
        assert d.agent_name == "agent"
        assert d.winning_score == 0.9
        assert d.score_delta == 0.2
        assert d.promoted is True

    def test_score_delta_matches_winner_minus_loser(self):
        d = PromotionDecision(
            agent_name="a", test_id="t", winning_variant_id="A",
            losing_variant_id="B", winning_score=0.85, losing_score=0.75,
            score_delta=0.10, promoted=True, reason="ok",
            trace_id="x", timestamp="now",
        )
        assert abs(d.score_delta - (d.winning_score - d.losing_score)) < 1e-9


# ── evaluate_agent: no test ───────────────────────────────────────────────────


class TestEvaluateAgentNoTest:
    def test_returns_none_when_no_tests_registered(self):
        tester = _make_tester()
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("unknown-agent")
        assert result is None

    def test_returns_none_for_different_agent(self):
        tester = _make_tester()
        cfg = _make_config(agent_name="other-agent")
        tester.register_test(cfg)
        _add_results(tester, "test-001", "other-agent", [0.9] * 10, [0.7] * 10)
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("test-agent")
        assert result is None

    def test_returns_none_for_disabled_test(self):
        tester = _make_tester()
        cfg = _make_config(agent_name="test-agent")
        cfg.enabled = False
        tester.register_test(cfg)
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("test-agent")
        assert result is None


# ── evaluate_agent: insufficient runs ────────────────────────────────────────


class TestEvaluateAgentInsufficientRuns:
    def test_returns_none_when_no_results_at_all(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("test-agent")
        assert result is None

    def test_returns_none_when_one_variant_below_min(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.7] * 5)
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("test-agent")
        assert result is None

    def test_returns_none_when_both_variants_below_min(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 3, [0.7] * 3)
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("test-agent")
        assert result is None

    def test_returns_none_with_custom_min_runs(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.7] * 10)
        promoter = AutoPromoter(PromoterConfig(min_runs_per_variant=20))
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("test-agent")
        assert result is None


# ── evaluate_agent: clear winner ─────────────────────────────────────────────


class TestEvaluateAgentClearWinner:
    def _run_with_winner(self, auto_promote=True) -> tuple[PromotionDecision, ABTestConfig]:
        tester = _make_tester()
        cfg = _make_config()
        tester.register_test(cfg)
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter(PromoterConfig(auto_promote=auto_promote))
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
            patch("ollama.auto_promoter.get_feedback_analyzer", return_value=_mock_feedback_gate_ok()),
        ):
            result = promoter.evaluate_agent("test-agent")
        return result, cfg

    def test_returns_promotion_decision(self):
        result, _ = self._run_with_winner()
        assert isinstance(result, PromotionDecision)

    def test_promoted_is_true(self):
        result, _ = self._run_with_winner()
        assert result.promoted is True

    def test_winning_variant_is_a(self):
        result, _ = self._run_with_winner()
        assert result.winning_variant_id == "A"

    def test_losing_variant_is_b(self):
        result, _ = self._run_with_winner()
        assert result.losing_variant_id == "B"

    def test_winning_score_correct(self):
        result, _ = self._run_with_winner()
        assert abs(result.winning_score - 0.9) < 0.01

    def test_losing_score_correct(self):
        result, _ = self._run_with_winner()
        assert abs(result.losing_score - 0.75) < 0.01

    def test_score_delta_correct(self):
        result, _ = self._run_with_winner()
        assert abs(result.score_delta - 0.15) < 0.01

    def test_trace_id_is_uuid_string(self):
        result, _ = self._run_with_winner()
        import uuid
        uuid.UUID(result.trace_id)  # should not raise

    def test_timestamp_is_iso_string(self):
        result, _ = self._run_with_winner()
        from datetime import datetime
        datetime.fromisoformat(result.timestamp)  # should not raise

    def test_reason_contains_winning_variant(self):
        result, _ = self._run_with_winner()
        assert "A" in result.reason

    def test_variants_marked_winner_loser(self):
        tester = _make_tester()
        cfg = _make_config()
        tester.register_test(cfg)
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
            patch("ollama.auto_promoter.get_feedback_analyzer", return_value=_mock_feedback_gate_ok()),
        ):
            promoter.evaluate_agent("test-agent")
        variant_a = next(v for v in cfg.variants if v.variant_id == "A")
        variant_b = next(v for v in cfg.variants if v.variant_id == "B")
        assert variant_a.status == VariantStatus.WINNER
        assert variant_b.status == VariantStatus.LOSER


# ── evaluate_agent: insufficient evidence ────────────────────────────────────


class TestEvaluateAgentInsufficientEvidence:
    def test_small_delta_returns_not_promoted(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.78] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert result is not None
        assert result.promoted is False

    def test_small_delta_reason_mentions_delta(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.78] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert "delta" in result.reason.lower() or "insufficient" in result.reason.lower()

    def test_low_winning_score_returns_not_promoted(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        # Winner has only 0.70, below min_winning_score=0.75; delta is sufficient
        _add_results(tester, "test-001", "test-agent", [0.70] * 10, [0.60] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert result is not None
        assert result.promoted is False

    def test_low_winning_score_reason_mentions_score(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.70] * 10, [0.60] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert "score" in result.reason.lower() or "low" in result.reason.lower()

    def test_insufficient_evidence_variants_stay_active(self):
        tester = _make_tester()
        cfg = _make_config()
        tester.register_test(cfg)
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.78] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("test-agent")
        for variant in cfg.variants:
            assert variant.status == VariantStatus.ACTIVE

    def test_no_journal_entry_on_insufficient_evidence(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.78] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("test-agent")
        assert len(journal._store) == 0


# ── auto_promote=False ────────────────────────────────────────────────────────


class TestAutoPromoteFalse:
    def _run_no_promote(self):
        tester = _make_tester()
        cfg = _make_config()
        tester.register_test(cfg)
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter(PromoterConfig(auto_promote=False))
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        return result, cfg, journal

    def test_returns_decision_with_promoted_false(self):
        result, _, _ = self._run_no_promote()
        assert result is not None
        assert result.promoted is False

    def test_variants_not_marked_when_auto_promote_false(self):
        _, cfg, _ = self._run_no_promote()
        for variant in cfg.variants:
            assert variant.status == VariantStatus.ACTIVE

    def test_journal_entry_recorded_when_auto_promote_false(self):
        _, _, journal = self._run_no_promote()
        assert len(journal._store) == 1

    def test_journal_entry_verdict_is_review(self):
        _, _, journal = self._run_no_promote()
        entries = list(journal._store.values())
        assert entries[0].verdict == "REVIEW"


# ── Decision journal on successful promotion ─────────────────────────────────


class TestDecisionJournalIntegration:
    def test_journal_record_called_on_promotion(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = MagicMock(spec=DecisionJournal)
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("test-agent")
        journal.record.assert_called_once()

    def test_journal_entry_agent_name(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("test-agent")
        entry = list(journal._store.values())[0]
        assert entry.agent_name == "test-agent"

    def test_journal_entry_verdict_approved(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
            patch("ollama.auto_promoter.get_feedback_analyzer", return_value=_mock_feedback_gate_ok()),
        ):
            promoter.evaluate_agent("test-agent")
        entry = list(journal._store.values())[0]
        assert entry.verdict == "APPROVED"

    def test_journal_not_called_on_insufficient_evidence(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.78] * 10)
        journal = MagicMock(spec=DecisionJournal)
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("test-agent")
        journal.record.assert_not_called()


# ── evaluate_all ──────────────────────────────────────────────────────────────


class TestEvaluateAll:
    def test_returns_list(self):
        tester = _make_tester()
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            results = promoter.evaluate_all()
        assert isinstance(results, list)

    def test_evaluates_all_agents_with_active_tests(self):
        tester = _make_tester()
        cfg_a = _make_config(agent_name="agent-alpha", test_id="t-alpha")
        cfg_b = _make_config(agent_name="agent-beta", test_id="t-beta")
        tester.register_test(cfg_a)
        tester.register_test(cfg_b)
        _add_results(tester, "t-alpha", "agent-alpha", [0.9] * 10, [0.75] * 10)
        _add_results(tester, "t-beta", "agent-beta", [0.85] * 10, [0.70] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            results = promoter.evaluate_all()
        assert len(results) == 2

    def test_evaluate_all_skips_agents_with_no_clear_winner(self):
        tester = _make_tester()
        cfg_a = _make_config(agent_name="agent-alpha", test_id="t-alpha")
        cfg_b = _make_config(agent_name="agent-beta", test_id="t-beta")
        tester.register_test(cfg_a)
        tester.register_test(cfg_b)
        # agent-alpha has clear winner; agent-beta has insufficient runs
        _add_results(tester, "t-alpha", "agent-alpha", [0.9] * 10, [0.75] * 10)
        _add_results(tester, "t-beta", "agent-beta", [0.9] * 2, [0.75] * 2)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            results = promoter.evaluate_all()
        assert len(results) == 1
        assert results[0].agent_name == "agent-alpha"

    def test_evaluate_all_returns_empty_when_no_tests(self):
        tester = _make_tester()
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            results = promoter.evaluate_all()
        assert results == []


# ── get_promotion_history ─────────────────────────────────────────────────────


class TestGetPromotionHistory:
    def test_empty_initially(self):
        promoter = AutoPromoter()
        assert promoter.get_promotion_history() == []

    def test_records_successful_promotion(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
            patch("ollama.auto_promoter.get_feedback_analyzer", return_value=_mock_feedback_gate_ok()),
        ):
            promoter.evaluate_agent("test-agent")
        history = promoter.get_promotion_history()
        assert len(history) == 1
        assert history[0].promoted is True

    def test_records_failed_promotion(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.78] * 10)
        promoter = AutoPromoter()
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("test-agent")
        history = promoter.get_promotion_history()
        assert len(history) == 1
        assert history[0].promoted is False

    def test_returns_copy_not_reference(self):
        promoter = AutoPromoter()
        h1 = promoter.get_promotion_history()
        h2 = promoter.get_promotion_history()
        assert h1 is not h2

    def test_accumulates_multiple_decisions(self):
        tester = _make_tester()
        cfg1 = _make_config(agent_name="agent-1", test_id="t1")
        cfg2 = _make_config(agent_name="agent-2", test_id="t2")
        tester.register_test(cfg1)
        tester.register_test(cfg2)
        _add_results(tester, "t1", "agent-1", [0.9] * 10, [0.75] * 10)
        _add_results(tester, "t2", "agent-2", [0.85] * 10, [0.70] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            promoter.evaluate_agent("agent-1")
            promoter.evaluate_agent("agent-2")
        assert len(promoter.get_promotion_history()) == 2


# ── Singleton ─────────────────────────────────────────────────────────────────


class TestSingleton:
    def test_get_auto_promoter_returns_same_instance(self):
        import ollama.auto_promoter as mod
        mod._promoter = None
        p1 = get_auto_promoter()
        p2 = get_auto_promoter()
        assert p1 is p2
        mod._promoter = None  # cleanup

    def test_get_auto_promoter_returns_auto_promoter_instance(self):
        import ollama.auto_promoter as mod
        mod._promoter = None
        p = get_auto_promoter()
        assert isinstance(p, AutoPromoter)
        mod._promoter = None  # cleanup

    def test_singleton_has_default_config(self):
        import ollama.auto_promoter as mod
        mod._promoter = None
        p = get_auto_promoter()
        assert p.config.auto_promote is True
        assert p.config.min_runs_per_variant == 10
        mod._promoter = None  # cleanup


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_exact_min_runs_triggers_evaluation(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        _add_results(tester, "test-001", "test-agent", [0.9] * 10, [0.75] * 10)
        promoter = AutoPromoter(PromoterConfig(min_runs_per_variant=10))
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert result is not None

    def test_exact_min_score_delta_triggers_promotion(self):
        tester = _make_tester()
        tester.register_test(_make_config())
        # A=0.80, B=0.75, delta=0.05 exactly
        _add_results(tester, "test-001", "test-agent", [0.80] * 10, [0.75] * 10)
        promoter = AutoPromoter(PromoterConfig(min_score_delta=0.05))
        journal = DecisionJournal()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
            patch("ollama.auto_promoter.get_feedback_analyzer", return_value=_mock_feedback_gate_ok()),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert result is not None
        assert result.promoted is True

    def test_decision_has_correct_test_id(self):
        tester = _make_tester()
        tester.register_test(_make_config(test_id="specific-test-id"))
        _add_results(tester, "specific-test-id", "test-agent", [0.9] * 10, [0.75] * 10)
        journal = DecisionJournal()
        promoter = AutoPromoter()
        with (
            patch("ollama.auto_promoter.get_ab_tester", return_value=tester),
            patch("ollama.auto_promoter.get_decision_journal", return_value=journal),
        ):
            result = promoter.evaluate_agent("test-agent")
        assert result.test_id == "specific-test-id"

    def test_evaluate_agent_result_not_in_history_on_none(self):
        tester = _make_tester()
        promoter = AutoPromoter()
        with patch("ollama.auto_promoter.get_ab_tester", return_value=tester):
            result = promoter.evaluate_agent("ghost-agent")
        assert result is None
        assert len(promoter.get_promotion_history()) == 0
