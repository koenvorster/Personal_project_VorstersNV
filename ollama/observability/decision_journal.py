"""
VorstersNV Decision Journal
Auditeerbaar logboek van alle AI-beslissingen: agent selectie, model keuze,
policy verdicts en human overrides.

Revisie 4 architectuur — OBSERVABILITY laag.

Gebruik:
    from ollama.decision_journal import DecisionJournal, JournalEntry, get_decision_journal

    journal = get_decision_journal()
    entry = JournalEntry(
        capability="fraud-detection",
        agent_name="fraud-agent-v2",
        model_used="llama3",
        verdict="APPROVED",
        risk_score=45,
    )
    trace_id = journal.record(entry)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# TODO: vervang in-memory dict door PostgreSQL tabel `decision_journal`
#   met columns: trace_id (PK), capability, agent_name, model_used,
#   tools_used (jsonb), selection_reason, alternatives_considered (jsonb),
#   human_override, verdict, timestamp, environment, risk_score,
#   execution_time_ms, policy_violations (jsonb)


# ─────────────────────────────────────────────
# Verdict constanten
# ─────────────────────────────────────────────

VERDICT_APPROVED = "APPROVED"
VERDICT_REJECTED = "REJECTED"
VERDICT_REVIEW   = "REVIEW"

_VALID_VERDICTS = {VERDICT_APPROVED, VERDICT_REJECTED, VERDICT_REVIEW}


# ─────────────────────────────────────────────
# JournalEntry
# ─────────────────────────────────────────────

@dataclass
class JournalEntry:
    """
    Één beslissingsrecord — volledig auditeerbaar.

    Elk record beschrijft welke capability werd uitgevoerd, welk model/agent
    gekozen werd, waarom, en wat het verdict was van de policy check.
    """
    capability: str
    agent_name: str
    model_used: str
    verdict: str  # APPROVED | REJECTED | REVIEW

    # Optionele velden met zinvolle defaults
    trace_id: str                     = field(default_factory=lambda: str(uuid.uuid4()))
    tools_used: list[str]             = field(default_factory=list)
    selection_reason: str             = ""
    alternatives_considered: list[str] = field(default_factory=list)
    human_override: bool              = False
    timestamp: datetime               = field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str                  = "local"
    risk_score: float                 = 0.0
    execution_time_ms: float | None   = None
    policy_violations: list[str]      = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.verdict not in _VALID_VERDICTS:
            raise ValueError(
                f"Ongeldig verdict '{self.verdict}'. "
                f"Geldige waarden: {sorted(_VALID_VERDICTS)}"
            )


# ─────────────────────────────────────────────
# DecisionJournal
# ─────────────────────────────────────────────

class DecisionJournal:
    """
    In-memory decision journal voor AI capability beslissingen.

    Biedt audit-functies: opslaan, ophalen, filteren en exporteren van
    beslissingsrecords. De storage is in-memory (dict keyed by trace_id).

    TODO: vervang _store door PostgreSQL-backed repository voor persistentie
    over meerdere instanties en herstarts.
    """

    def __init__(self) -> None:
        self._store: dict[str, JournalEntry] = {}

    def record(self, entry: JournalEntry) -> str:
        """
        Sla een JournalEntry op in het journal.

        Args:
            entry: de te bewaren beslissing.

        Returns:
            trace_id van de opgeslagen entry.
        """
        self._store[entry.trace_id] = entry
        logger.info(
            "Beslissing gelogd: trace_id=%s capability=%s verdict=%s risk=%.1f",
            entry.trace_id, entry.capability, entry.verdict, entry.risk_score,
        )
        return entry.trace_id

    def get(self, trace_id: str) -> JournalEntry | None:
        """
        Haal een entry op via trace_id.

        Returns:
            JournalEntry of None als niet gevonden.
        """
        return self._store.get(trace_id)

    def list_by_capability(self, capability: str) -> list[JournalEntry]:
        """
        Geef alle entries terug voor een bepaalde capability.

        Args:
            capability: naam van de capability (bijv. 'fraud-detection').

        Returns:
            Gesorteerde lijst (oudste eerst) van JournalEntry objecten.
        """
        results = [e for e in self._store.values() if e.capability == capability]
        return sorted(results, key=lambda e: e.timestamp)

    def list_by_verdict(self, verdict: str) -> list[JournalEntry]:
        """
        Geef alle entries terug met een bepaald verdict.

        Args:
            verdict: 'APPROVED', 'REJECTED' of 'REVIEW'.

        Returns:
            Gesorteerde lijst (oudste eerst) van JournalEntry objecten.
        """
        results = [e for e in self._store.values() if e.verdict == verdict]
        return sorted(results, key=lambda e: e.timestamp)

    def export_json(self, trace_id: str) -> dict[str, Any]:
        """
        Exporteer een entry als JSON-compatibel dict voor audit doeleinden.

        Args:
            trace_id: trace_id van de gewenste entry.

        Returns:
            dict met alle velden geserialiseerd (timestamps als ISO string).

        Raises:
            KeyError als trace_id niet bestaat.
        """
        entry = self._store.get(trace_id)
        if entry is None:
            raise KeyError(f"Geen journal entry gevonden voor trace_id='{trace_id}'")

        return {
            "trace_id": entry.trace_id,
            "capability": entry.capability,
            "agent_name": entry.agent_name,
            "model_used": entry.model_used,
            "tools_used": entry.tools_used,
            "selection_reason": entry.selection_reason,
            "alternatives_considered": entry.alternatives_considered,
            "human_override": entry.human_override,
            "verdict": entry.verdict,
            "timestamp": entry.timestamp.isoformat(),
            "environment": entry.environment,
            "risk_score": entry.risk_score,
            "execution_time_ms": entry.execution_time_ms,
            "policy_violations": entry.policy_violations,
        }

    def summary_stats(self) -> dict[str, Any]:
        """
        Geef samenvattingsstatistieken terug: verdicts per capability
        en gemiddelde risicoscore.

        Returns:
            dict met 'verdicts_per_capability', 'avg_risk_score',
            'total_entries' en 'human_overrides'.
        """
        if not self._store:
            return {
                "total_entries": 0,
                "verdicts_per_capability": {},
                "avg_risk_score": 0.0,
                "human_overrides": 0,
            }

        verdicts_per_capability: dict[str, dict[str, int]] = {}
        total_risk = 0.0
        human_overrides = 0

        for entry in self._store.values():
            cap = entry.capability
            if cap not in verdicts_per_capability:
                verdicts_per_capability[cap] = {
                    VERDICT_APPROVED: 0,
                    VERDICT_REJECTED: 0,
                    VERDICT_REVIEW:   0,
                }
            verdicts_per_capability[cap][entry.verdict] = (
                verdicts_per_capability[cap].get(entry.verdict, 0) + 1
            )
            total_risk += entry.risk_score
            if entry.human_override:
                human_overrides += 1

        return {
            "total_entries": len(self._store),
            "verdicts_per_capability": verdicts_per_capability,
            "avg_risk_score": total_risk / len(self._store),
            "human_overrides": human_overrides,
        }

    def clear(self) -> None:
        """Wis alle entries — alleen voor tests bedoeld."""
        self._store.clear()


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

_journal: DecisionJournal | None = None


def get_decision_journal() -> DecisionJournal:
    """Geef de singleton DecisionJournal terug."""
    global _journal
    if _journal is None:
        _journal = DecisionJournal()
    return _journal
