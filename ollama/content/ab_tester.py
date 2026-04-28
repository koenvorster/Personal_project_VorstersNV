"""
A/B Testing Framework voor agent prompt varianten.

Werking:
- Elke agent kan meerdere prompt-varianten hebben (A, B, C...)
- Gewogen random selectie: variant A=70%, B=30%
- Resultaten worden gelogd per variant
- Winner wordt bepaald op basis van kwaliteitsscore
- Statistische significantie via chi-square test (pure Python, geen externe deps)
"""
from __future__ import annotations

import hashlib
import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any

logger = logging.getLogger(__name__)


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


@dataclass
class StatistischeSignificantie:
    """
    Resultaat van een chi-square significantietest voor twee A/B-varianten.

    Velden:
        variant_a_id:               Identifier van variant A.
        variant_b_id:               Identifier van variant B.
        n_a:                        Aantal observaties voor variant A.
        n_b:                        Aantal observaties voor variant B.
        score_a:                    Gemiddelde kwaliteitsscore variant A (0–1).
        score_b:                    Gemiddelde kwaliteitsscore variant B (0–1).
        chi_square_stat:            Berekende chi-kwadraatstatistiek.
        p_waarde:                   Geschatte p-waarde (1 vrijheidsgraad).
        significant:                True als p_waarde < (1 - betrouwbaarheidsinterval).
        winner:                     variant_id van de winnaar, of None als niet significant.
        betrouwbaarheidsinterval:   Gebruikte betrouwbaarheid (bijv. 0.95 = 95 %).
        analyse_op:                 ISO 8601 UTC-tijdstempel van de analyse.
    """

    variant_a_id: str
    variant_b_id: str
    n_a: int
    n_b: int
    score_a: float
    score_b: float
    chi_square_stat: float
    p_waarde: float
    significant: bool
    winner: str | None
    betrouwbaarheidsinterval: float
    analyse_op: str


# ── Pure-Python chi-square hulpfuncties ───────────────────────────────────────

def _regularized_incomplete_gamma(a: float, x: float, max_iter: int = 100) -> float:
    """
    Regularized lower incomplete gamma function P(a, x) via Taylor-series.

    Formule (series-expansie)::

        P(a, x) = e^(-x) * x^a / Gamma(a) * sum_{n=0}^{inf} x^n / (a*(a+1)*...*(a+n))

    Voor df=1 (2×2-tabel) geldt a=0.5, zodat P(0.5, x) = erf(sqrt(x)).

    Bron: Abramowitz & Stegun, "Handbook of Mathematical Functions",
          formule 6.5.29 (serie voor de incomplete gammafunctie).

    Args:
        a:        Vormparameter (0.5 voor 1 vrijheidsgraad).
        x:        Bovengrens van de integratie (chi_sq / 2).
        max_iter: Maximaal aantal Taylor-iteraties (standaard 100).

    Returns:
        P(a, x) ∈ [0, 1].
    """
    if x <= 0.0:
        return 0.0

    # Series: term_0 = 1/a; term_n = term_{n-1} * x / (a+n)
    term: float = 1.0 / a
    total: float = term
    for n in range(1, max_iter + 1):
        term *= x / (a + n)
        total += term
        if abs(term) < 1e-14 * abs(total):
            break

    # P(a, x) = e^(-x + a*ln(x) - ln(Gamma(a))) * series_sum
    log_prefactor = -x + a * math.log(x) - math.lgamma(a)
    result = math.exp(log_prefactor) * total
    return max(0.0, min(result, 1.0))


