"""
Tests voor ollama/review_loop.py — minimaal 8 tests.
Gebruikt unittest.mock.AsyncMock om AgentRunner te mocken.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ollama.quality_gates import GateResult, Verdict
from ollama.review_loop import run_with_review


def _make_runner(responses: list[tuple[str, str, dict | None]]) -> MagicMock:
    """Maak een gemockte AgentRunner met vooraf ingestelde responses."""
    runner = MagicMock()
    runner.run_agent = AsyncMock(side_effect=responses)
    return runner


# ─────────────────────────────────────────────
# Happy path
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_approved_on_first_iteration():
    """Agent output die direct APPROVED is hoeft niet herhaald te worden."""
    # Uitgebreide output die alle general gates passeert
    good_output = "Dit is een uitgebreide en goede response tekst die zeker lang genoeg is."
    runner = _make_runner([
        (good_output, "iid-1", None),
    ])

    output, verdict, results = await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",  # alleen general gates
    )

    assert verdict == Verdict.APPROVED
    assert output == good_output
    runner.run_agent.assert_called_once()


@pytest.mark.asyncio
async def test_changes_requested_retries_and_eventually_approved():
    """CHANGES_REQUESTED triggert een retry; tweede poging is APPROVED."""
    short_output = "kort"  # faalt QG-GENERAL-02 (IMPROVEMENT)
    good_output = "Dit is een uitgebreide en goede response tekst die zeker lang genoeg is."

    runner = _make_runner([
        (short_output, "iid-1", None),
        (good_output, "iid-2", None),
    ])

    output, verdict, results = await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",
        max_iterations=2,
    )

    assert verdict == Verdict.APPROVED
    assert output == good_output
    assert runner.run_agent.call_count == 2


@pytest.mark.asyncio
async def test_needs_discussion_no_retry():
    """Bij NEEDS_DISCUSSION (BLOCKER fail) mag er geen retry plaatsvinden."""
    # Lege output faalt QG-GENERAL-01 (BLOCKER)
    runner = _make_runner([
        ("", "iid-1", None),
        ("dit zou nooit aangeroepen mogen worden", "iid-2", None),
    ])

    output, verdict, results = await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",
        max_iterations=2,
    )

    assert verdict == Verdict.NEEDS_DISCUSSION
    runner.run_agent.assert_called_once()


@pytest.mark.asyncio
async def test_max_iterations_respected():
    """Na max_iterations pogingen stopt de loop altijd."""
    short_output = "kort"  # faalt IMPROVEMENT gate, nooit APPROVED

    runner = _make_runner([
        (short_output, "iid-1", None),
        (short_output, "iid-2", None),
        (short_output, "iid-3", None),
    ])

    output, verdict, results = await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",
        max_iterations=2,
    )

    # max_iterations=2 betekent maximaal 3 aanroepen (0,1,2)
    assert runner.run_agent.call_count == 3
    assert verdict == Verdict.CHANGES_REQUESTED


@pytest.mark.asyncio
async def test_context_prepended_to_input():
    """Context wordt vóór de input toegevoegd in de eerste aanroep."""
    good_output = "Dit is een uitgebreide en goede response tekst die zeker lang genoeg is."
    runner = _make_runner([(good_output, "iid-1", None)])

    await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        context="Extra context info",
        capability="unknown-cap",
    )

    call_args = runner.run_agent.call_args
    user_input = call_args.kwargs.get("user_input") or call_args.args[1]
    assert "Extra context info" in user_input
    assert "Analyseer dit" in user_input


@pytest.mark.asyncio
async def test_feedback_prompt_contains_failing_gate_info():
    """Na CHANGES_REQUESTED bevat de retry-prompt informatie over falende gates."""
    short_output = "kort"
    good_output = "Dit is een uitgebreide en goede response tekst die zeker lang genoeg is."

    runner = _make_runner([
        (short_output, "iid-1", None),
        (good_output, "iid-2", None),
    ])

    await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",
        max_iterations=2,
    )

    # Tweede aanroep moet feedback-prompt bevatten
    second_call_args = runner.run_agent.call_args_list[1]
    user_input = second_call_args.kwargs.get("user_input") or second_call_args.args[1]
    assert "kwaliteitseisen" in user_input.lower() or "QG-" in user_input


@pytest.mark.asyncio
async def test_gate_results_returned():
    """De teruggegeven gate_results zijn de resultaten van de laatste iteratie."""
    good_output = "Dit is een uitgebreide en goede response tekst die zeker lang genoeg is."
    runner = _make_runner([(good_output, "iid-1", None)])

    _, _, results = await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",
    )

    assert isinstance(results, list)
    assert all(isinstance(r, GateResult) for r in results)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_trace_id_passed_to_gates():
    """trace_id wordt doorgegeven aan alle gate resultaten."""
    good_output = "Dit is een uitgebreide en goede response tekst die zeker lang genoeg is."
    runner = _make_runner([(good_output, "iid-1", None)])

    _, _, results = await run_with_review(
        runner=runner,
        agent_name="test-agent",
        input_text="Analyseer dit",
        capability="unknown-cap",
        trace_id="TRACE-XYZ",
    )

    for r in results:
        assert r.trace_id == "TRACE-XYZ"
