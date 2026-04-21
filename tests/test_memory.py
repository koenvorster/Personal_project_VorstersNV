"""
Tests voor VorstersNV memory management — f3-09.
Versioned context injection met SessionMemory en ContextAssembler.
"""
from __future__ import annotations

import hashlib
import pytest

from ollama.memory import (
    TurnRecord,
    MemorySummary,
    VersionedContext,
    SessionMemory,
    ContextAssembler,
    get_context_assembler,
)


# ─────────────────────────────────────────────────────────
# TurnRecord
# ─────────────────────────────────────────────────────────

class TestTurnRecord:
    def test_fields_stored_correctly(self):
        tr = TurnRecord(role="user", content="hallo wereld")
        assert tr.role == "user"
        assert tr.content == "hallo wereld"

    def test_timestamp_auto_set(self):
        tr = TurnRecord(role="assistant", content="antwoord")
        assert tr.timestamp is not None
        assert "T" in tr.timestamp  # ISO format

    def test_custom_timestamp(self):
        tr = TurnRecord(role="user", content="test", timestamp="2024-01-01T00:00:00")
        assert tr.timestamp == "2024-01-01T00:00:00"

    def test_role_values(self):
        u = TurnRecord(role="user", content="x")
        a = TurnRecord(role="assistant", content="y")
        assert u.role == "user"
        assert a.role == "assistant"


# ─────────────────────────────────────────────────────────
# MemorySummary
# ─────────────────────────────────────────────────────────

class TestMemorySummary:
    def test_version_hash_generated(self):
        ms = MemorySummary(summary="test samenvatting", turn_count=5)
        expected = hashlib.sha256("test samenvatting".encode()).hexdigest()[:8]
        assert ms.version == expected

    def test_version_is_8_chars(self):
        ms = MemorySummary(summary="any text", turn_count=3)
        assert len(ms.version) == 8

    def test_turn_count_stored(self):
        ms = MemorySummary(summary="x", turn_count=10)
        assert ms.turn_count == 10

    def test_different_summaries_different_versions(self):
        ms1 = MemorySummary(summary="aaa", turn_count=1)
        ms2 = MemorySummary(summary="bbb", turn_count=1)
        assert ms1.version != ms2.version

    def test_created_at_auto_set(self):
        ms = MemorySummary(summary="s", turn_count=1)
        assert ms.created_at is not None
        assert "T" in ms.created_at


# ─────────────────────────────────────────────────────────
# SessionMemory
# ─────────────────────────────────────────────────────────

class TestSessionMemory:
    def test_add_turn_accumulates(self):
        sm = SessionMemory("s1")
        sm.add_turn("user", "bericht 1")
        sm.add_turn("assistant", "antwoord 1")
        assert len(sm._turns) == 2

    def test_auto_summarize_triggers_at_10_turns(self):
        sm = SessionMemory("s1")
        for i in range(10):
            sm.add_turn("user", f"bericht {i}")
        assert len(sm._summaries) == 1
        assert len(sm._turns) == 0

    def test_auto_summarize_resets_turns(self):
        sm = SessionMemory("s2")
        for i in range(10):
            sm.add_turn("user", f"msg {i}")
        assert sm._turns == []

    def test_summary_contains_turn_count(self):
        sm = SessionMemory("s3")
        for i in range(10):
            sm.add_turn("user", f"bericht {i}")
        assert sm._summaries[0].turn_count == 10

    def test_no_summary_before_threshold(self):
        sm = SessionMemory("s4")
        for i in range(9):
            sm.add_turn("user", f"m{i}")
        assert len(sm._summaries) == 0

    def test_get_recent_turns_returns_last_n(self):
        sm = SessionMemory("s5")
        for i in range(5):
            sm.add_turn("user", f"m{i}")
        recent = sm.get_recent_turns(3)
        assert len(recent) == 3
        assert recent[-1].content == "m4"

    def test_get_recent_turns_empty_session(self):
        sm = SessionMemory("s6")
        assert sm.get_recent_turns(3) == []

    def test_get_recent_turns_fewer_than_n(self):
        sm = SessionMemory("s7")
        sm.add_turn("user", "enkel bericht")
        recent = sm.get_recent_turns(5)
        assert len(recent) == 1

    def test_get_turn_count_only_turns(self):
        sm = SessionMemory("s8")
        sm.add_turn("user", "a")
        sm.add_turn("assistant", "b")
        assert sm.get_turn_count() == 2

    def test_get_turn_count_includes_summary_turns(self):
        sm = SessionMemory("s9")
        for i in range(10):  # triggers summary of 10
            sm.add_turn("user", f"m{i}")
        sm.add_turn("user", "extra")
        assert sm.get_turn_count() == 11

    def test_get_context_summary_none_initially(self):
        sm = SessionMemory("s10")
        assert sm.get_context_summary() is None

    def test_get_context_summary_after_summarize(self):
        sm = SessionMemory("s11")
        for i in range(10):
            sm.add_turn("user", f"m{i}")
        summary = sm.get_context_summary()
        assert summary is not None
        assert "Samenvatting" in summary

    def test_clear_resets_turns_and_summaries(self):
        sm = SessionMemory("s12")
        for i in range(10):
            sm.add_turn("user", f"m{i}")
        sm.add_turn("user", "nog een")
        sm.clear()
        assert sm._turns == []
        assert sm._summaries == []
        assert sm.get_turn_count() == 0

    def test_multiple_summaries_accumulate(self):
        sm = SessionMemory("s13")
        for _ in range(20):  # two batches of 10
            sm.add_turn("user", "bericht")
        assert len(sm._summaries) == 2

    def test_get_context_summary_returns_most_recent(self):
        sm = SessionMemory("s14")
        for _ in range(10):
            sm.add_turn("user", "batch1")
        for _ in range(10):
            sm.add_turn("user", "batch2")
        summary = sm.get_context_summary()
        assert "batch2" in summary