def _chi2_p_waarde(chi_sq: float, df: int = 1) -> float:
    """
    Bereken de rechter-staart p-waarde van een chi-kwadraatverdeling.

    p = 1 - chi2_CDF(chi_sq, df)
      = 1 - P(df/2, chi_sq/2)   [incomplete gamma met a=df/2, x=chi_sq/2]

    Args:
        chi_sq: Berekende chi-kwadraatstatistiek (≥ 0).
        df:     Vrijheidsgraden (standaard 1 voor 2×2-tabel).

    Returns:
        p-waarde ∈ [0, 1].
    """
    if chi_sq <= 0.0:
        return 1.0
    p_cdf = _regularized_incomplete_gamma(df / 2.0, chi_sq / 2.0)
    return max(0.0, min(1.0 - p_cdf, 1.0))


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

    # ── Statistische significantie ────────────────────────────────────────────

    def bereken_significantie(
        self,
        test_id: str,
        variant_a_id: str,
        variant_b_id: str,
        betrouwbaarheid: float = 0.95,
    ) -> StatistischeSignificantie:
        """
        Voer een chi-square test uit voor twee A/B-varianten.

        Chi-square formule (Pearson, 2×2-contingentietabel)::

            chi² = Σ (O_ij − E_ij)² / E_ij
            E_ij = (rij_totaal × kolom_totaal) / N

        Vrijheidsgraden: df = (rijen-1) × (kolommen-1) = 1 voor een 2×2-tabel.
        Bron: Pearson, K. (1900). "On the criterion that a given system of deviations …"
              Philosophical Magazine, 50(302), 157–175.

        Args:
            test_id:         Identifier van de A/B-test.
            variant_a_id:    Variant-ID van de referentie (A).
            variant_b_id:    Variant-ID van de uitdager (B).
            betrouwbaarheid: Gewenste betrouwbaarheid (standaard 0.95 = 95 %).

        Returns:
            :class:`StatistischeSignificantie` met alle testresultaten.

        Raises:
            ValueError: Als ``test_id`` onbekend is, een variant ontbreekt,
                        of als één van de varianten minder dan 30 observaties heeft.
        """
        _MIN_OBS = 30
        _SUCCES_DREMPEL = 0.7  # score ≥ drempel telt als "succes"

        # ── Validatie ─────────────────────────────────────────────────────────
        config = self._tests.get(test_id)
        if config is None:
            raise ValueError(f"Onbekende test_id: '{test_id}'")

        scores_a = [r.quality_score for r in self.get_results_for_variant(test_id, variant_a_id)]
        scores_b = [r.quality_score for r in self.get_results_for_variant(test_id, variant_b_id)]

        n_a, n_b = len(scores_a), len(scores_b)

        if n_a < _MIN_OBS:
            raise ValueError(
                f"Variant '{variant_a_id}' heeft slechts {n_a} observaties "
                f"(minimum {_MIN_OBS} vereist voor chi-square test)."
            )
        if n_b < _MIN_OBS:
            raise ValueError(
                f"Variant '{variant_b_id}' heeft slechts {n_b} observaties "
                f"(minimum {_MIN_OBS} vereist voor chi-square test)."
            )

        # ── Gemiddelde scores ─────────────────────────────────────────────────
        score_a = sum(scores_a) / n_a
        score_b = sum(scores_b) / n_b

        # ── 2×2 contingentietabel ─────────────────────────────────────────────
        # Rijen: [variant A, variant B]
        # Kolommen: [succes (score ≥ drempel), fout (score < drempel)]
        succes_a = sum(1 for s in scores_a if s >= _SUCCES_DREMPEL)
        fout_a = n_a - succes_a
        succes_b = sum(1 for s in scores_b if s >= _SUCCES_DREMPEL)
        fout_b = n_b - succes_b

        n_totaal = n_a + n_b
        col_succes = succes_a + succes_b
        col_fout = fout_a + fout_b

        # Verwachte waarden: E_ij = (rij_totaal * kolom_totaal) / N
        e_aa = (n_a * col_succes) / n_totaal   # A × succes
        e_ab = (n_a * col_fout) / n_totaal     # A × fout
        e_ba = (n_b * col_succes) / n_totaal   # B × succes
        e_bb = (n_b * col_fout) / n_totaal     # B × fout

        # Chi-kwadraat: som van (O - E)^2 / E voor alle cellen met E > 0
        chi_sq = 0.0
        for observed, expected in (
            (succes_a, e_aa),
            (fout_a,   e_ab),
            (succes_b, e_ba),
            (fout_b,   e_bb),
        ):
            if expected > 0:
                chi_sq += (observed - expected) ** 2 / expected

        # ── P-waarde (df=1) ───────────────────────────────────────────────────
        p_waarde = _chi2_p_waarde(chi_sq, df=1)
        alpha = 1.0 - betrouwbaarheid
        significant = p_waarde < alpha

        # ── Winner ────────────────────────────────────────────────────────────
        winner: str | None = None
        if significant:
            winner = variant_a_id if score_a >= score_b else variant_b_id

        logger.info(
            "Chi-square test test_id=%s A=%s(n=%d,score=%.4f) B=%s(n=%d,score=%.4f) "
            "chi2=%.4f p=%.4f significant=%s winner=%s",
            test_id,
            variant_a_id, n_a, score_a,
            variant_b_id, n_b, score_b,
            chi_sq, p_waarde, significant, winner,
        )

        return StatistischeSignificantie(
            variant_a_id=variant_a_id,
            variant_b_id=variant_b_id,
            n_a=n_a,
            n_b=n_b,
            score_a=round(score_a, 4),
            score_b=round(score_b, 4),
            chi_square_stat=round(chi_sq, 6),
            p_waarde=round(p_waarde, 6),
            significant=significant,
            winner=winner,
            betrouwbaarheidsinterval=betrouwbaarheid,
            analyse_op=datetime.now(timezone.utc).isoformat(),
        )

    def auto_beslis_winner(self, test_id: str) -> str | None:
        """
        Bepaal automatisch de winnaar van een A/B-test op basis van chi-square.

        Eisen:
        - Minimaal 30 observaties per variant.
        - Statistische significantie: p < 0.05 (95 % betrouwbaarheid).

        Bij een significante uitslag wordt de winnende variant gemarkeerd als
        :attr:`VariantStatus.WINNER` en de verliezende als :attr:`VariantStatus.LOSER`.

        Args:
            test_id: Identifier van de A/B-test.

        Returns:
            ``variant_id`` van de winnaar, of ``None`` als de test niet
            significant is of onvoldoende data heeft.
        """
        config = self._tests.get(test_id)
        if config is None:
            logger.warning("auto_beslis_winner: onbekende test_id '%s'", test_id)
            return None

        actieve_varianten = config.get_active_variants()
        if len(actieve_varianten) < 2:
            logger.warning(
                "auto_beslis_winner: test '%s' heeft minder dan 2 actieve varianten",
                test_id,
            )
            return None

        # Beperk tot eerste twee actieve varianten (A en B)
        variant_a = actieve_varianten[0]
        variant_b = actieve_varianten[1]

        try:
            sig = self.bereken_significantie(
                test_id=test_id,
                variant_a_id=variant_a.variant_id,
                variant_b_id=variant_b.variant_id,
                betrouwbaarheid=0.95,
            )
        except ValueError as exc:
            logger.info(
                "auto_beslis_winner: onvoldoende data voor test '%s' — %s",
                test_id, exc,
            )
            return None

        if not sig.significant or sig.winner is None:
            logger.info(
                "auto_beslis_winner: test '%s' niet significant (p=%.4f)",
                test_id, sig.p_waarde,
            )
            return None

        # Markeer varianten
        loser_id = (
            variant_b.variant_id
            if sig.winner == variant_a.variant_id
            else variant_a.variant_id
        )

        for variant in config.variants:
            if variant.variant_id == sig.winner:
                variant.status = VariantStatus.WINNER
                logger.info(
                    "auto_beslis_winner: variant '%s' gemarkeerd als WINNER (test=%s, p=%.4f)",
                    variant.variant_id, test_id, sig.p_waarde,
                )
            elif variant.variant_id == loser_id:
                variant.status = VariantStatus.LOSER
                logger.info(
                    "auto_beslis_winner: variant '%s' gemarkeerd als LOSER (test=%s)",
                    variant.variant_id, test_id,
                )

        return sig.winner


def get_ab_tester() -> PromptABTester:
    global _tester
    if _tester is None:
        _tester = PromptABTester()
    return _tester


_tester: Optional[PromptABTester] = None
