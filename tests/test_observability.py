"""
Tests voor VorstersNV Observability Layer 3 — Business Metrics (w4-01).
3-tier: N1 (request) + N2 (agent) + N3 (business KPIs).
"""
from __future__ import annotations

import pytest

from ollama.observability import (
    MetricTier,
    N1RequestMetric,
    N2AgentMetric,
    N3BusinessMetric,
    ObservabilityCollector,
    get_observability_collector,
)


def _fresh() -> ObservabilityCollector:
    """Return a fresh, empty collector for each test."""
    c = ObservabilityCollector()
    return c


# ─────────────────────────────────────────────────────────
# MetricTier enum
# ─────────────────────────────────────────────────────────

class TestMetricTier:
    def test_n1_value(self):
        assert MetricTier.N1_REQUEST.value == "n1_request"

    def test_n2_value(self):
        assert MetricTier.N2_AGENT.value == "n2_agent"

    def test_n3_value(self):
        assert MetricTier.N3_BUSINESS.value == "n3_business"


# ─────────────────────────────────────────────────────────
# N1 — Request metrics
# ─────────────────────────────────────────────────────────

class TestN1RequestMetrics:
    def test_record_request_stored(self):
        c = _fresh()
        c.record_request("t1", "llama3", 100, 50, 350.0, "fraud-detection")
        assert len(c._n1) == 1

    def test_get_avg_latency_single(self):
        c = _fresh()
        c.record_request("t1", "llama3", 100, 50, 400.0, "fraud-detection")
        assert c.get_avg_latency() == pytest.approx(400.0)

    def test_get_avg_latency_multiple(self):
        c = _fresh()
        c.record_request("t1", "llama3", 50, 25, 200.0, "fraud-detection")
        c.record_request("t2", "llama3", 50, 25, 400.0, "fraud-detection")
        assert c.get_avg_latency() == pytest.approx(300.0)

    def test_get_avg_latency_per_capability(self):
        c = _fresh()
        c.record_request("t1", "llama3", 50, 25, 100.0, "fraud-detection")
        c.record_request("t2", "llama3", 50, 25, 900.0, "onboarding")
        assert c.get_avg_latency("fraud-detection") == pytest.approx(100.0)
        assert c.get_avg_latency("onboarding") == pytest.approx(900.0)

    def test_get_avg_latency_empty_returns_zero(self):
        c = _fresh()
        assert c.get_avg_latency() == 0.0

    def test_get_avg_latency_unknown_capability_returns_zero(self):
        c = _fresh()
        c.record_request("t1", "llama3", 10, 5, 100.0, "fraud-detection")
        assert c.get_avg_latency("onboarding") == 0.0

    def test_get_total_tokens_correct(self):
        c = _fresh()
        c.record_request("t1", "llama3", 100, 50, 100.0, "fraud-detection")
        c.record_request("t2", "llama3", 200, 80, 100.0, "fraud-detection")
        assert c.get_total_tokens() == 430

    def test_get_total_tokens_per_capability(self):
        c = _fresh()
        c.record_request("t1", "llama3", 100, 50, 100.0, "fraud-detection")
        c.record_request("t2", "llama3", 200, 80, 100.0, "onboarding")
        assert c.get_total_tokens("fraud-detection") == 150
        assert c.get_total_tokens("onboarding") == 280

    def test_get_total_tokens_empty_returns_zero(self):
        c = _fresh()
        assert c.get_total_tokens() == 0

    def test_n1_metric_fields(self):
        m = N1RequestMetric("t1", "llama3", 10, 5, 100.0, "fraud-detection")
        assert m.trace_id == "t1"
        assert m.model == "llama3"
        assert m.input_tokens == 10
        assert m.output_tokens == 5
        assert m.latency_ms == 100.0
        assert m.capability == "fraud-detection"
        assert m.timestamp is not None


# ─────────────────────────────────────────────────────────
# N2 — Agent metrics
# ─────────────────────────────────────────────────────────

