"""
Tests for ollama/quality_monitor.py — QualityMonitor, AgentMetrics, QualityReport.
"""
from __future__ import annotations

import pytest

from ollama.quality_monitor import (
    AgentMetrics,
    QualityMonitor,
    QualityReport,
    get_quality_monitor,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh() -> QualityMonitor:
    return QualityMonitor()


def _record(
    m: QualityMonitor,
    agent: str = "agent-a",
    capability: str = "fraud-detection",
    success: bool = True,
    score: float = 0.9,
    latency_ms: float = 500.0,
    cost_eur: float = 0.01,
    human_escalated: bool = False,
) -> None:
    m.record_run(agent, capability, success, score, latency_ms, cost_eur, human_escalated)


# ── record_run() & get_agent_metrics() ───────────────────────────────────────

class TestRecordRun:
    def test_first_run_creates_entry(self):
        m = fresh()
        _record(m)
        assert m.get_agent_metrics("agent-a") is not None

    def test_total_runs_increments(self):
        m = fresh()
        _record(m)
        _record(m)
        assert m.get_agent_metrics("agent-a").total_runs == 2

    def test_success_rate_all_success(self):
        m = fresh()
        _record(m, success=True)
        _record(m, success=True)
        assert m.get_agent_metrics("agent-a").success_rate == pytest.approx(1.0)

    def test_success_rate_all_failure(self):
        m = fresh()
        _record(m, success=False)
        _record(m, success=False)
        assert m.get_agent_metrics("agent-a").success_rate == pytest.approx(0.0)

    def test_success_rate_mixed(self):
        m = fresh()
        _record(m, success=True)
        _record(m, success=False)
        _record(m, success=True)
        _record(m, success=True)
        assert m.get_agent_metrics("agent-a").success_rate == pytest.approx(0.75)

    def test_avg_score_single(self):
        m = fresh()
        _record(m, score=0.8)
        assert m.get_agent_metrics("agent-a").avg_score == pytest.approx(0.8)

    def test_avg_score_multiple(self):
        m = fresh()
        _record(m, score=0.6)
        _record(m, score=1.0)
        assert m.get_agent_metrics("agent-a").avg_score == pytest.approx(0.8)

    def test_avg_latency_correct(self):
        m = fresh()
        _record(m, latency_ms=200.0)
        _record(m, latency_ms=400.0)
        assert m.get_agent_metrics("agent-a").avg_latency_ms == pytest.approx(300.0)

    def test_error_rate_correct(self):
        m = fresh()
        _record(m, success=False)
        _record(m, success=True)
        assert m.get_agent_metrics("agent-a").error_rate == pytest.approx(0.5)

    def test_human_escalation_rate_correct(self):
        m = fresh()
        _record(m, human_escalated=True)
        _record(m, human_escalated=False)
        assert m.get_agent_metrics("agent-a").human_escalation_rate == pytest.approx(0.5)

    def test_cost_accumulates(self):
        m = fresh()
        _record(m, cost_eur=0.05)
        _record(m, cost_eur=0.10)
        assert m.get_agent_metrics("agent-a").cost_eur == pytest.approx(0.15)

    def test_capability_stored(self):
        m = fresh()
        _record(m, capability="order-validation")
        assert m.get_agent_metrics("agent-a").capability == "order-validation"

    def test_agent_name_stored(self):
        m = fresh()
        _record(m, agent="my-agent")
        assert m.get_agent_metrics("my-agent").agent_name == "my-agent"

    def test_last_updated_is_iso_string(self):
        m = fresh()
        _record(m)
        last = m.get_agent_metrics("agent-a").last_updated
        assert isinstance(last, str)
        assert "T" in last  # ISO datetime contains T

    def test_multiple_agents_tracked_independently(self):
        m = fresh()
        _record(m, agent="agent-a", score=0.9)
        _record(m, agent="agent-b", score=0.5)
        assert m.get_agent_metrics("agent-a").avg_score == pytest.approx(0.9)
        assert m.get_agent_metrics("agent-b").avg_score == pytest.approx(0.5)

    def test_unknown_agent_returns_none(self):
        m = fresh()
        assert m.get_agent_metrics("nonexistent") is None


# ── Alert generation ──────────────────────────────────────────────────────────

class TestAlerts:
    def test_no_alerts_healthy_agent(self):
        m = fresh()
        for _ in range(10):
            _record(m, success=True, score=0.9, latency_ms=1000.0, human_escalated=False)
        assert m.get_alerts() == []

    def test_critical_alert_below_0_6(self):
        m = fresh()
        for _ in range(5):
            _record(m, success=False, score=0.9, latency_ms=500.0)
        for _ in range(5):
            _record(m, success=True, score=0.9, latency_ms=500.0)
        # success_rate = 0.5 → CRITICAL
        alerts = m.get_alerts()
        assert any("CRITICAL" in a for a in alerts)

    def test_degraded_alert_between_0_6_and_0_8(self):
        m = fresh()
        # 7 success / 10 = 0.7 → DEGRADED
        for _ in range(7):
            _record(m, success=True, score=0.9, latency_ms=500.0)
        for _ in range(3):
            _record(m, success=False, score=0.9, latency_ms=500.0)
        alerts = m.get_alerts()
        assert any("DEGRADED" in a for a in alerts)

    def test_no_critical_when_exactly_0_6(self):
        m = fresh()
        for _ in range(6):
            _record(m, success=True, score=0.9, latency_ms=500.0)
        for _ in range(4):
            _record(m, success=False, score=0.9, latency_ms=500.0)
        # success_rate = 0.6 → DEGRADED (not CRITICAL)
        alerts = m.get_alerts()
        assert not any("CRITICAL" in a for a in alerts)
        assert any("DEGRADED" in a for a in alerts)

    def test_no_degraded_when_exactly_0_8(self):
        m = fresh()
        for _ in range(8):
            _record(m, success=True, score=0.9, latency_ms=500.0)
        for _ in range(2):
            _record(m, success=False, score=0.9, latency_ms=500.0)
        # success_rate = 0.8 → healthy (no DEGRADED)
        alerts = m.get_alerts()
        assert not any("DEGRADED" in a for a in alerts)

    def test_low_quality_alert_below_0_7(self):
        m = fresh()
        _record(m, success=True, score=0.5)
        alerts = m.get_alerts()
        assert any("LOW_QUALITY" in a for a in alerts)

    def test_no_low_quality_at_0_7(self):
        m = fresh()
        _record(m, success=True, score=0.7)
        alerts = m.get_alerts()
        assert not any("LOW_QUALITY" in a for a in alerts)

    def test_high_escalation_alert_above_0_3(self):
        m = fresh()
        for _ in range(4):
            _record(m, success=True, score=0.9, human_escalated=True)
        for _ in range(6):
            _record(m, success=True, score=0.9, human_escalated=False)
        # escalation_rate = 0.4 → HIGH_ESCALATION
        alerts = m.get_alerts()
        assert any("HIGH_ESCALATION" in a for a in alerts)

    def test_no_high_escalation_at_exactly_0_3(self):
        m = fresh()
        for _ in range(3):
            _record(m, success=True, score=0.9, human_escalated=True)
        for _ in range(7):
            _record(m, success=True, score=0.9, human_escalated=False)
        # escalation_rate = 0.3 → no alert
        alerts = m.get_alerts()
        assert not any("HIGH_ESCALATION" in a for a in alerts)

    def test_slow_alert_above_5000ms(self):
        m = fresh()
        _record(m, success=True, score=0.9, latency_ms=6000.0)
        alerts = m.get_alerts()
        assert any("SLOW" in a for a in alerts)

    def test_no_slow_alert_at_5000ms(self):
        m = fresh()
        _record(m, success=True, score=0.9, latency_ms=5000.0)
        alerts = m.get_alerts()
        assert not any("SLOW" in a for a in alerts)

    def test_multiple_alert_types_combined(self):
        m = fresh()
        # success_rate=0.5 (CRITICAL), score=0.5 (LOW_QUALITY), latency=6000 (SLOW), escalation=0.5 (HIGH_ESCALATION)
        for _ in range(5):
            _record(m, success=True, score=0.5, latency_ms=6000.0, human_escalated=True)
        for _ in range(5):
            _record(m, success=False, score=0.5, latency_ms=6000.0, human_escalated=False)
        alerts = m.get_alerts()
        alert_text = " ".join(alerts)
        assert "CRITICAL" in alert_text
        assert "LOW_QUALITY" in alert_text
        assert "SLOW" in alert_text
        assert "HIGH_ESCALATION" in alert_text

    def test_alert_contains_agent_name(self):
        m = fresh()
        _record(m, agent="my-special-agent", success=False, score=0.3)
        alerts = m.get_alerts()
        assert any("my-special-agent" in a for a in alerts)


# ── Recommendations ───────────────────────────────────────────────────────────

class TestRecommendations:
    def test_no_recs_for_healthy_agent(self):
        m = fresh()
        for _ in range(10):
            _record(m, success=True, score=0.9, latency_ms=1000.0, human_escalated=False)
        assert m.get_recommendations() == []

    def test_critical_triggers_model_switch_rec(self):
        m = fresh()
        for _ in range(10):
            _record(m, agent="bad-agent", success=False, score=0.9)
        recs = m.get_recommendations()
        assert any("claude-sonnet-4-5" in r and "bad-agent" in r for r in recs)

    def test_low_quality_triggers_eval_hierarchy_rec(self):
        m = fresh()
        _record(m, agent="low-agent", score=0.5)
        recs = m.get_recommendations()
        assert any("eval hierarchy" in r and "low-agent" in r for r in recs)

    def test_high_escalation_triggers_hitl_rec(self):
        m = fresh()
        for _ in range(5):
            _record(m, agent="esc-agent", human_escalated=True)
        recs = m.get_recommendations()
        assert any("HITL" in r and "esc-agent" in r for r in recs)

    def test_slow_triggers_caching_rec(self):
        m = fresh()
        _record(m, agent="slow-agent", latency_ms=6000.0)
        recs = m.get_recommendations()
        assert any("caching" in r and "slow-agent" in r for r in recs)

    def test_degraded_does_not_trigger_model_switch(self):
        m = fresh()
        for _ in range(7):
            _record(m, success=True, score=0.9)
        for _ in range(3):
            _record(m, success=False, score=0.9)
        # success_rate=0.7 → DEGRADED, not CRITICAL → no model-switch rec
        recs = m.get_recommendations()
        assert not any("claude-sonnet-4-5" in r for r in recs)


# ── generate_report() ─────────────────────────────────────────────────────────

class TestGenerateReport:
    def test_report_is_quality_report(self):
        m = fresh()
        assert isinstance(m.generate_report(), QualityReport)

    def test_report_empty_monitor(self):
        m = fresh()
        report = m.generate_report()
        assert report.total_agents == 0
        assert report.healthy_agents == 0
        assert report.degraded_agents == 0
        assert report.critical_agents == 0
        assert report.platform_avg_score == 0.0
        assert report.platform_avg_latency_ms == 0.0
        assert report.total_cost_eur == 0.0
        assert report.agents == []
        assert report.alerts == []
        assert report.recommendations == []

    def test_report_total_agents_count(self):
        m = fresh()
        _record(m, agent="a1")
        _record(m, agent="a2")
        assert m.generate_report().total_agents == 2

    def test_report_healthy_count(self):
        m = fresh()
        for _ in range(10):
            _record(m, agent="healthy", success=True, score=0.9)
        report = m.generate_report()
        assert report.healthy_agents == 1
        assert report.degraded_agents == 0
        assert report.critical_agents == 0

    def test_report_degraded_count(self):
        m = fresh()
        for _ in range(7):
            _record(m, agent="deg", success=True)
        for _ in range(3):
            _record(m, agent="deg", success=False)
        report = m.generate_report()
        assert report.degraded_agents == 1
        assert report.healthy_agents == 0
        assert report.critical_agents == 0

    def test_report_critical_count(self):
        m = fresh()
        for _ in range(10):
            _record(m, agent="crit", success=False)
        report = m.generate_report()
        assert report.critical_agents == 1
        assert report.healthy_agents == 0
        assert report.degraded_agents == 0

    def test_report_platform_avg_score(self):
        m = fresh()
        for _ in range(5):
            _record(m, agent="a1", score=0.8)
        for _ in range(5):
            _record(m, agent="a2", score=0.6)
        # a1.avg_score=0.8, a2.avg_score=0.6 → platform avg=0.7
        assert m.generate_report().platform_avg_score == pytest.approx(0.7)

    def test_report_total_cost(self):
        m = fresh()
        _record(m, agent="a1", cost_eur=1.0)
        _record(m, agent="a2", cost_eur=2.0)
        assert m.generate_report().total_cost_eur == pytest.approx(3.0)

    def test_report_generated_at_is_str(self):
        m = fresh()
        report = m.generate_report()
        assert isinstance(report.generated_at, str)

    def test_report_agents_list_populated(self):
        m = fresh()
        _record(m, agent="x")
        report = m.generate_report()
        assert len(report.agents) == 1
        assert isinstance(report.agents[0], AgentMetrics)

    def test_report_alerts_propagated(self):
        m = fresh()
        for _ in range(10):
            _record(m, success=False, score=0.3, latency_ms=6000.0)
        report = m.generate_report()
        assert len(report.alerts) > 0

    def test_report_recommendations_propagated(self):
        m = fresh()
        for _ in range(10):
            _record(m, success=False, score=0.3)
        report = m.generate_report()
        assert len(report.recommendations) > 0

    def test_report_mixed_health(self):
        m = fresh()
        for _ in range(10):
            _record(m, agent="healthy", success=True, score=0.9)
        for _ in range(7):
            _record(m, agent="degraded", success=True, score=0.9)
        for _ in range(3):
            _record(m, agent="degraded", success=False, score=0.9)
        for _ in range(10):
            _record(m, agent="critical", success=False, score=0.9)
        report = m.generate_report()
        assert report.total_agents == 3
        assert report.healthy_agents == 1
        assert report.degraded_agents == 1
        assert report.critical_agents == 1


# ── reset() ───────────────────────────────────────────────────────────────────

class TestReset:
    def test_reset_all_clears_everything(self):
        m = fresh()
        _record(m, agent="a1")
        _record(m, agent="a2")
        m.reset()
        assert m.get_agent_metrics("a1") is None
        assert m.get_agent_metrics("a2") is None

    def test_reset_all_report_empty(self):
        m = fresh()
        _record(m)
        m.reset()
        assert m.generate_report().total_agents == 0

    def test_reset_specific_agent(self):
        m = fresh()
        _record(m, agent="a1")
        _record(m, agent="a2")
        m.reset("a1")
        assert m.get_agent_metrics("a1") is None
        assert m.get_agent_metrics("a2") is not None

    def test_reset_specific_leaves_others_intact(self):
        m = fresh()
        for _ in range(5):
            _record(m, agent="keep", score=0.9)
        _record(m, agent="remove")
        m.reset("remove")
        metrics = m.get_agent_metrics("keep")
        assert metrics is not None
        assert metrics.total_runs == 5

    def test_reset_nonexistent_agent_no_error(self):
        m = fresh()
        m.reset("ghost")  # should not raise

    def test_reset_then_re_record(self):
        m = fresh()
        _record(m, agent="a", score=0.5)
        m.reset("a")
        _record(m, agent="a", score=0.9)
        assert m.get_agent_metrics("a").avg_score == pytest.approx(0.9)


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_quality_monitor_returns_same_instance(self):
        m1 = get_quality_monitor()
        m2 = get_quality_monitor()
        assert m1 is m2

    def test_singleton_is_quality_monitor(self):
        assert isinstance(get_quality_monitor(), QualityMonitor)

    def test_singleton_state_persists(self):
        m = get_quality_monitor()
        # Record to singleton; retrieve via a fresh call — same object
        before = m.generate_report().total_agents
        _record(m, agent="__singleton_test_agent__")
        after = get_quality_monitor().generate_report().total_agents
        assert after == before + 1
        m.reset("__singleton_test_agent__")  # cleanup
