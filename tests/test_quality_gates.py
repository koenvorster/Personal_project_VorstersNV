"""
Tests voor ollama/quality_gates.py — minimaal 18 tests.
"""
from __future__ import annotations

import pytest

from ollama.quality_gates import (
    GateResult,
    QualityGate,
    QualityGateEngine,
    Verdict,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _make_engine() -> QualityGateEngine:
    return QualityGateEngine()


# ─────────────────────────────────────────────
# Verdict logica
# ─────────────────────────────────────────────

class TestGetVerdict:
    def test_all_passed_returns_approved(self):
        results = [
            GateResult("G1", True, "BLOCKER", "ok"),
            GateResult("G2", True, "IMPROVEMENT", "ok"),
        ]
        assert _make_engine().get_verdict(results) == Verdict.APPROVED

    def test_blocker_fail_returns_needs_discussion(self):
        results = [
            GateResult("G1", False, "BLOCKER", "fail"),
            GateResult("G2", True, "IMPROVEMENT", "ok"),
        ]
        assert _make_engine().get_verdict(results) == Verdict.NEEDS_DISCUSSION

    def test_only_improvement_fail_returns_changes_requested(self):
        results = [
            GateResult("G1", True, "BLOCKER", "ok"),
            GateResult("G2", False, "IMPROVEMENT", "fail"),
        ]
        assert _make_engine().get_verdict(results) == Verdict.CHANGES_REQUESTED

    def test_empty_results_returns_approved(self):
        assert _make_engine().get_verdict([]) == Verdict.APPROVED

    def test_multiple_blocker_fails_returns_needs_discussion(self):
        results = [
            GateResult("G1", False, "BLOCKER", "fail"),
            GateResult("G2", False, "BLOCKER", "fail"),
        ]
        assert _make_engine().get_verdict(results) == Verdict.NEEDS_DISCUSSION

    def test_is_approved_true_when_all_pass(self):
        results = [GateResult("G1", True, "BLOCKER", "ok")]
        assert _make_engine().is_approved(results) is True

    def test_is_approved_false_when_blocker_fails(self):
        results = [GateResult("G1", False, "BLOCKER", "fail")]
        assert _make_engine().is_approved(results) is False

    def test_get_failing_gates_filters_correctly(self):
        results = [
            GateResult("G1", True, "BLOCKER", "ok"),
            GateResult("G2", False, "IMPROVEMENT", "fail"),
            GateResult("G3", False, "BLOCKER", "fail"),
        ]
        failing = _make_engine().get_failing_gates(results)
        assert len(failing) == 2
        gate_ids = {r.gate_id for r in failing}
        assert gate_ids == {"G2", "G3"}


# ─────────────────────────────────────────────
# Fraud gates
# ─────────────────────────────────────────────

class TestFraudGates:
    def test_qg_fraud_01_passes_with_risk_score_in_validated(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "output", {"risk_score": 75})
        r = next(r for r in results if r.gate_id == "QG-FRAUD-01")
        assert r.passed is True

    def test_qg_fraud_01_fails_without_risk_score(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "output zonder score", {})
        r = next(r for r in results if r.gate_id == "QG-FRAUD-01")
        assert r.passed is False

    def test_qg_fraud_04_passes_with_allow_action(self):
        engine = _make_engine()
        results = engine.run_gates(
            "fraud-detection", "output", {"recommended_action": "ALLOW"}
        )
        r = next(r for r in results if r.gate_id == "QG-FRAUD-04")
        assert r.passed is True

    def test_qg_fraud_04_fails_with_invalid_action(self):
        engine = _make_engine()
        results = engine.run_gates(
            "fraud-detection", "output", {"recommended_action": "UNKNOWN"}
        )
        r = next(r for r in results if r.gate_id == "QG-FRAUD-04")
        assert r.passed is False

    def test_qg_fraud_02_fails_when_rationale_empty(self):
        engine = _make_engine()
        results = engine.run_gates(
            "fraud-detection", "output", {"rationale": "   "}
        )
        r = next(r for r in results if r.gate_id == "QG-FRAUD-02")
        assert r.passed is False


# ─────────────────────────────────────────────
# Content gates
# ─────────────────────────────────────────────

class TestContentGates:
    def test_qg_content_01_passes_with_long_description(self):
        engine = _make_engine()
        desc = "x" * 60
        results = engine.run_gates("product-content", "output", {"beschrijving": desc})
        r = next(r for r in results if r.gate_id == "QG-CONTENT-01")
        assert r.passed is True

    def test_qg_content_01_fails_with_short_description(self):
        engine = _make_engine()
        results = engine.run_gates("product-content", "output", {"beschrijving": "kort"})
        r = next(r for r in results if r.gate_id == "QG-CONTENT-01")
        assert r.passed is False

    def test_qg_content_02_passes_with_keywords_list(self):
        engine = _make_engine()
        results = engine.run_gates(
            "product-content", "output", {"seo_keywords": ["lamp", "led"]}
        )
        r = next(r for r in results if r.gate_id == "QG-CONTENT-02")
        assert r.passed is True

    def test_qg_content_02_fails_with_empty_keywords(self):
        engine = _make_engine()
        results = engine.run_gates(
            "product-content", "output", {"seo_keywords": []}
        )
        r = next(r for r in results if r.gate_id == "QG-CONTENT-02")
        assert r.passed is False


# ─────────────────────────────────────────────
# Order gates
# ─────────────────────────────────────────────

class TestOrderGates:
    def test_qg_order_01_passes_with_order_id(self):
        engine = _make_engine()
        results = engine.run_gates(
            "order-validation", "output", {"order_id": "ORD-001"}
        )
        r = next(r for r in results if r.gate_id == "QG-ORDER-01")
        assert r.passed is True

    def test_qg_order_02_passes_with_aanbeveling(self):
        engine = _make_engine()
        results = engine.run_gates(
            "order-validation", "output", {"order_id": "ORD-001", "aanbeveling": "Goedkeuren"}
        )
        r = next(r for r in results if r.gate_id == "QG-ORDER-02")
        assert r.passed is True


# ─────────────────────────────────────────────
# General gates
# ─────────────────────────────────────────────

class TestGeneralGates:
    def test_qg_general_01_fails_with_empty_output(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "   ", None)
        r = next(r for r in results if r.gate_id == "QG-GENERAL-01")
        assert r.passed is False

    def test_qg_general_01_passes_with_non_empty_output(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "Dit is output", None)
        r = next(r for r in results if r.gate_id == "QG-GENERAL-01")
        assert r.passed is True

    def test_qg_general_02_fails_with_short_output(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "kort", None)
        r = next(r for r in results if r.gate_id == "QG-GENERAL-02")
        assert r.passed is False

    def test_qg_general_02_passes_with_long_output(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "Dit is een langere output tekst", None)
        r = next(r for r in results if r.gate_id == "QG-GENERAL-02")
        assert r.passed is True

    def test_general_gates_apply_to_all_capabilities(self):
        engine = _make_engine()
        for cap in ["fraud-detection", "product-content", "order-validation", "unknown-cap"]:
            results = engine.run_gates(cap, "output", None)
            gate_ids = {r.gate_id for r in results}
            assert "QG-GENERAL-01" in gate_ids, f"QG-GENERAL-01 missing for {cap}"
            assert "QG-GENERAL-02" in gate_ids, f"QG-GENERAL-02 missing for {cap}"


# ─────────────────────────────────────────────
# Extra / Custom gates
# ─────────────────────────────────────────────

class TestCustomGates:
    def test_extra_gate_is_evaluated(self):
        custom = QualityGate(
            gate_id="QG-CUSTOM-01",
            name="Altijd geslaagd",
            capability="*",
            severity="BLOCKER",
            check=lambda o, v: True,
        )
        engine = QualityGateEngine(extra_gates=[custom])
        results = engine.run_gates("fraud-detection", "output", None)
        r = next((r for r in results if r.gate_id == "QG-CUSTOM-01"), None)
        assert r is not None
        assert r.passed is True

    def test_gate_result_contains_trace_id(self):
        engine = _make_engine()
        results = engine.run_gates("fraud-detection", "output test tekst", None, trace_id="TR-001")
        for r in results:
            assert r.trace_id == "TR-001"
