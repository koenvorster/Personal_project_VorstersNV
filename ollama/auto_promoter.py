"""
VorstersNV Auto Promoter
Automatically promotes winning A/B test variants when sufficient evidence exists.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ollama.ab_tester import VariantStatus, get_ab_tester
from ollama.decision_journal import (
    JournalEntry,
    VERDICT_APPROVED,
    VERDICT_REVIEW,
    get_decision_journal,
)


@dataclass
class PromotionDecision:
    agent_name: str
    test_id: str
    winning_variant_id: str
    losing_variant_id: str
    winning_score: float
    losing_score: float
    score_delta: float          # winner - loser
    promoted: bool
    reason: str                 # human-readable explanation
    trace_id: str
    timestamp: str              # ISO datetime


@dataclass
class PromoterConfig:
    min_runs_per_variant: int = 10      # minimum runs before evaluating
    min_score_delta: float = 0.05       # winner must beat loser by at least 5%
    min_winning_score: float = 0.75     # winner must have at least 75% score
    auto_promote: bool = True           # if False, only log decision without promoting


class AutoPromoter:
    """Automatically promotes winning A/B test variants based on quality evidence."""

    def __init__(self, config: Optional[PromoterConfig] = None):
        self.config = config or PromoterConfig()
        self._history: list[PromotionDecision] = []

    def evaluate_agent(self, agent_name: str) -> Optional[PromotionDecision]:
        """
        Check if agent has an active A/B test with a clear winner.

        Returns PromotionDecision if a winner could be determined (promoted or not),
        or None if there is no active test or insufficient runs.
        """
        ab_tester = get_ab_tester()

        active_test_ids = [
            test_id for test_id in ab_tester.list_tests()
            if (cfg := ab_tester.get_test(test_id))
            and cfg.agent_name == agent_name
            and cfg.enabled
        ]

        if not active_test_ids:
            return None

        test_id = active_test_ids[0]
        config = ab_tester.get_test(test_id)
        summary = ab_tester.get_summary(test_id)

        active_variants = config.get_active_variants()
        if len(active_variants) < 2:
            return None

        # Require minimum runs per variant before evaluating
        for variant in active_variants:
            stats = summary.variant_stats.get(variant.variant_id, {})
            if stats.get("count", 0) < self.config.min_runs_per_variant:
                return None

        sorted_variants = sorted(
            [
                (vid, stats)
                for vid, stats in summary.variant_stats.items()
                if any(v.variant_id == vid for v in active_variants)
            ],
            key=lambda x: x[1]["avg_score"],
            reverse=True,
        )

        if len(sorted_variants) < 2:
            return None

        winning_vid, winning_stats = sorted_variants[0]
        losing_vid, losing_stats = sorted_variants[1]

        winning_score = winning_stats["avg_score"]
        losing_score = losing_stats["avg_score"]
        score_delta = winning_score - losing_score

        trace_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        if score_delta >= self.config.min_score_delta and winning_score >= self.config.min_winning_score:
            promoted = self.config.auto_promote
            reason = (
                f"Variant {winning_vid} won with score {winning_score:.2%} "
                f"(delta: {score_delta:.2%})"
            )

            if self.config.auto_promote:
                for variant in config.variants:
                    if variant.variant_id == winning_vid:
                        variant.status = VariantStatus.WINNER
                    elif variant.variant_id == losing_vid:
                        variant.status = VariantStatus.LOSER

            entry = JournalEntry(
                capability=config.capability,
                agent_name=agent_name,
                model_used=winning_vid,
                verdict=VERDICT_APPROVED if promoted else VERDICT_REVIEW,
                trace_id=trace_id,
                selection_reason=reason,
            )
            get_decision_journal().record(entry)

        else:
            promoted = False
            if score_delta < self.config.min_score_delta:
                reason = (
                    f"Insufficient score delta: {score_delta:.4f} < {self.config.min_score_delta}"
                )
            else:
                reason = (
                    f"Winning score too low: {winning_score:.4f} < {self.config.min_winning_score}"
                )

        decision = PromotionDecision(
            agent_name=agent_name,
            test_id=test_id,
            winning_variant_id=winning_vid,
            losing_variant_id=losing_vid,
            winning_score=winning_score,
            losing_score=losing_score,
            score_delta=score_delta,
            promoted=promoted,
            reason=reason,
            trace_id=trace_id,
            timestamp=timestamp,
        )
        self._history.append(decision)
        return decision

    def evaluate_all(self) -> list[PromotionDecision]:
        """Evaluate all agents that have active A/B tests."""
        ab_tester = get_ab_tester()
        agent_names = {
            ab_tester.get_test(test_id).agent_name
            for test_id in ab_tester.list_tests()
            if ab_tester.get_test(test_id) and ab_tester.get_test(test_id).enabled
        }

        decisions = []
        for agent_name in agent_names:
            decision = self.evaluate_agent(agent_name)
            if decision is not None:
                decisions.append(decision)
        return decisions

    def get_promotion_history(self) -> list[PromotionDecision]:
        """Return all past promotion decisions."""
        return list(self._history)


# ── Singleton ─────────────────────────────────────────────────────────────────

_promoter: Optional[AutoPromoter] = None


def get_auto_promoter() -> AutoPromoter:
    global _promoter
    if _promoter is None:
        _promoter = AutoPromoter()
    return _promoter
