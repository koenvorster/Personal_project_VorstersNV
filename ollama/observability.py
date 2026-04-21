"""
VorstersNV Observability Layer 3 — Business Metrics (w4-01)
3-tier observability: N1 (request) + N2 (agent) + N3 (business KPIs).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class MetricTier(Enum):
    N1_REQUEST = "n1_request"    # tokens, latency, model
    N2_AGENT = "n2_agent"        # agent.name, capability, fallback, verdict
    N3_BUSINESS = "n3_business"  # fraud_accuracy, cost_per_outcome, etc.


@dataclass
class N1RequestMetric:
    trace_id: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    capability: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class N2AgentMetric:
    trace_id: str
    agent_name: str
    capability: str
    verdict: str  # APPROVED | REJECTED | ESCALATED | NEEDS_REVIEW
    fallback_triggered: bool = False
    hitl_escalation: bool = False
    quality_gate_failed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class N3BusinessMetric:
    """Business-level KPI snapshot."""
    capability: str
    fraud_accuracy: Optional[float] = None        # TP / (TP + FP + FN)
    false_positive_rate: Optional[float] = None   # FP / (FP + TN)
    onboarding_success_rate: Optional[float] = None
    human_escalation_rate: Optional[float] = None
    cost_per_outcome_eur: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ObservabilityCollector:
    """3-tier observability collector: N1 (request) + N2 (agent) + N3 (business)."""

    def __init__(self):
        self._n1: list[N1RequestMetric] = []
        self._n2: list[N2AgentMetric] = []
        self._n3: list[N3BusinessMetric] = []

    # --- N1 ---
    def record_request(
        self,
        trace_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        capability: str,
    ):
        self._n1.append(
            N1RequestMetric(trace_id, model, input_tokens, output_tokens, latency_ms, capability)
        )

    def get_avg_latency(self, capability: Optional[str] = None) -> float:
        records = [r for r in self._n1 if capability is None or r.capability == capability]
        if not records:
            return 0.0
        return sum(r.latency_ms for r in records) / len(records)

    def get_total_tokens(self, capability: Optional[str] = None) -> int:
        records = [r for r in self._n1 if capability is None or r.capability == capability]
        return sum(r.input_tokens + r.output_tokens for r in records)

    # --- N2 ---
    def record_agent(
        self,
        trace_id: str,
        agent_name: str,
        capability: str,
        verdict: str,
        fallback_triggered: bool = False,
        hitl_escalation: bool = False,
        quality_gate_failed: bool = False,
    ):
        self._n2.append(
            N2AgentMetric(
                trace_id, agent_name, capability, verdict,
                fallback_triggered, hitl_escalation, quality_gate_failed,
            )
        )

    def get_escalation_rate(self, capability: Optional[str] = None) -> float:
        records = [r for r in self._n2 if capability is None or r.capability == capability]
        if not records:
            return 0.0
        escalated = sum(1 for r in records if r.hitl_escalation)
        return escalated / len(records)

    def get_fallback_rate(self, capability: Optional[str] = None) -> float:
        records = [r for r in self._n2 if capability is None or r.capability == capability]
        if not records:
            return 0.0
        fallbacks = sum(1 for r in records if r.fallback_triggered)
        return fallbacks / len(records)

    # --- N3 ---
    def record_business_metric(self, metric: N3BusinessMetric):
        self._n3.append(metric)

    def get_fraud_accuracy(self, capability: str = "fraud-detection") -> Optional[float]:
        relevant = [m for m in self._n3 if m.capability == capability and m.fraud_accuracy is not None]
        if not relevant:
            return None
        return sum(m.fraud_accuracy for m in relevant) / len(relevant)

    def get_cost_per_outcome(self, capability: Optional[str] = None) -> Optional[float]:
        relevant = [
            m for m in self._n3
            if (capability is None or m.capability == capability) and m.cost_per_outcome_eur is not None
        ]
        if not relevant:
            return None
        return sum(m.cost_per_outcome_eur for m in relevant) / len(relevant)

    def get_dashboard_snapshot(self) -> dict:
        """Returns full 3-tier dashboard snapshot."""
        return {
            "n1_request": {
                "total_requests": len(self._n1),
                "avg_latency_ms": self.get_avg_latency(),
                "total_tokens": self.get_total_tokens(),
            },
            "n2_agent": {
                "total_agent_calls": len(self._n2),
                "escalation_rate": self.get_escalation_rate(),
                "fallback_rate": self.get_fallback_rate(),
                "approvals": sum(1 for r in self._n2 if r.verdict == "APPROVED"),
                "rejections": sum(1 for r in self._n2 if r.verdict == "REJECTED"),
            },
            "n3_business": {
                "fraud_accuracy": self.get_fraud_accuracy(),
                "avg_cost_per_outcome_eur": self.get_cost_per_outcome(),
                "n3_records": len(self._n3),
            },
        }

    def clear(self):
        self._n1 = []
        self._n2 = []
        self._n3 = []


def get_observability_collector() -> ObservabilityCollector:
    global _collector
    if _collector is None:
        _collector = ObservabilityCollector()
    return _collector


_collector: Optional[ObservabilityCollector] = None
