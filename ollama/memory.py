"""
VorstersNV Memory Management — Versioned Context Injection (f3-09)
Manages conversation turns with auto-summarization and versioned context assembly.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class TurnRecord:
    role: str  # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class MemorySummary:
    summary: str
    turn_count: int
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = ""

    def __post_init__(self):
        self.version = hashlib.sha256(self.summary.encode()).hexdigest()[:8]


@dataclass
class VersionedContext:
    """Assembled context with version tracking."""
    domain_rules: str = ""
    task_context: str = ""
    tool_results: list[str] = field(default_factory=list)
    memory_summary: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"

    def to_prompt_sections(self) -> list[str]:
        """Returns ordered context sections with delimiters."""
        sections = []
        if self.domain_rules:
            sections.append(f"[DOMAIN_RULES v{self.version}]\n{self.domain_rules}\n[/DOMAIN_RULES]")
        if self.memory_summary:
            sections.append(f"[MEMORY]\n{self.memory_summary}\n[/MEMORY]")
        if self.task_context:
            sections.append(f"[TASK_CONTEXT]\n{self.task_context}\n[/TASK_CONTEXT]")
        for i, result in enumerate(self.tool_results):
            sections.append(f"[TOOL_RESULT_{i+1}]\n{result}\n[/TOOL_RESULT_{i+1}]")
        return sections

    def assemble(self) -> str:
        return "\n\n".join(self.to_prompt_sections())


class SessionMemory:
    """Manages conversation turns with auto-summarization after 10 turns."""

    MAX_TURNS_BEFORE_SUMMARY = 10

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._turns: list[TurnRecord] = []
        self._summaries: list[MemorySummary] = []

    def add_turn(self, role: str, content: str):
        self._turns.append(TurnRecord(role=role, content=content))
        if len(self._turns) >= self.MAX_TURNS_BEFORE_SUMMARY:
            self._summarize()

    def _summarize(self):
        """Auto-summarizes turns when limit reached."""
        if not self._turns:
            return
        lines = [f"{t.role}: {t.content[:100]}..." for t in self._turns]
        summary_text = f"Samenvatting van {len(self._turns)} gespreksbeurten:\n" + "\n".join(lines)
        self._summaries.append(MemorySummary(summary=summary_text, turn_count=len(self._turns)))
        self._turns = []

    def get_context_summary(self) -> Optional[str]:
        """Returns most recent summary if available."""
        if self._summaries:
            return self._summaries[-1].summary
        return None

    def get_recent_turns(self, n: int = 3) -> list[TurnRecord]:
        return self._turns[-n:] if self._turns else []

    def get_turn_count(self) -> int:
        return len(self._turns) + sum(s.turn_count for s in self._summaries)

    def clear(self):
        self._turns = []
        self._summaries = []


class ContextAssembler:
    """Assembles versioned context for agent injection."""

    DOMAIN_RULES = """
VorstersNV e-commerce regels:
- BTW België: 21% (standaard), 6% (voeding/boeken), 0% (export buiten EU)
- Fraude drempel: score >= 75 blokkeert order automatisch
- Mollie betalingsstatussen: paid, pending, failed, expired, canceled, refunded
- GDPR: geen persoonsgegevens in logs of traces
""".strip()

    def __init__(self, version: str = "1.0"):
        self.version = version
        self._sessions: dict[str, SessionMemory] = {}

    def get_session(self, session_id: str) -> SessionMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id)
        return self._sessions[session_id]

    def assemble(
        self,
        task_context: str,
        session_id: Optional[str] = None,
        tool_results: Optional[list[str]] = None,
        domain_rules: Optional[str] = None,
    ) -> VersionedContext:
        memory_summary = None
        if session_id:
            session = self.get_session(session_id)
            memory_summary = session.get_context_summary()

        ctx = VersionedContext(
            domain_rules=domain_rules or self.DOMAIN_RULES,
            task_context=task_context,
            tool_results=tool_results or [],
            memory_summary=memory_summary,
            version=self.version,
        )
        return ctx

    def record_turn(self, session_id: str, role: str, content: str):
        self.get_session(session_id).add_turn(role, content)


def get_context_assembler() -> ContextAssembler:
    global _assembler
    if _assembler is None:
        _assembler = ContextAssembler()
    return _assembler


_assembler: Optional[ContextAssembler] = None