# ─────────────────────────────────────────────────────────
# VersionedContext
# ─────────────────────────────────────────────────────────

class TestVersionedContext:
    def test_to_prompt_sections_contains_domain_rules(self):
        ctx = VersionedContext(domain_rules="BTW 21%", task_context="check order")
        sections = ctx.to_prompt_sections()
        assert any("[DOMAIN_RULES" in s for s in sections)

    def test_to_prompt_sections_contains_closing_delimiter(self):
        ctx = VersionedContext(domain_rules="BTW 21%")
        sections = ctx.to_prompt_sections()
        assert any("[/DOMAIN_RULES]" in s for s in sections)

    def test_empty_domain_rules_omitted(self):
        ctx = VersionedContext(domain_rules="", task_context="taak")
        sections = ctx.to_prompt_sections()
        assert not any("[DOMAIN_RULES" in s for s in sections)

    def test_task_context_section_present(self):
        ctx = VersionedContext(task_context="controleer betaling")
        sections = ctx.to_prompt_sections()
        assert any("[TASK_CONTEXT]" in s for s in sections)
        assert any("[/TASK_CONTEXT]" in s for s in sections)

    def test_memory_summary_section(self):
        ctx = VersionedContext(memory_summary="eerder gesprek samenvatting")
        sections = ctx.to_prompt_sections()
        assert any("[MEMORY]" in s for s in sections)
        assert any("[/MEMORY]" in s for s in sections)

    def test_no_memory_section_when_none(self):
        ctx = VersionedContext(domain_rules="x", memory_summary=None)
        sections = ctx.to_prompt_sections()
        assert not any("[MEMORY]" in s for s in sections)

    def test_tool_results_numbered_correctly(self):
        ctx = VersionedContext(tool_results=["result_a", "result_b"])
        sections = ctx.to_prompt_sections()
        assert any("[TOOL_RESULT_1]" in s for s in sections)
        assert any("[TOOL_RESULT_2]" in s for s in sections)
        assert not any("[TOOL_RESULT_3]" in s for s in sections)

    def test_tool_results_closing_delimiters(self):
        ctx = VersionedContext(tool_results=["r1"])
        sections = ctx.to_prompt_sections()
        assert any("[/TOOL_RESULT_1]" in s for s in sections)

    def test_assemble_joins_with_double_newline(self):
        ctx = VersionedContext(domain_rules="d", task_context="t")
        assembled = ctx.assemble()
        assert "\n\n" in assembled

    def test_assemble_empty_context_is_empty_string(self):
        ctx = VersionedContext()
        assert ctx.assemble() == ""

    def test_version_in_domain_rules_header(self):
        ctx = VersionedContext(domain_rules="BTW", version="2.5")
        sections = ctx.to_prompt_sections()
        domain_section = next(s for s in sections if "[DOMAIN_RULES" in s)
        assert "v2.5" in domain_section


# ─────────────────────────────────────────────────────────
# ContextAssembler
# ─────────────────────────────────────────────────────────

class TestContextAssembler:
    def test_assemble_without_session_id(self):
        ca = ContextAssembler()
        ctx = ca.assemble("controleer order 123")
        assert ctx.task_context == "controleer order 123"
        assert ctx.memory_summary is None

    def test_assemble_uses_default_domain_rules(self):
        ca = ContextAssembler()
        ctx = ca.assemble("taak")
        assert "BTW" in ctx.domain_rules
        assert "Mollie" in ctx.domain_rules

    def test_assemble_custom_domain_rules(self):
        ca = ContextAssembler()
        ctx = ca.assemble("taak", domain_rules="Eigen regels")
        assert ctx.domain_rules == "Eigen regels"

    def test_assemble_with_tool_results(self):
        ca = ContextAssembler()
        ctx = ca.assemble("taak", tool_results=["result 1", "result 2"])
        assert len(ctx.tool_results) == 2

    def test_assemble_with_session_no_summary(self):
        ca = ContextAssembler()
        ctx = ca.assemble("taak", session_id="sess-001")
        assert ctx.memory_summary is None

    def test_assemble_with_session_after_summarize(self):
        ca = ContextAssembler()
        for i in range(10):
            ca.record_turn("sess-002", "user", f"bericht {i}")
        ctx = ca.assemble("taak", session_id="sess-002")
        assert ctx.memory_summary is not None
        assert "Samenvatting" in ctx.memory_summary

    def test_get_session_creates_new_session(self):
        ca = ContextAssembler()
        sess = ca.get_session("nieuw-id")
        assert sess.session_id == "nieuw-id"

    def test_get_session_returns_same_instance(self):
        ca = ContextAssembler()
        s1 = ca.get_session("same-id")
        s2 = ca.get_session("same-id")
        assert s1 is s2

    def test_record_turn_adds_to_session(self):
        ca = ContextAssembler()
        ca.record_turn("sess-003", "user", "hallo")
        sess = ca.get_session("sess-003")
        assert sess.get_turn_count() == 1

    def test_version_propagated_to_context(self):
        ca = ContextAssembler(version="3.0")
        ctx = ca.assemble("taak")
        assert ctx.version == "3.0"


# ─────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_context_assembler_singleton(self):
        a1 = get_context_assembler()
        a2 = get_context_assembler()
        assert a1 is a2

    def test_singleton_is_context_assembler(self):
        assembler = get_context_assembler()
        assert isinstance(assembler, ContextAssembler)
