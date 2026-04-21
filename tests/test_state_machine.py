"""
Tests voor ollama/state_machine.py — minimaal 20 tests.

Dekt:
- Alle geldige transities
- Ongeldige transities → InvalidTransitionError
- Checkpoint save/restore
- HITL trigger/approve/reject flow
- Volledige workflow happy path
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from ollama.state_machine import (
    Checkpoint,
    InvalidTransitionError,
    WorkflowState,
    WorkflowStateMachine,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _make_sm(workflow_id: str = "WF-TEST") -> WorkflowStateMachine:
    """Maak een WorkflowStateMachine met een nep-EventBus."""
    mock_bus = MagicMock()
    mock_bus.publish = AsyncMock(return_value=True)
    return WorkflowStateMachine(workflow_id=workflow_id, trace_id="trace-test", event_bus=mock_bus)


# ─────────────────────────────────────────────
# Initialisatie
# ─────────────────────────────────────────────

class TestInitialization:
    def test_initial_state_is_pending(self):
        sm = _make_sm()
        assert sm.current_state == WorkflowState.PENDING

    def test_history_starts_with_pending(self):
        sm = _make_sm()
        assert len(sm.history) == 1
        assert sm.history[0][0] == WorkflowState.PENDING

    def test_no_checkpoints_initially(self):
        sm = _make_sm()
        assert sm.get_latest_checkpoint() is None


# ─────────────────────────────────────────────
# Geldige transities
# ─────────────────────────────────────────────

class TestValidTransitions:
    def test_pending_to_running(self):
        sm = _make_sm()
        assert sm.transition(WorkflowState.RUNNING) is True
        assert sm.current_state == WorkflowState.RUNNING

    def test_running_to_checkpoint(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        assert sm.transition(WorkflowState.CHECKPOINT) is True
        assert sm.current_state == WorkflowState.CHECKPOINT

    def test_running_to_completed(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        assert sm.transition(WorkflowState.COMPLETED) is True
        assert sm.current_state == WorkflowState.COMPLETED

    def test_running_to_failed(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        assert sm.transition(WorkflowState.FAILED) is True
        assert sm.current_state == WorkflowState.FAILED

    def test_running_to_awaiting_human(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        assert sm.transition(WorkflowState.AWAITING_HUMAN) is True
        assert sm.current_state == WorkflowState.AWAITING_HUMAN

    def test_checkpoint_to_running(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.CHECKPOINT)
        assert sm.transition(WorkflowState.RUNNING) is True
        assert sm.current_state == WorkflowState.RUNNING

    def test_checkpoint_to_awaiting_human(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.CHECKPOINT)
        assert sm.transition(WorkflowState.AWAITING_HUMAN) is True
        assert sm.current_state == WorkflowState.AWAITING_HUMAN

    def test_awaiting_human_to_running(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.AWAITING_HUMAN)
        assert sm.transition(WorkflowState.RUNNING) is True
        assert sm.current_state == WorkflowState.RUNNING

    def test_awaiting_human_to_failed(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.AWAITING_HUMAN)
        assert sm.transition(WorkflowState.FAILED) is True
        assert sm.current_state == WorkflowState.FAILED


# ─────────────────────────────────────────────
# Ongeldige transities
# ─────────────────────────────────────────────

class TestInvalidTransitions:
    def test_pending_to_completed_raises(self):
        sm = _make_sm()
        with pytest.raises(InvalidTransitionError):
            sm.transition(WorkflowState.COMPLETED)

    def test_pending_to_failed_raises(self):
        sm = _make_sm()
        with pytest.raises(InvalidTransitionError):
            sm.transition(WorkflowState.FAILED)

    def test_completed_to_running_raises(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.COMPLETED)
        with pytest.raises(InvalidTransitionError):
            sm.transition(WorkflowState.RUNNING)

    def test_failed_to_running_raises(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.FAILED)
        with pytest.raises(InvalidTransitionError):
            sm.transition(WorkflowState.RUNNING)

    def test_invalid_transition_error_contains_states(self):
        sm = _make_sm()
        try:
            sm.transition(WorkflowState.COMPLETED)
        except InvalidTransitionError as e:
            assert "PENDING" in str(e)
            assert "COMPLETED" in str(e)

    def test_running_to_pending_raises(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        with pytest.raises(InvalidTransitionError):
            sm.transition(WorkflowState.PENDING)


# ─────────────────────────────────────────────
# Checkpoints
# ─────────────────────────────────────────────

class TestCheckpoints:
    def test_save_checkpoint_returns_checkpoint(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        cp = sm.save_checkpoint("stap-1", "output van stap 1")
        assert isinstance(cp, Checkpoint)
        assert cp.step_name == "stap-1"
        assert cp.step_output == "output van stap 1"
        assert cp.workflow_id == "WF-TEST"

    def test_get_latest_checkpoint_returns_last(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.save_checkpoint("stap-1", "output 1")
        cp2 = sm.save_checkpoint("stap-2", "output 2")
        latest = sm.get_latest_checkpoint()
        assert latest is not None
        assert latest.checkpoint_id == cp2.checkpoint_id

    def test_restore_from_checkpoint_restores_state(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        cp = sm.save_checkpoint("stap-1", "output 1")
        sm.transition(WorkflowState.CHECKPOINT)
        result = sm.restore_from_checkpoint(cp.checkpoint_id)
        assert result is True
        assert sm.current_state == WorkflowState.RUNNING  # toestand in cp was RUNNING

    def test_restore_nonexistent_checkpoint_returns_false(self):
        sm = _make_sm()
        assert sm.restore_from_checkpoint("nonexistent-id") is False

    def test_checkpoint_metadata_stored(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        cp = sm.save_checkpoint("stap-1", "output", metadata={"extra": "data"})
        assert cp.metadata == {"extra": "data"}


# ─────────────────────────────────────────────
# HITL flow
# ─────────────────────────────────────────────

class TestHitlFlow:
    def test_trigger_hitl_sets_awaiting_human(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.trigger_hitl("hoog risico gedetecteerd", risk_score=85)
        assert sm.current_state == WorkflowState.AWAITING_HUMAN

    def test_trigger_hitl_returns_event(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        from ollama.events import HitlRequiredEvent
        event = sm.trigger_hitl("test reden", risk_score=50)
        assert isinstance(event, HitlRequiredEvent)
        assert event.reason == "test reden"
        assert event.risk_score == 50

    def test_approve_hitl_sets_running(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.trigger_hitl("review")
        sm.approve_hitl(approver_id="user-123")
        assert sm.current_state == WorkflowState.RUNNING

    def test_reject_hitl_sets_failed(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.trigger_hitl("review")
        sm.reject_hitl(reason="niet goedgekeurd")
        assert sm.current_state == WorkflowState.FAILED

    def test_hitl_from_checkpoint_state(self):
        sm = _make_sm()
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.CHECKPOINT)
        sm.transition(WorkflowState.AWAITING_HUMAN, reason="hoog risico")
        assert sm.current_state == WorkflowState.AWAITING_HUMAN


# ─────────────────────────────────────────────
# Happy path end-to-end
# ─────────────────────────────────────────────

class TestHappyPath:
    def test_complete_workflow_without_hitl(self):
        """PENDING → RUNNING → CHECKPOINT → RUNNING → COMPLETED."""
        sm = _make_sm("WF-HAPPY-01")
        sm.transition(WorkflowState.RUNNING, "start")
        cp = sm.save_checkpoint("stap-1", "resultaat stap 1")
        sm.transition(WorkflowState.CHECKPOINT, "stap 1 klaar")
        sm.transition(WorkflowState.RUNNING, "doorgaan")
        sm.transition(WorkflowState.COMPLETED, "workflow klaar")

        assert sm.current_state == WorkflowState.COMPLETED
        assert len(sm.history) == 5  # PENDING + 4 transities
        latest = sm.get_latest_checkpoint()
        assert latest.checkpoint_id == cp.checkpoint_id

    def test_complete_workflow_with_hitl_approval(self):
        """PENDING → RUNNING → AWAITING_HUMAN → RUNNING → COMPLETED."""
        sm = _make_sm("WF-HITL-01")
        sm.transition(WorkflowState.RUNNING, "start")
        sm.trigger_hitl("hoog risico", risk_score=90)
        assert sm.current_state == WorkflowState.AWAITING_HUMAN
        sm.approve_hitl("reviewer-abc")
        assert sm.current_state == WorkflowState.RUNNING
        sm.transition(WorkflowState.COMPLETED, "goedgekeurd en afgerond")
        assert sm.current_state == WorkflowState.COMPLETED

    def test_history_records_all_transitions(self):
        sm = _make_sm("WF-HIST-01")
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.CHECKPOINT)
        sm.transition(WorkflowState.RUNNING)
        sm.transition(WorkflowState.COMPLETED)

        states = [h[0] for h in sm.history]
        assert states == [
            WorkflowState.PENDING,
            WorkflowState.RUNNING,
            WorkflowState.CHECKPOINT,
            WorkflowState.RUNNING,
            WorkflowState.COMPLETED,
        ]
