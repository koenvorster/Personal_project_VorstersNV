"""
VorstersNV Quality Gates
Beoordeelt agent output conform het phr-globalconfig QG systeem.

Gebruik:
    from ollama.quality_gates import QualityGateEngine, Verdict

    engine = QualityGateEngine()
    results = engine.run_gates("fraud-detection", output, validated)
    verdict = engine.get_verdict(results)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Verdict
# ─────────────────────────────────────────────

class Verdict(str, Enum):
    """Eindoordeel van de quality gate evaluatie."""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    NEEDS_DISCUSSION = "NEEDS_DISCUSSION"


# ─────────────────────────────────────────────
# QualityGate & GateResult
# ─────────────────────────────────────────────

@dataclass
class QualityGate:
    """
    Definitie van één quality gate.

    Attributes:
        gate_id:    Unieke identifier (bijv. "QG-FRAUD-01")
        name:       Leesbare naam
        capability: Capability waarvoor de gate geldt, of "*" voor alle
        severity:   "BLOCKER" blokkeert release; "IMPROVEMENT" is advies
        check:      Callable(output, validated) -> bool
    """
    gate_id: str
    name: str
    capability: str
    severity: str  # "BLOCKER" | "IMPROVEMENT"
    check: Callable[[str, dict | None], bool]


@dataclass
class GateResult:
    """
    Resultaat van één quality gate evaluatie.

    Attributes:
        gate_id:  Identifier van de gate
        passed:   True als de gate geslaagd is
        severity: Overgenomen van de gate definitie
        message:  Leesbare uitleg van het resultaat
        trace_id: Optionele trace identifier
    """
    gate_id: str
    passed: bool
    severity: str
    message: str
    trace_id: str = ""


# ─────────────────────────────────────────────
# Pre-configured gates
# ─────────────────────────────────────────────

def _has_key(key: str) -> Callable[[str, dict | None], bool]:
    """Factory: controleert of een sleutel aanwezig is in validated dict."""
    def _check(output: str, validated: dict | None) -> bool:
        if validated and key in validated:
            return bool(validated[key] is not None)
        return key in output

    return _check


def _recommended_action_valid(output: str, validated: dict | None) -> bool:
    valid = {"ALLOW", "REVIEW", "BLOCK"}
    if validated and "recommended_action" in validated:
        return str(validated["recommended_action"]).upper() in valid
    for v in valid:
        if v in output.upper():
            return True
    return False


def _description_min_50(output: str, validated: dict | None) -> bool:
    if validated and "beschrijving" in validated:
        return len(str(validated["beschrijving"])) >= 50
    return len(output) >= 50


def _seo_keywords_not_empty(output: str, validated: dict | None) -> bool:
    if validated and "seo_keywords" in validated:
        kw = validated["seo_keywords"]
        if isinstance(kw, list):
            return len(kw) > 0
        return bool(str(kw).strip())
    return "keyword" in output.lower() or "seo" in output.lower()


PRECONFIGURED_GATES: list[QualityGate] = [
    # Fraude gates
    QualityGate(
        gate_id="QG-FRAUD-01",
        name="Risk score aanwezig",
        capability="fraud-detection",
        severity="BLOCKER",
        check=_has_key("risk_score"),
    ),
    QualityGate(
        gate_id="QG-FRAUD-02",
        name="Rationale niet leeg",
        capability="fraud-detection",
        severity="BLOCKER",
        check=lambda output, validated: (
            bool(validated.get("rationale", "").strip()) if validated and "rationale" in validated
            else bool(output.strip())
        ),
    ),
    QualityGate(
        gate_id="QG-FRAUD-03",
        name="Confidence score aanwezig",
        capability="fraud-detection",
        severity="IMPROVEMENT",
        check=_has_key("confidence_score"),
    ),
    QualityGate(
        gate_id="QG-FRAUD-04",
        name="Recommended action is ALLOW/REVIEW/BLOCK",
        capability="fraud-detection",
        severity="BLOCKER",
        check=_recommended_action_valid,
    ),
    # Content gates
    QualityGate(
        gate_id="QG-CONTENT-01",
        name="Beschrijving minimaal 50 tekens",
        capability="product-content",
        severity="BLOCKER",
        check=_description_min_50,
    ),
    QualityGate(
        gate_id="QG-CONTENT-02",
        name="SEO keywords niet leeg",
        capability="product-content",
        severity="IMPROVEMENT",
        check=_seo_keywords_not_empty,
    ),
    QualityGate(
        gate_id="QG-CONTENT-03",
        name="BTW categorie aanwezig",
        capability="product-content",
        severity="BLOCKER",
        check=_has_key("btw_categorie"),
    ),
    # Order gates
    QualityGate(
        gate_id="QG-ORDER-01",
        name="Order ID aanwezig",
        capability="order-validation",
        severity="BLOCKER",
        check=_has_key("order_id"),
    ),
    QualityGate(
        gate_id="QG-ORDER-02",
        name="Aanbeveling aanwezig",
        capability="order-validation",
        severity="BLOCKER",
        check=_has_key("aanbeveling"),
    ),
    # General gates (capability = "*")
    QualityGate(
        gate_id="QG-GENERAL-01",
        name="Response niet leeg",
        capability="*",
        severity="BLOCKER",
        check=lambda output, validated: bool(output.strip()),
    ),
    QualityGate(
        gate_id="QG-GENERAL-02",
        name="Response langer dan 20 tekens",
        capability="*",
        severity="IMPROVEMENT",
        check=lambda output, validated: len(output.strip()) > 20,
    ),
]


# ─────────────────────────────────────────────
# QualityGateEngine
# ─────────────────────────────────────────────

class QualityGateEngine:
    """
    Voert quality gates uit op agent output.

    Gates worden gefilterd op capability: gates met capability="*" gelden altijd,
    gates met een specifieke capability alleen voor die capability.
    """

    def __init__(self, extra_gates: list[QualityGate] | None = None) -> None:
        self._gates: list[QualityGate] = list(PRECONFIGURED_GATES)
        if extra_gates:
            self._gates.extend(extra_gates)

    def _gates_for(self, capability: str) -> list[QualityGate]:
        return [g for g in self._gates if g.capability in ("*", capability)]

    def run_gates(
        self,
        capability: str,
        output: str,
        validated: dict | None = None,
        trace_id: str = "",
    ) -> list[GateResult]:
        """
        Evalueer alle gates die van toepassing zijn op de gegeven capability.

        Args:
            capability: De capability naam (bijv. "fraud-detection")
            output:     De ruwe tekst-output van de agent
            validated:  Optioneel: gevalideerde dict (uit output schema)
            trace_id:   Optionele trace identifier

        Returns:
            Lijst van GateResult objecten
        """
        results: list[GateResult] = []
        for gate in self._gates_for(capability):
            try:
                passed = gate.check(output, validated)
            except Exception as exc:
                logger.exception("Fout bij uitvoeren gate %s: %s", gate.gate_id, exc)
                passed = False

            status = "geslaagd" if passed else "mislukt"
            message = f"[{gate.gate_id}] {gate.name}: {status}"
            results.append(
                GateResult(
                    gate_id=gate.gate_id,
                    passed=passed,
                    severity=gate.severity,
                    message=message,
                    trace_id=trace_id,
                )
            )
            logger.debug(message)

        return results

    def get_verdict(self, gate_results: list[GateResult]) -> Verdict:
        """
        Bepaal het eindoordeel op basis van gate resultaten.

        - Een of meer BLOCKER mislukt → NEEDS_DISCUSSION
        - Alleen IMPROVEMENT mislukt → CHANGES_REQUESTED
        - Alles geslaagd → APPROVED
        """
        failing = self.get_failing_gates(gate_results)
        if not failing:
            return Verdict.APPROVED
        if any(r.severity == "BLOCKER" for r in failing):
            return Verdict.NEEDS_DISCUSSION
        return Verdict.CHANGES_REQUESTED

    def get_failing_gates(self, results: list[GateResult]) -> list[GateResult]:
        """Geef alle mislukte gate resultaten terug."""
        return [r for r in results if not r.passed]

    def is_approved(self, results: list[GateResult]) -> bool:
        """Geeft True terug als het verdict APPROVED is."""
        return self.get_verdict(results) == Verdict.APPROVED
