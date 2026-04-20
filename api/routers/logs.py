"""
VorstersNV Logs API Router
Geeft recente applicatielog-entries terug voor het dashboard.
"""
import logging
import sys
from collections import deque
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory ring buffer voor recente log regels (max 200)
_LOG_BUFFER: deque[dict] = deque(maxlen=200)


class LogEntry(BaseModel):
    tijd: str
    level: str
    bericht: str
    bron: str


class _BufferHandler(logging.Handler):
    """Logging handler die entries toevoegt aan de in-memory ring buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _LOG_BUFFER.append({
                "tijd": datetime.fromtimestamp(record.created, tz=timezone.utc)
                        .strftime("%H:%M:%S"),
                "level": record.levelname,
                "bericht": self.format(record),
                "bron": record.name.split(".")[-1],
            })
        except Exception:  # noqa: BLE001
            pass


def setup_log_buffer(app_logger: logging.Logger | None = None) -> None:
    """Registreer de buffer handler op de root logger (eenmalig bij startup)."""
    handler = _BufferHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.INFO)
    root = app_logger or logging.getLogger()
    # Alleen toevoegen als nog niet aanwezig
    if not any(isinstance(h, _BufferHandler) for h in root.handlers):
        root.addHandler(handler)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/recent",
    response_model=list[LogEntry],
    summary="Recente log-entries",
    description=(
        "Haal de laatste N applicatielog-regels op. "
        "Openbaar endpoint — geen gevoelige data in logs opnemen."
    ),
)
async def recente_logs(limiet: int = 20) -> list[LogEntry]:
    """Geeft de recentste log-entries terug, nieuwste bovenaan."""
    entries = list(_LOG_BUFFER)[-limiet:]
    entries.reverse()
    return [LogEntry(**e) for e in entries]
