"""
VorstersNV Workflow State Machine
State machine voor workflow execution met HITL checkpointing.

Gebruik:
    from ollama.state_machine import WorkflowStateMachine, WorkflowState

    sm = WorkflowStateMachine(workflow_id="WF-001", trace_id="trace-abc")
    sm.transition(WorkflowState.RUNNING)
    cp = sm.save_checkpoint("stap-1", "output van stap 1")
    sm.transition(WorkflowState.CHECKPOINT)
    sm.transition(WorkflowState.RUNNING)
    sm.transition(WorkflowState.COMPLETED)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..core.events import EventBus, HitlRequiredEvent, get_event_bus

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# WorkflowState
# ─────────────────────────────────────────────

class WorkflowState(str, Enum):
    """Mogelijke toestanden in de workflow lifecycle."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CHECKPOINT = "CHECKPOINT"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Toegestane state transities
_VALID_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.PENDING:         {WorkflowState.RUNNING},
    WorkflowState.RUNNING:         {
        WorkflowState.CHECKPOINT,
        WorkflowState.AWAITING_HUMAN,
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
    },
    WorkflowState.CHECKPOINT:      {WorkflowState.RUNNING, WorkflowState.AWAITING_HUMAN},
    WorkflowState.AWAITING_HUMAN:  {WorkflowState.RUNNING, WorkflowState.FAILED},
    WorkflowState.COMPLETED:       set(),  # eindtoestand
    WorkflowState.FAILED:          set(),  # eindtoestand
}


# ─────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────

class InvalidTransitionError(Exception):
    """Raised wanneer een ongeldige state transitie wordt geprobeerd."""

    def __init__(self, from_state: WorkflowState, to_state: WorkflowState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Ongeldige transitie: {from_state.value} → {to_state.value}"
        )


# ─────────────────────────────────────────────
# Checkpoint
# ─────────────────────────────────────────────

@dataclass
class Checkpoint:
    """
    Snapshot van de workflow toestand op een bepaald moment.

    # TODO: Persisteer naar PostgreSQL tabel workflow_checkpoints met kolommen:
    #   checkpoint_id TEXT PRIMARY KEY,
    #   workflow_id   TEXT NOT NULL,
    #   state         TEXT NOT NULL,
    #   step_name     TEXT NOT NULL,
    #   step_output   TEXT,
    #   trace_id      TEXT,
    #   timestamp     TIMESTAMPTZ NOT NULL,
    #   metadata      JSONB
    """
    checkpoint_id: str
    workflow_id: str
    state: WorkflowState
    step_name: str
    step_output: str
    trace_id: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────
# WorkflowStateMachine
# ─────────────────────────────────────────────