class TestN2AgentMetrics:
    def test_record_agent_stored(self):
        c = _fresh()
        c.record_agent("t1", "fraud_agent", "fraud-detection", "APPROVED")
        assert len(c._n2) == 1

    def test_get_escalation_rate_all_escalated(self):
        c = _fresh()
        c.record_agent("t1", "agent", "fraud-detection", "ESCALATED", hitl_escalation=True)
        c.record_agent("t2", "agent", "fraud-detection", "ESCALATED", hitl_escalation=True)
        assert c.get_escalation_rate() == pytest.approx(1.0)

    def test_get_escalation_rate_partial(self):
        c = _fresh()
        c.record_agent("t1", "agent", "fraud-detection", "APPROVED", hitl_escalation=False)
        c.record_agent("t2", "agent", "fraud-detection", "ESCALATED", hitl_escalation=True)
        assert c.get_escalation_rate() == pytest.approx(0.5)

    def test_get_escalation_rate_empty_returns_zero(self):
        c = _fresh()
        assert c.get_escalation_rate() == 0.0

    def test_get_escalation_rate_per_capability(self):
        c = _fresh()
        c.record_agent("t1", "agent", "fraud-detection", "ESCALATED", hitl_escalation=True)
        c.record_agent("t2", "agent", "onboarding", "APPROVED", hitl_escalation=False)
        assert c.get_escalation_rate("fraud-detection") == pytest.approx(1.0)
        assert c.get_escalation_rate("onboarding") == pytest.approx(0.0)

    def test_get_fallback_rate_correct(self):
        c = _fresh()
        c.record_agent("t1", "agent", "cap", "APPROVED", fallback_triggered=True)
        c.record_agent("t2", "agent", "cap", "APPROVED", fallback_triggered=False)
        c.record_agent("t3", "agent", "cap", "APPROVED", fallback_triggered=True)
        assert c.get_fallback_rate() == pytest.approx(2 / 3)

    def test_get_fallback_rate_empty_returns_zero(self):
        c = _fresh()
        assert c.get_fallback_rate() == 0.0

    def test_get_fallback_rate_per_capability(self):
        c = _fresh()
        c.record_agent("t1", "agent", "fraud-detection", "APPROVED", fallback_triggered=True)
        c.record_agent("t2", "agent", "onboarding", "APPROVED", fallback_triggered=False)
        assert c.get_fallback_rate("fraud-detection") == pytest.approx(1.0)
        assert c.get_fallback_rate("onboarding") == pytest.approx(0.0)

    def test_n2_metric_default_fields(self):
        m = N2AgentMetric("t1", "agent", "cap", "APPROVED")
        assert m.fallback_triggered is False
        assert m.hitl_escalation is False
        assert m.quality_gate_failed is False


# ─────────────────────────────────────────────────────────
# N3 — Business metrics
# ─────────────────────────────────────────────────────────

