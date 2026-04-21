"""Tests voor ollama/decision_journal.py"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from ollama.decision_journal import (
    DecisionJournal,
    JournalEntry,
    VERDICT_APPROVED,
    VERDICT_REJECTED,
    VERDICT_REVIEW,
    get_decision_journal,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def journal() -> DecisionJournal:
    """Frisse DecisionJournal instantie per test."""
    return DecisionJournal()


@pytest.fixture
def approved_entry() -> JournalEntry:
    return JournalEntry(
        capability="fraud-detection",
        agent_name="fraud-agent-v2",
        model_used="llama3",
        verdict=VERDICT_APPROVED,
        risk_score=30.0,
        environment="dev",
        tools_used=["fraud-check", "address-verify"],
        selection_reason="lage risicoscore",
        alternatives_considered=["mistral", "codellama"],
    )


@pytest.fixture
def rejected_entry() -> JournalEntry:
    return JournalEntry(
        capability="order-blocking",
        agent_name="action-agent-v1",
        model_used="mistral",
        verdict=VERDICT_REJECTED,
        risk_score=85.0,
        environment="prod",
        human_override=True,
        policy_violations=["HITL-001", "HITL-002"],
    )


@pytest.fixture
def review_entry() -> JournalEntry:
    return JournalEntry(
        capability="fraud-detection",
        agent_name="fraud-agent-v2",
        model_used="llama3",
        verdict=VERDICT_REVIEW,
        risk_score=60.0,
        environment="staging",
        execution_time_ms=1234.5,
    )


# ─────────────────────────────────────────────
# JournalEntry validatie
# ─────────────────────────────────────────────

class TestJournalEntry:
    def test_valid_entry_creates_trace_id(self, approved_entry):
        assert approved_entry.trace_id != ""

    def test_timestamp_is_utc(self, approved_entry):
        assert approved_entry.timestamp.tzinfo is not None

    def test_invalid_verdict_raises_value_error(self):
        with pytest.raises(ValueError, match="Ongeldig verdict"):
            JournalEntry(
                capability="test",
                agent_name="agent",
                model_used="llama3",
                verdict="INVALID",
            )

    def test_all_valid_verdicts_accepted(self):
        for verdict in [VERDICT_APPROVED, VERDICT_REJECTED, VERDICT_REVIEW]:
            entry = JournalEntry(
                capability="fraud-detection",
                agent_name="agent",
                model_used="llama3",
                verdict=verdict,
            )
            assert entry.verdict == verdict

    def test_default_tools_used_is_empty_list(self):
        entry = JournalEntry(
            capability="test", agent_name="a", model_used="llama3", verdict=VERDICT_APPROVED
        )
        assert entry.tools_used == []

    def test_execution_time_ms_can_be_none(self):
        entry = JournalEntry(
            capability="test", agent_name="a", model_used="llama3", verdict=VERDICT_APPROVED
        )
        assert entry.execution_time_ms is None


# ─────────────────────────────────────────────
# DecisionJournal.record / get
# ─────────────────────────────────────────────

class TestRecordAndGet:
    def test_record_returns_trace_id(self, journal, approved_entry):
        trace_id = journal.record(approved_entry)
        assert trace_id == approved_entry.trace_id

    def test_get_returns_recorded_entry(self, journal, approved_entry):
        journal.record(approved_entry)
        result = journal.get(approved_entry.trace_id)
        assert result is approved_entry

    def test_get_unknown_trace_id_returns_none(self, journal):
        assert journal.get("nonexistent-id") is None

    def test_multiple_entries_stored_independently(self, journal, approved_entry, rejected_entry):
        journal.record(approved_entry)
        journal.record(rejected_entry)
        assert journal.get(approved_entry.trace_id) is approved_entry
        assert journal.get(rejected_entry.trace_id) is rejected_entry


# ─────────────────────────────────────────────
# list_by_capability / list_by_verdict
# ─────────────────────────────────────────────

class TestListFilters:
    def test_list_by_capability_returns_matching(self, journal, approved_entry, review_entry):
        journal.record(approved_entry)
        journal.record(review_entry)
        results = journal.list_by_capability("fraud-detection")
        assert len(results) == 2

    def test_list_by_capability_excludes_other_capabilities(
        self, journal, approved_entry, rejected_entry
    ):
        journal.record(approved_entry)
        journal.record(rejected_entry)
        results = journal.list_by_capability("fraud-detection")
        assert all(e.capability == "fraud-detection" for e in results)

    def test_list_by_capability_empty_when_no_match(self, journal, rejected_entry):
        journal.record(rejected_entry)
        assert journal.list_by_capability("fraud-detection") == []

    def test_list_by_verdict_returns_approved(
        self, journal, approved_entry, rejected_entry, review_entry
    ):
        journal.record(approved_entry)
        journal.record(rejected_entry)
        journal.record(review_entry)
        approved = journal.list_by_verdict(VERDICT_APPROVED)
        assert all(e.verdict == VERDICT_APPROVED for e in approved)
        assert len(approved) == 1

    def test_list_by_verdict_returns_rejected(
        self, journal, approved_entry, rejected_entry
    ):
        journal.record(approved_entry)
        journal.record(rejected_entry)
        rejected = journal.list_by_verdict(VERDICT_REJECTED)
        assert len(rejected) == 1
        assert rejected[0].capability == "order-blocking"


# ─────────────────────────────────────────────
# export_json
# ─────────────────────────────────────────────

class TestExportJson:
    def test_export_returns_dict(self, journal, approved_entry):
        journal.record(approved_entry)
        data = journal.export_json(approved_entry.trace_id)
        assert isinstance(data, dict)

    def test_export_contains_all_fields(self, journal, approved_entry):
        journal.record(approved_entry)
        data = journal.export_json(approved_entry.trace_id)
        expected_keys = {
            "trace_id", "capability", "agent_name", "model_used", "tools_used",
            "selection_reason", "alternatives_considered", "human_override",
            "verdict", "timestamp", "environment", "risk_score",
            "execution_time_ms", "policy_violations",
        }
        assert expected_keys.issubset(data.keys())

    def test_export_timestamp_is_iso_string(self, journal, approved_entry):
        journal.record(approved_entry)
        data = journal.export_json(approved_entry.trace_id)
        assert isinstance(data["timestamp"], str)
        # moet parseerbaar zijn
        datetime.fromisoformat(data["timestamp"])

    def test_export_unknown_trace_id_raises_key_error(self, journal):
        with pytest.raises(KeyError):
            journal.export_json("nonexistent-id")

    def test_export_human_override_serialized(self, journal, rejected_entry):
        journal.record(rejected_entry)
        data = journal.export_json(rejected_entry.trace_id)
        assert data["human_override"] is True
        assert data["policy_violations"] == ["HITL-001", "HITL-002"]


# ─────────────────────────────────────────────
# summary_stats
# ─────────────────────────────────────────────

class TestSummaryStats:
    def test_empty_journal_returns_zeros(self, journal):
        stats = journal.summary_stats()
        assert stats["total_entries"] == 0
        assert stats["avg_risk_score"] == 0.0
        assert stats["human_overrides"] == 0

    def test_total_entries_count(
        self, journal, approved_entry, rejected_entry, review_entry
    ):
        journal.record(approved_entry)
        journal.record(rejected_entry)
        journal.record(review_entry)
        assert journal.summary_stats()["total_entries"] == 3

    def test_avg_risk_score_calculation(self, journal):
        for risk in [20.0, 40.0, 60.0]:
            journal.record(JournalEntry(
                capability="test", agent_name="a", model_used="llama3",
                verdict=VERDICT_APPROVED, risk_score=risk,
            ))
        assert journal.summary_stats()["avg_risk_score"] == pytest.approx(40.0)

    def test_human_overrides_count(self, journal, rejected_entry):
        journal.record(rejected_entry)
        assert journal.summary_stats()["human_overrides"] == 1

    def test_verdicts_per_capability_structure(
        self, journal, approved_entry, rejected_entry
    ):
        journal.record(approved_entry)
        journal.record(rejected_entry)
        stats = journal.summary_stats()
        vpc = stats["verdicts_per_capability"]
        assert "fraud-detection" in vpc
        assert "order-blocking" in vpc
        assert vpc["fraud-detection"][VERDICT_APPROVED] == 1


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

class TestSingleton:
    def test_get_decision_journal_returns_same_instance(self):
        j1 = get_decision_journal()
        j2 = get_decision_journal()
        assert j1 is j2