class WorkflowStateMachine:
    """
    State machine voor workflow execution met HITL checkpointing.

    Ondersteunt:
    - State transities met validatie
    - Checkpoint opslaan en herstellen
    - HITL trigger/approve/reject
    - Geschiedenis van transities
    """

    def __init__(
        self,
        workflow_id: str,
        trace_id: str = "",
        event_bus: EventBus | None = None,
    ) -> None:
        self._workflow_id = workflow_id
        self._trace_id = trace_id or str(uuid.uuid4())
        self._state = WorkflowState.PENDING
        self._history: list[tuple[WorkflowState, str, datetime]] = [
            (WorkflowState.PENDING, "initialisatie", datetime.now(timezone.utc))
        ]
        # In-memory checkpoint opslag
        # TODO: vervang door PostgreSQL tabel workflow_checkpoints
        self._checkpoints: dict[str, Checkpoint] = {}
        self._event_bus = event_bus or get_event_bus()

        logger.info(
            "WorkflowStateMachine aangemaakt: workflow_id=%s trace_id=%s",
            self._workflow_id, self._trace_id,
        )

    # ── Properties ──────────────────────────────

    @property
    def current_state(self) -> WorkflowState:
        """De huidige toestand van de workflow."""
        return self._state

    @property
    def history(self) -> list[tuple[WorkflowState, str, datetime]]:
        """Lijst van (state, reden, tijdstip) tuples in chronologische volgorde."""
        return list(self._history)

    # ── Transities ──────────────────────────────

    def transition(self, new_state: WorkflowState, reason: str = "") -> bool:
        """
        Voer een state transitie uit.

        Args:
            new_state: De gewenste nieuwe state
            reason:    Optionele reden voor de transitie

        Returns:
            True bij succes

        Raises:
            InvalidTransitionError: Als de transitie niet toegestaan is
        """
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise InvalidTransitionError(self._state, new_state)

        old_state = self._state
        self._state = new_state
        self._history.append((new_state, reason, datetime.now(timezone.utc)))

        logger.info(
            "Workflow %s: %s → %s (reden: %s)",
            self._workflow_id, old_state.value, new_state.value, reason or "-",
        )
        return True

    # ── Checkpoints ─────────────────────────────

    def save_checkpoint(
        self,
        step_name: str,
        output: str,
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """
        Sla een checkpoint op voor de huidige stap.

        Args:
            step_name: Naam van de stap
            output:    Output van de stap
            metadata:  Optionele extra metadata

        Returns:
            Het opgeslagen Checkpoint object
        """
        checkpoint_id = str(uuid.uuid4())
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            workflow_id=self._workflow_id,
            state=self._state,
            step_name=step_name,
            step_output=output,
            trace_id=self._trace_id,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        self._checkpoints[checkpoint_id] = checkpoint

        logger.info(
            "Checkpoint opgeslagen: %s voor stap '%s' (workflow=%s)",
            checkpoint_id, step_name, self._workflow_id,
        )
        return checkpoint

    def get_latest_checkpoint(self) -> Checkpoint | None:
        """Geef het meest recente checkpoint terug, of None als er geen zijn."""
        if not self._checkpoints:
            return None
        # Gebruik invoegvolgorde (Python dict is geordend) als primaire sortering,
        # timestamp als secondaire sortering voor het geval meerdere dezelfde volgorde hebben.
        return list(self._checkpoints.values())[-1]

    def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Herstel de workflow vanuit een eerder opgeslagen checkpoint.

        Args:
            checkpoint_id: ID van het te herstellen checkpoint

        Returns:
            True als herstel geslaagd, False als checkpoint niet gevonden
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint is None:
            logger.warning(
                "Checkpoint %s niet gevonden (workflow=%s)",
                checkpoint_id, self._workflow_id,
            )
            return False

        self._state = checkpoint.state
        self._history.append(
            (checkpoint.state, f"hersteld vanuit checkpoint {checkpoint_id}", datetime.now(timezone.utc))
        )

        logger.info(
            "Workflow %s hersteld vanuit checkpoint %s (state=%s, stap=%s)",
            self._workflow_id, checkpoint_id, checkpoint.state.value, checkpoint.step_name,
        )
        return True

    # ── HITL ────────────────────────────────────

    def trigger_hitl(self, reason: str, risk_score: int = 0) -> HitlRequiredEvent:
        """
        Pauzeer de workflow en publiceer een HITL event.

        De state wordt overgezet naar AWAITING_HUMAN.
        Een HitlRequiredEvent wordt gepubliceerd via de EventBus.

        Args:
            reason:     Reden voor de HITL trigger
            risk_score: Risicoscore (0-100) die de urgentie aangeeft

        Returns:
            Het gepubliceerde HitlRequiredEvent
        """
        latest = self.get_latest_checkpoint()
        checkpoint_id = latest.checkpoint_id if latest else ""

        self.transition(WorkflowState.AWAITING_HUMAN, reason=reason)

        event = HitlRequiredEvent(
            trace_id=self._trace_id,
            reason=reason,
            risk_score=risk_score,
            workflow_checkpoint_id=checkpoint_id,
        )

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._event_bus.publish(event))
            else:
                loop.run_until_complete(self._event_bus.publish(event))
        except RuntimeError:
            # Geen event loop beschikbaar — log en ga door
            logger.warning(
                "Geen asyncio event loop beschikbaar voor HITL event publicatie "
                "(workflow=%s)", self._workflow_id,
            )

        logger.info(
            "HITL getriggerd voor workflow %s: reden='%s' risk=%d",
            self._workflow_id, reason, risk_score,
        )
        return event

    def approve_hitl(self, approver_id: str = "") -> bool:
        """
        Verwerk menselijke goedkeuring — zet state terug naar RUNNING.

        Args:
            approver_id: Optionele identifier van de goedkeurder

        Returns:
            True als de transitie geslaagd is
        """
        reason = f"goedgekeurd door '{approver_id}'" if approver_id else "goedgekeurd"
        result = self.transition(WorkflowState.RUNNING, reason=reason)
        logger.info(
            "HITL goedgekeurd voor workflow %s (%s)",
            self._workflow_id, reason,
        )
        return result

    def reject_hitl(self, reason: str = "") -> bool:
        """
        Verwerk menselijke afwijzing — zet state naar FAILED.

        Args:
            reason: Reden voor afwijzing

        Returns:
            True als de transitie geslaagd is
        """
        full_reason = f"afgewezen: {reason}" if reason else "afgewezen"
        result = self.transition(WorkflowState.FAILED, reason=full_reason)
        logger.info(
            "HITL afgewezen voor workflow %s (%s)",
            self._workflow_id, full_reason,
        )
        return result