class TestN3BusinessMetrics:
    def test_record_business_metric_stored(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", fraud_accuracy=0.95))
        assert len(c._n3) == 1

    def test_get_fraud_accuracy_single(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", fraud_accuracy=0.92))
        assert c.get_fraud_accuracy() == pytest.approx(0.92)

    def test_get_fraud_accuracy_average(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", fraud_accuracy=0.80))
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", fraud_accuracy=0.90))
        assert c.get_fraud_accuracy() == pytest.approx(0.85)

    def test_get_fraud_accuracy_none_when_empty(self):
        c = _fresh()
        assert c.get_fraud_accuracy() is None

    def test_get_fraud_accuracy_ignores_other_capabilities(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="onboarding", fraud_accuracy=0.50))
        assert c.get_fraud_accuracy("fraud-detection") is None

    def test_get_cost_per_outcome_correct(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", cost_per_outcome_eur=0.10))
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", cost_per_outcome_eur=0.20))
        assert c.get_cost_per_outcome() == pytest.approx(0.15)

    def test_get_cost_per_outcome_none_when_empty(self):
        c = _fresh()
        assert c.get_cost_per_outcome() is None

    def test_get_cost_per_outcome_per_capability(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", cost_per_outcome_eur=0.10))
        c.record_business_metric(N3BusinessMetric(capability="onboarding", cost_per_outcome_eur=0.50))
        assert c.get_cost_per_outcome("fraud-detection") == pytest.approx(0.10)
        assert c.get_cost_per_outcome("onboarding") == pytest.approx(0.50)

    def test_n3_optional_fields_default_none(self):
        m = N3BusinessMetric(capability="fraud-detection")
        assert m.fraud_accuracy is None
        assert m.false_positive_rate is None
        assert m.onboarding_success_rate is None
        assert m.human_escalation_rate is None
        assert m.cost_per_outcome_eur is None

    def test_n3_all_optional_fields_set(self):
        m = N3BusinessMetric(
            capability="fraud-detection",
            fraud_accuracy=0.95,
            false_positive_rate=0.02,
            onboarding_success_rate=0.88,
            human_escalation_rate=0.05,
            cost_per_outcome_eur=0.12,
        )
        assert m.fraud_accuracy == 0.95
        assert m.false_positive_rate == 0.02
        assert m.onboarding_success_rate == 0.88
        assert m.human_escalation_rate == 0.05
        assert m.cost_per_outcome_eur == 0.12


# ─────────────────────────────────────────────────────────
# Dashboard snapshot
# ─────────────────────────────────────────────────────────

class TestDashboardSnapshot:
    def test_snapshot_contains_all_tiers(self):
        c = _fresh()
        snap = c.get_dashboard_snapshot()
        assert "n1_request" in snap
        assert "n2_agent" in snap
        assert "n3_business" in snap

    def test_snapshot_n1_total_requests(self):
        c = _fresh()
        c.record_request("t1", "llama3", 10, 5, 100.0, "fraud-detection")
        c.record_request("t2", "llama3", 10, 5, 200.0, "fraud-detection")
        snap = c.get_dashboard_snapshot()
        assert snap["n1_request"]["total_requests"] == 2

    def test_snapshot_n1_avg_latency(self):
        c = _fresh()
        c.record_request("t1", "llama3", 10, 5, 100.0, "cap")
        c.record_request("t2", "llama3", 10, 5, 300.0, "cap")
        snap = c.get_dashboard_snapshot()
        assert snap["n1_request"]["avg_latency_ms"] == pytest.approx(200.0)

    def test_snapshot_n2_escalation_rate(self):
        c = _fresh()
        c.record_agent("t1", "agent", "cap", "APPROVED", hitl_escalation=True)
        c.record_agent("t2", "agent", "cap", "APPROVED", hitl_escalation=False)
        snap = c.get_dashboard_snapshot()
        assert snap["n2_agent"]["escalation_rate"] == pytest.approx(0.5)

    def test_snapshot_n2_approvals_and_rejections(self):
        c = _fresh()
        c.record_agent("t1", "agent", "cap", "APPROVED")
        c.record_agent("t2", "agent", "cap", "REJECTED")
        c.record_agent("t3", "agent", "cap", "APPROVED")
        snap = c.get_dashboard_snapshot()
        assert snap["n2_agent"]["approvals"] == 2
        assert snap["n2_agent"]["rejections"] == 1

    def test_snapshot_n3_fraud_accuracy(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", fraud_accuracy=0.90))
        snap = c.get_dashboard_snapshot()
        assert snap["n3_business"]["fraud_accuracy"] == pytest.approx(0.90)

    def test_snapshot_n3_records_count(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection"))
        c.record_business_metric(N3BusinessMetric(capability="onboarding"))
        snap = c.get_dashboard_snapshot()
        assert snap["n3_business"]["n3_records"] == 2

    def test_snapshot_empty_collector(self):
        c = _fresh()
        snap = c.get_dashboard_snapshot()
        assert snap["n1_request"]["total_requests"] == 0
        assert snap["n2_agent"]["total_agent_calls"] == 0
        assert snap["n3_business"]["n3_records"] == 0


# ─────────────────────────────────────────────────────────
# clear()
# ─────────────────────────────────────────────────────────

class TestClear:
    def test_clear_resets_all_tiers(self):
        c = _fresh()
        c.record_request("t1", "llama3", 10, 5, 100.0, "cap")
        c.record_agent("t1", "agent", "cap", "APPROVED")
        c.record_business_metric(N3BusinessMetric(capability="cap", fraud_accuracy=0.9))
        c.clear()
        assert len(c._n1) == 0
        assert len(c._n2) == 0
        assert len(c._n3) == 0

    def test_clear_avg_latency_returns_zero_after(self):
        c = _fresh()
        c.record_request("t1", "llama3", 10, 5, 500.0, "cap")
        c.clear()
        assert c.get_avg_latency() == 0.0

    def test_clear_fraud_accuracy_returns_none_after(self):
        c = _fresh()
        c.record_business_metric(N3BusinessMetric(capability="fraud-detection", fraud_accuracy=0.9))
        c.clear()
        assert c.get_fraud_accuracy() is None


# ─────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_observability_collector_singleton(self):
        c1 = get_observability_collector()
        c2 = get_observability_collector()
        assert c1 is c2

    def test_singleton_is_observability_collector(self):
        collector = get_observability_collector()
        assert isinstance(collector, ObservabilityCollector)
