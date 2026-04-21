"""
A/B Testing Framework voor agent prompt varianten.

Werking:
- Elke agent kan meerdere prompt-varianten hebben (A, B, C...)
- Gewogen random selectie: variant A=70%, B=30%
- Resultaten worden gelogd per variant
- Winner wordt bepaald op basis van kwaliteitsscore
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any


class VariantStatus(Enum):
    ACTIVE = "active"
    WINNER = "winner"
    LOSER = "loser"
    PAUSED = "paused"


@dataclass
class PromptVariant:
    variant_id: str          # "A", "B", "control"
    prompt_template: str
    weight: float = 0.5      # kans op selectie (0.0-1.0)
    status: VariantStatus = VariantStatus.ACTIVE
    description: str = ""


@dataclass
class ABTestConfig:
    test_id: str
    agent_name: str
    capability: str
    variants: list[PromptVariant]
    min_samples_per_variant: int = 10    # min voor statistisch besluit
    confidence_threshold: float = 0.95   # vereiste confidence
    enabled: bool = True

    def get_active_variants(self) -> list[PromptVariant]:
        return [v for v in self.variants if v.status == VariantStatus.ACTIVE]

    def normalize_weights(self):
        """Normaliseert gewichten zodat ze optellen tot 1.0."""
        active = self.get_active_variants()
        if not active:
            return
        total = sum(v.weight for v in active)
        if total > 0:
            for v in active:
                v.weight = v.weight / total


@dataclass
class ABTestResult:
    test_id: str
    variant_id: str
    agent_name: str
    quality_score: float     # 0.0-1.0
    latency_ms: float
    success: bool
    trace_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class ABTestSummary:
    test_id: str
    variant_stats: dict[str, dict]   # variant_id → {count, avg_score, avg_latency, success_rate}
    winner: Optional[str] = None
    confidence: float = 0.0
    recommendation: str = ""

    def get_variant_score(self, variant_id: str) -> float:
        stats = self.variant_stats.get(variant_id, {})
        return stats.get("avg_score", 0.0)


class PromptABTester:
    """Beheert A/B tests voor agent prompt varianten."""

    def __init__(self):
        self._tests: dict[str, ABTestConfig] = {}
        self._results: list[ABTestResult] = []

    def register_test(self, config: ABTestConfig):
        config.normalize_weights()
        self._tests[config.test_id] = config

    def get_test(self, test_id: str) -> Optional[ABTestConfig]:
        return self._tests.get(test_id)

    def select_variant(self, test_id: str, seed: Optional[str] = None) -> Optional[PromptVariant]:
        """
        Selecteert een variant via gewogen random keuze.
        seed: deterministische selectie (bijv. trace_id) — handig voor reproducibility
        """
        config = self._tests.get(test_id)
        if not config or not config.enabled:
            return None

        active = config.get_active_variants()
        if not active:
            return None

        if seed:
            # Deterministische selectie op basis van seed
            hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)
            rng = random.Random(hash_val)
        else:
            rng = random

        weights = [v.weight for v in active]
        return rng.choices(active, weights=weights, k=1)[0]

    def record_result(self, result: ABTestResult):
        self._results.append(result)

    def get_summary(self, test_id: str) -> ABTestSummary:
        """Berekent statistieken per variant en bepaalt winner."""
        results = [r for r in self._results if r.test_id == test_id]

        variant_stats: dict[str, dict] = {}
        for r in results:
            if r.variant_id not in variant_stats:
                variant_stats[r.variant_id] = {
                    "count": 0,
                    "total_score": 0.0,
                    "total_latency": 0.0,
                    "successes": 0,
                }
            s = variant_stats[r.variant_id]
            s["count"] += 1
            s["total_score"] += r.quality_score
            s["total_latency"] += r.latency_ms
            s["successes"] += 1 if r.success else 0

        # Bereken gemiddelden
        for vid, s in variant_stats.items():
            n = s["count"]
            s["avg_score"] = round(s["total_score"] / n, 4) if n > 0 else 0.0
            s["avg_latency"] = round(s["total_latency"] / n, 2) if n > 0 else 0.0
            s["success_rate"] = round(s["successes"] / n, 4) if n > 0 else 0.0

        # Bepaal winner
        config = self._tests.get(test_id)
        winner = None
        confidence = 0.0
        recommendation = "Onvoldoende data voor beslissing"

        if config and all(
            variant_stats.get(v.variant_id, {}).get("count", 0) >= config.min_samples_per_variant
            for v in config.get_active_variants()
        ):
            best = max(variant_stats.items(), key=lambda x: x[1]["avg_score"], default=None)
            if best:
                winner = best[0]
                # Simplified confidence: score verschil als proxy
                scores = [s["avg_score"] for s in variant_stats.values()]
                if len(scores) >= 2:
                    scores_sorted = sorted(scores, reverse=True)
                    diff = scores_sorted[0] - scores_sorted[1]
                    confidence = min(0.99, 0.5 + diff * 5)  # simplified
                else:
                    confidence = 0.5
                recommendation = f"Gebruik variant {winner} (score: {best[1]['avg_score']:.2%})"

        return ABTestSummary(
            test_id=test_id,
            variant_stats=variant_stats,
            winner=winner,
            confidence=confidence,
            recommendation=recommendation,
        )

    def list_tests(self) -> list[str]:
        return list(self._tests.keys())

    def get_results_for_variant(self, test_id: str, variant_id: str) -> list[ABTestResult]:
        return [r for r in self._results if r.test_id == test_id and r.variant_id == variant_id]

    def clear_results(self, test_id: Optional[str] = None):
        if test_id:
            self._results = [r for r in self._results if r.test_id != test_id]
        else:
            self._results = []


def get_ab_tester() -> PromptABTester:
    global _tester
    if _tester is None:
        _tester = PromptABTester()
    return _tester


_tester: Optional[PromptABTester] = None
