"""Tests voor ollama/ab_tester.py — A/B Testing Framework."""
from __future__ import annotations

import pytest

from ollama.ab_tester import (
    ABTestConfig,
    ABTestResult,
    ABTestSummary,
    PromptABTester,
    PromptVariant,
    VariantStatus,
    get_ab_tester,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_variant(vid: str, weight: float = 0.5, status: VariantStatus = VariantStatus.ACTIVE) -> PromptVariant:
    return PromptVariant(
        variant_id=vid,
        prompt_template=f"Prompt voor variant {vid}",
        weight=weight,
        status=status,
    )


def make_config(
    test_id: str = "test-1",
    agent_name: str = "agent-x",
    capability: str = "cap-a",
    variants: list[PromptVariant] | None = None,
    min_samples: int = 2,
    enabled: bool = True,
) -> ABTestConfig:
    if variants is None:
        variants = [make_variant("A", 0.7), make_variant("B", 0.3)]
    return ABTestConfig(
        test_id=test_id,
        agent_name=agent_name,
        capability=capability,
        variants=variants,
        min_samples_per_variant=min_samples,
        enabled=enabled,
    )


def make_result(
    test_id: str = "test-1",
    variant_id: str = "A",
    quality_score: float = 0.8,
    latency_ms: float = 100.0,
    success: bool = True,
) -> ABTestResult:
    return ABTestResult(
        test_id=test_id,
        variant_id=variant_id,
        agent_name="agent-x",
        quality_score=quality_score,
        latency_ms=latency_ms,
        success=success,
    )


@pytest.fixture
def tester() -> PromptABTester:
    """Frisse PromptABTester per test."""
    return PromptABTester()


@pytest.fixture
def registered_tester() -> PromptABTester:
    t = PromptABTester()
    t.register_test(make_config())
    return t


# ─────────────────────────────────────────────
# PromptVariant
# ─────────────────────────────────────────────

def test_prompt_variant_defaults():
    v = PromptVariant(variant_id="A", prompt_template="Hallo")
    assert v.weight == 0.5
    assert v.status == VariantStatus.ACTIVE
    assert v.description == ""


def test_prompt_variant_custom_values():
    v = PromptVariant(
        variant_id="control",
        prompt_template="Control prompt",
        weight=0.9,
        status=VariantStatus.WINNER,
        description="De controle variant",
    )
    assert v.variant_id == "control"
    assert v.weight == 0.9
    assert v.status == VariantStatus.WINNER
    assert v.description == "De controle variant"


# ─────────────────────────────────────────────
# VariantStatus
# ─────────────────────────────────────────────

def test_variant_status_values_exist():
    assert VariantStatus.ACTIVE.value == "active"
    assert VariantStatus.WINNER.value == "winner"
    assert VariantStatus.LOSER.value == "loser"
    assert VariantStatus.PAUSED.value == "paused"


# ─────────────────────────────────────────────
# ABTestConfig.get_active_variants
# ─────────────────────────────────────────────

def test_get_active_variants_filters_active():
    variants = [
        make_variant("A", status=VariantStatus.ACTIVE),
        make_variant("B", status=VariantStatus.PAUSED),
        make_variant("C", status=VariantStatus.WINNER),
        make_variant("D", status=VariantStatus.LOSER),
    ]
    config = make_config(variants=variants)
    active = config.get_active_variants()
    assert len(active) == 1
    assert active[0].variant_id == "A"


def test_get_active_variants_paused_not_included():
    variants = [
        make_variant("A", status=VariantStatus.ACTIVE),
        make_variant("B", status=VariantStatus.PAUSED),
    ]
    config = make_config(variants=variants)
    active = config.get_active_variants()
    ids = [v.variant_id for v in active]
    assert "B" not in ids


def test_get_active_variants_all_active():
    variants = [make_variant("A"), make_variant("B"), make_variant("C")]
    config = make_config(variants=variants)
    assert len(config.get_active_variants()) == 3


def test_get_active_variants_none_active():
    variants = [
        make_variant("A", status=VariantStatus.PAUSED),
        make_variant("B", status=VariantStatus.LOSER),
    ]
    config = make_config(variants=variants)
    assert config.get_active_variants() == []


# ─────────────────────────────────────────────
# ABTestConfig.normalize_weights
# ─────────────────────────────────────────────

def test_normalize_weights_two_variants():
    variants = [make_variant("A", weight=0.7), make_variant("B", weight=0.3)]
    config = make_config(variants=variants)
    config.normalize_weights()
    active = config.get_active_variants()
    total = sum(v.weight for v in active)
    assert abs(total - 1.0) < 1e-9


def test_normalize_weights_unequal_weights():
    variants = [make_variant("A", weight=2.0), make_variant("B", weight=6.0), make_variant("C", weight=2.0)]
    config = make_config(variants=variants)
    config.normalize_weights()
    active = config.get_active_variants()
    total = sum(v.weight for v in active)
    assert abs(total - 1.0) < 1e-9
    # B should have weight 0.6
    b = next(v for v in active if v.variant_id == "B")
    assert abs(b.weight - 0.6) < 1e-9


def test_normalize_weights_single_variant():
    variants = [make_variant("A", weight=0.4)]
    config = make_config(variants=variants)
    config.normalize_weights()
    assert abs(config.variants[0].weight - 1.0) < 1e-9


def test_normalize_weights_no_active_no_crash():
    variants = [
        make_variant("A", status=VariantStatus.PAUSED),
        make_variant("B", status=VariantStatus.LOSER),
    ]
    config = make_config(variants=variants)
    # Should not raise
    config.normalize_weights()


def test_normalize_weights_only_active_variants_affected():
    variants = [
        make_variant("A", weight=0.5, status=VariantStatus.ACTIVE),
        make_variant("B", weight=0.5, status=VariantStatus.PAUSED),
    ]
    config = make_config(variants=variants)
    config.normalize_weights()
    paused = next(v for v in config.variants if v.variant_id == "B")
    # Paused variant weight must remain unchanged
    assert paused.weight == 0.5


# ─────────────────────────────────────────────
# register_test / get_test
# ─────────────────────────────────────────────

def test_register_and_get_test(tester):
    config = make_config(test_id="my-test")
    tester.register_test(config)
    result = tester.get_test("my-test")
    assert result is not None
    assert result.test_id == "my-test"


def test_get_test_unknown_returns_none(tester):
    assert tester.get_test("nonexistent") is None


def test_register_test_normalizes_weights(tester):
    variants = [make_variant("A", weight=3.0), make_variant("B", weight=1.0)]
    config = make_config(variants=variants)
    tester.register_test(config)
    active = tester.get_test(config.test_id).get_active_variants()
    total = sum(v.weight for v in active)
    assert abs(total - 1.0) < 1e-9


# ─────────────────────────────────────────────
# select_variant
# ─────────────────────────────────────────────

def test_select_variant_unknown_test_returns_none(tester):
    assert tester.select_variant("nonexistent") is None


def test_select_variant_disabled_test_returns_none(tester):
    config = make_config(test_id="disabled", enabled=False)
    tester.register_test(config)
    assert tester.select_variant("disabled") is None


def test_select_variant_with_seed_deterministic(registered_tester):
    seed = "trace-abc-123"
    first = registered_tester.select_variant("test-1", seed=seed)
    second = registered_tester.select_variant("test-1", seed=seed)
    assert first is not None
    assert second is not None
    assert first.variant_id == second.variant_id


def test_select_variant_different_seeds_can_differ(registered_tester):
    results = set()
    seeds = [f"seed-{i}" for i in range(50)]
    for s in seeds:
        v = registered_tester.select_variant("test-1", seed=s)
        if v:
            results.add(v.variant_id)
    # With 50 different seeds and two variants, both should appear
    assert len(results) >= 2


def test_select_variant_weight_one_always_selected(tester):
    variants = [make_variant("A", weight=1.0), make_variant("B", weight=0.0)]
    config = make_config(variants=variants)
    tester.register_test(config)
    for i in range(20):
        v = tester.select_variant(config.test_id, seed=f"s{i}")
        assert v is not None
        assert v.variant_id == "A"


def test_select_variant_returns_prompt_variant_instance(registered_tester):
    v = registered_tester.select_variant("test-1", seed="fixed")
    assert isinstance(v, PromptVariant)


def test_select_variant_no_active_variants_returns_none(tester):
    variants = [make_variant("A", status=VariantStatus.PAUSED)]
    config = make_config(variants=variants)
    tester.register_test(config)
    assert tester.select_variant(config.test_id) is None


# ─────────────────────────────────────────────
# record_result / get_results_for_variant
# ─────────────────────────────────────────────

def test_record_and_get_results_for_variant(tester):
    r = make_result(test_id="t1", variant_id="A")
    tester.record_result(r)
    results = tester.get_results_for_variant("t1", "A")
    assert len(results) == 1
    assert results[0].variant_id == "A"


def test_get_results_for_variant_filters_correctly(tester):
    tester.record_result(make_result(test_id="t1", variant_id="A"))
    tester.record_result(make_result(test_id="t1", variant_id="B"))
    tester.record_result(make_result(test_id="t2", variant_id="A"))

    assert len(tester.get_results_for_variant("t1", "A")) == 1
    assert len(tester.get_results_for_variant("t1", "B")) == 1
    assert len(tester.get_results_for_variant("t2", "A")) == 1
    assert len(tester.get_results_for_variant("t1", "C")) == 0


# ─────────────────────────────────────────────
# get_summary
# ─────────────────────────────────────────────

def test_get_summary_no_results(tester):
    config = make_config(test_id="empty")
    tester.register_test(config)
    summary = tester.get_summary("empty")
    assert summary.variant_stats == {}
    assert summary.winner is None


def test_get_summary_avg_score(tester):
    config = make_config(test_id="t1", min_samples=2)
    tester.register_test(config)
    tester.record_result(make_result("t1", "A", quality_score=0.6))
    tester.record_result(make_result("t1", "A", quality_score=0.8))
    tester.record_result(make_result("t1", "B", quality_score=0.4))
    tester.record_result(make_result("t1", "B", quality_score=0.6))
    summary = tester.get_summary("t1")
    assert abs(summary.variant_stats["A"]["avg_score"] - 0.7) < 1e-3
    assert abs(summary.variant_stats["B"]["avg_score"] - 0.5) < 1e-3


def test_get_summary_success_rate(tester):
    config = make_config(test_id="t1", min_samples=2)
    tester.register_test(config)
    tester.record_result(make_result("t1", "A", success=True))
    tester.record_result(make_result("t1", "A", success=False))
    summary = tester.get_summary("t1")
    assert abs(summary.variant_stats["A"]["success_rate"] - 0.5) < 1e-3


def test_get_summary_avg_latency(tester):
    config = make_config(test_id="t1", min_samples=2)
    tester.register_test(config)
    tester.record_result(make_result("t1", "A", latency_ms=100.0))
    tester.record_result(make_result("t1", "A", latency_ms=200.0))
    summary = tester.get_summary("t1")
    assert abs(summary.variant_stats["A"]["avg_latency"] - 150.0) < 1e-3


def test_get_summary_winner_with_enough_samples(tester):
    config = make_config(test_id="t1", min_samples=2)
    tester.register_test(config)
    # A scores higher
    for _ in range(2):
        tester.record_result(make_result("t1", "A", quality_score=0.9))
    for _ in range(2):
        tester.record_result(make_result("t1", "B", quality_score=0.4))
    summary = tester.get_summary("t1")
    assert summary.winner == "A"


def test_get_summary_winner_is_highest_avg_score(tester):
    config = make_config(test_id="t1", min_samples=1)
    tester.register_test(config)
    tester.record_result(make_result("t1", "A", quality_score=0.3))
    tester.record_result(make_result("t1", "B", quality_score=0.95))
    summary = tester.get_summary("t1")
    assert summary.winner == "B"


def test_get_summary_insufficient_samples_no_winner(tester):
    config = make_config(test_id="t1", min_samples=5)
    tester.register_test(config)
    # Only 2 results per variant — below min_samples=5
    for _ in range(2):
        tester.record_result(make_result("t1", "A", quality_score=0.9))
    for _ in range(2):
        tester.record_result(make_result("t1", "B", quality_score=0.5))
    summary = tester.get_summary("t1")
    assert summary.winner is None


def test_get_summary_count_is_correct(tester):
    config = make_config(test_id="t1", min_samples=1)
    tester.register_test(config)
    for _ in range(3):
        tester.record_result(make_result("t1", "A"))
    for _ in range(5):
        tester.record_result(make_result("t1", "B"))
    summary = tester.get_summary("t1")
    assert summary.variant_stats["A"]["count"] == 3
    assert summary.variant_stats["B"]["count"] == 5


def test_get_summary_recommendation_contains_winner(tester):
    config = make_config(test_id="t1", min_samples=1)
    tester.register_test(config)
    tester.record_result(make_result("t1", "A", quality_score=0.9))
    tester.record_result(make_result("t1", "B", quality_score=0.4))
    summary = tester.get_summary("t1")
    assert "A" in summary.recommendation


# ─────────────────────────────────────────────
# ABTestSummary.get_variant_score
# ─────────────────────────────────────────────

def test_get_variant_score_existing_variant():
    summary = ABTestSummary(
        test_id="t1",
        variant_stats={"A": {"avg_score": 0.75}},
    )
    assert abs(summary.get_variant_score("A") - 0.75) < 1e-9


def test_get_variant_score_missing_variant_returns_zero():
    summary = ABTestSummary(test_id="t1", variant_stats={})
    assert summary.get_variant_score("X") == 0.0


# ─────────────────────────────────────────────
# list_tests
# ─────────────────────────────────────────────

def test_list_tests_contains_registered(tester):
    tester.register_test(make_config(test_id="alpha"))
    tester.register_test(make_config(test_id="beta"))
    tests = tester.list_tests()
    assert "alpha" in tests
    assert "beta" in tests


def test_list_tests_empty_initially(tester):
    assert tester.list_tests() == []


# ─────────────────────────────────────────────
# clear_results
# ─────────────────────────────────────────────

def test_clear_results_specific_test_id(tester):
    tester.record_result(make_result("t1", "A"))
    tester.record_result(make_result("t2", "A"))
    tester.clear_results("t1")
    assert tester.get_results_for_variant("t1", "A") == []
    assert len(tester.get_results_for_variant("t2", "A")) == 1


def test_clear_results_all(tester):
    tester.record_result(make_result("t1", "A"))
    tester.record_result(make_result("t2", "B"))
    tester.clear_results()
    assert tester.get_results_for_variant("t1", "A") == []
    assert tester.get_results_for_variant("t2", "B") == []


def test_clear_results_only_removes_matching_test(tester):
    tester.record_result(make_result("keep", "A"))
    tester.record_result(make_result("remove", "B"))
    tester.clear_results("remove")
    assert len(tester.get_results_for_variant("keep", "A")) == 1


# ─────────────────────────────────────────────
# Singleton get_ab_tester
# ─────────────────────────────────────────────

def test_get_ab_tester_returns_same_instance():
    inst1 = get_ab_tester()
    inst2 = get_ab_tester()
    assert inst1 is inst2


def test_get_ab_tester_is_prompt_ab_tester_instance():
    assert isinstance(get_ab_tester(), PromptABTester)


# ─────────────────────────────────────────────
# Meerdere onafhankelijke tests
# ─────────────────────────────────────────────

def test_multiple_tests_independent(tester):
    tester.register_test(make_config(test_id="test-alpha"))
    tester.register_test(make_config(test_id="test-beta"))
    tester.record_result(make_result("test-alpha", "A", quality_score=0.9))
    tester.record_result(make_result("test-beta", "B", quality_score=0.2))

    alpha_results = tester.get_results_for_variant("test-alpha", "A")
    beta_results = tester.get_results_for_variant("test-beta", "B")
    assert len(alpha_results) == 1
    assert len(beta_results) == 1
    assert alpha_results[0].quality_score == 0.9
    assert beta_results[0].quality_score == 0.2


def test_multiple_tests_summary_independent(tester):
    tester.register_test(make_config(test_id="t-x", min_samples=1))
    tester.register_test(make_config(test_id="t-y", min_samples=1))
    tester.record_result(make_result("t-x", "A", quality_score=0.9))
    tester.record_result(make_result("t-x", "B", quality_score=0.1))
    tester.record_result(make_result("t-y", "A", quality_score=0.2))
    tester.record_result(make_result("t-y", "B", quality_score=0.8))

    summary_x = tester.get_summary("t-x")
    summary_y = tester.get_summary("t-y")
    assert summary_x.winner == "A"
    assert summary_y.winner == "B"


# ─────────────────────────────────────────────
# ABTestResult dataclass
# ─────────────────────────────────────────────

def test_ab_test_result_defaults():
    r = ABTestResult(
        test_id="t1",
        variant_id="A",
        agent_name="agent",
        quality_score=0.5,
        latency_ms=50.0,
        success=True,
    )
    assert r.trace_id == ""
    assert r.metadata == {}


def test_ab_test_result_with_metadata():
    r = ABTestResult(
        test_id="t1",
        variant_id="B",
        agent_name="agent",
        quality_score=0.7,
        latency_ms=120.0,
        success=False,
        trace_id="trace-xyz",
        metadata={"model": "llama3"},
    )
    assert r.trace_id == "trace-xyz"
    assert r.metadata["model"] == "llama3"
    assert r.success is False
