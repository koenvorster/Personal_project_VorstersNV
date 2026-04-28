"""
VorstersNV Quality Monitor — aggregates agent metrics across the platform.
Tracks success rates, scores, latency, escalation, and costs per agent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AgentMetrics:
    agent_name: str
    capability: str
    total_runs: int
    success_rate: float           # 0.0–1.0
    avg_score: float              # 0.0–1.0
    avg_latency_ms: float
    error_rate: float             # 0.0–1.0
    human_escalation_rate: float  # 0.0–1.0
    cost_eur: float
    last_updated: str             # ISO datetime


@dataclass
class QualityReport:
    generated_at: str             # ISO datetime
    total_agents: int
    healthy_agents: int           # success_rate >= 0.8
    degraded_agents: int          # 0.6 <= success_rate < 0.8
    critical_agents: int          # success_rate < 0.6
    platform_avg_score: float
    platform_avg_latency_ms: float
    total_cost_eur: float
    agents: list[AgentMetrics]
    alerts: list[str]
    recommendations: list[str]


# ── Internal accumulator ──────────────────────────────────────────────────────

@dataclass
class _AgentAccumulator:
    agent_name: str
    capability: str
    total_runs: int = 0
    successful_runs: int = 0
    score_sum: float = 0.0
    latency_sum: float = 0.0
    error_runs: int = 0
    escalated_runs: int = 0
    cost_eur: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def record(
        self,
        success: bool,
        score: float,
        latency_ms: float,
        cost_eur: float,
        human_escalated: bool,
    ) -> None:
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.error_runs += 1
        self.score_sum += score
        self.latency_sum += latency_ms
        self.cost_eur += cost_eur
        if human_escalated:
            self.escalated_runs += 1
        self.last_updated = datetime.utcnow().isoformat()

    def to_metrics(self) -> AgentMetrics:
        n = self.total_runs
        return AgentMetrics(
            agent_name=self.agent_name,
            capability=self.capability,
            total_runs=n,
            success_rate=self.successful_runs / n if n else 0.0,
            avg_score=self.score_sum / n if n else 0.0,
            avg_latency_ms=self.latency_sum / n if n else 0.0,
            error_rate=self.error_runs / n if n else 0.0,
            human_escalation_rate=self.escalated_runs / n if n else 0.0,
            cost_eur=self.cost_eur,
            last_updated=self.last_updated,
        )


# ── Alert & recommendation helpers ───────────────────────────────────────────

_ALERT_SUCCESS_CRITICAL = 0.6
_ALERT_SUCCESS_DEGRADED = 0.8
_ALERT_SCORE_LOW = 0.7
_ALERT_ESCALATION_HIGH = 0.3
_ALERT_LATENCY_SLOW = 5000.0


def _alerts_for(m: AgentMetrics) -> list[str]:
    alerts: list[str] = []
    if m.success_rate < _ALERT_SUCCESS_CRITICAL:
        alerts.append(f"CRITICAL: {m.agent_name} success_rate={m.success_rate:.2f} (< 0.6)")
    elif m.success_rate < _ALERT_SUCCESS_DEGRADED:
        alerts.append(f"DEGRADED: {m.agent_name} success_rate={m.success_rate:.2f} (< 0.8)")
    if m.avg_score < _ALERT_SCORE_LOW:
        alerts.append(f"LOW_QUALITY: {m.agent_name} avg_score={m.avg_score:.2f} (< 0.7)")
    if m.human_escalation_rate > _ALERT_ESCALATION_HIGH:
        alerts.append(
            f"HIGH_ESCALATION: {m.agent_name} escalation_rate={m.human_escalation_rate:.2f} (> 0.3)"
        )
    if m.avg_latency_ms > _ALERT_LATENCY_SLOW:
        alerts.append(f"SLOW: {m.agent_name} avg_latency_ms={m.avg_latency_ms:.0f} (> 5000)")
    return alerts


def _recommendations_for(m: AgentMetrics) -> list[str]:
    recs: list[str] = []
    if m.success_rate < _ALERT_SUCCESS_CRITICAL:
        recs.append(f"Consider switching model to claude-sonnet-4-5 for {m.agent_name}")
    if m.avg_score < _ALERT_SCORE_LOW:
        recs.append(f"Run eval hierarchy to identify quality gaps for {m.agent_name}")
    if m.human_escalation_rate > _ALERT_ESCALATION_HIGH:
        recs.append(f"Review HITL policy thresholds for {m.agent_name}")
    if m.avg_latency_ms > _ALERT_LATENCY_SLOW:
        recs.append(f"Enable caching or reduce context size for {m.agent_name}")
    return recs


# ── QualityMonitor ────────────────────────────────────────────────────────────

class QualityMonitor:
    """Aggregates quality metrics for all agents on the platform."""

    def __init__(self) -> None:
        self._agents: dict[str, _AgentAccumulator] = {}

    def record_run(
        self,
        agent_name: str,
        capability: str,
        success: bool,
        score: float,
        latency_ms: float,
        cost_eur: float,
        human_escalated: bool,
    ) -> None:
        if agent_name not in self._agents:
            self._agents[agent_name] = _AgentAccumulator(
                agent_name=agent_name, capability=capability
            )
        self._agents[agent_name].record(success, score, latency_ms, cost_eur, human_escalated)

    def get_agent_metrics(self, agent_name: str) -> Optional[AgentMetrics]:
        acc = self._agents.get(agent_name)
        return acc.to_metrics() if acc else None

    def get_alerts(self) -> list[str]:
        alerts: list[str] = []
        for acc in self._agents.values():
            alerts.extend(_alerts_for(acc.to_metrics()))
        return alerts

    def get_recommendations(self) -> list[str]:
        recs: list[str] = []
        for acc in self._agents.values():
            recs.extend(_recommendations_for(acc.to_metrics()))
        return recs

    def generate_report(self) -> QualityReport:
        all_metrics = [acc.to_metrics() for acc in self._agents.values()]

        healthy = sum(1 for m in all_metrics if m.success_rate >= _ALERT_SUCCESS_DEGRADED)
        degraded = sum(
            1 for m in all_metrics
            if _ALERT_SUCCESS_CRITICAL <= m.success_rate < _ALERT_SUCCESS_DEGRADED
        )
        critical = sum(1 for m in all_metrics if m.success_rate < _ALERT_SUCCESS_CRITICAL)

        platform_avg_score = (
            sum(m.avg_score for m in all_metrics) / len(all_metrics) if all_metrics else 0.0
        )
        platform_avg_latency = (
            sum(m.avg_latency_ms for m in all_metrics) / len(all_metrics) if all_metrics else 0.0
        )
        total_cost = sum(m.cost_eur for m in all_metrics)

        alerts: list[str] = []
        recs: list[str] = []
        for m in all_metrics:
            alerts.extend(_alerts_for(m))
            recs.extend(_recommendations_for(m))

        return QualityReport(
            generated_at=datetime.utcnow().isoformat(),
            total_agents=len(all_metrics),
            healthy_agents=healthy,
            degraded_agents=degraded,
            critical_agents=critical,
            platform_avg_score=platform_avg_score,
            platform_avg_latency_ms=platform_avg_latency,
            total_cost_eur=total_cost,
            agents=all_metrics,
            alerts=alerts,
            recommendations=recs,
        )

    def reset(self, agent_name: Optional[str] = None) -> None:
        if agent_name is None:
            self._agents.clear()
        else:
            self._agents.pop(agent_name, None)


# ── Singleton ─────────────────────────────────────────────────────────────────

_monitor: Optional[QualityMonitor] = None


def get_quality_monitor() -> QualityMonitor:
    global _monitor
    if _monitor is None:
        _monitor = QualityMonitor()
    return _monitor
