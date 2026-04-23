"""
VorstersNV Streaming API Router  –  W6-02
==========================================
SSE (Server-Sent Events) endpoint voor real-time analyse-voortgang.

Protocol
--------
Elke SSE-event heeft het formaat::

    data: {"event": "...", "trace_id": "...", "payload": {...}, "timestamp": "..."}
    <lege regel>

EventStore (in-memory singleton) beheert één asyncio.Queue per actieve trace_id.
De pipeline publiceert events via POST /api/analyse/events/{trace_id}.
Clients luisteren via GET /api/analyse/stream/{trace_id}.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── Constanten ────────────────────────────────────────────────────────────────

# Maximaal wachten op een nieuw event voordat de stream sluit (seconden)
_STREAM_TIMEOUT_SECONDS: int = 300  # 5 minuten

# Maximum aantal events dat gebufferd wordt per trace (backpressure)
_QUEUE_MAX_SIZE: int = 256

# ── Pydantic-modellen ─────────────────────────────────────────────────────────

EventType = Literal[
    "pipeline_started",
    "scan_completed",
    "chunk_processed",
    "pii_detected",
    "rapport_ready",
    "pipeline_error",
    "pipeline_done",
]


class StreamEvent(BaseModel):
    """Volledig SSE-event zoals het de queue ingaat en naar de client gaat."""

    event: EventType
    trace_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    model_config = {"from_attributes": True}

    def to_sse_line(self) -> str:
        """Serialiseer naar een SSE-frame: ``data: <json>\\n\\n``."""
        return f"data: {self.model_dump_json()}\n\n"


class StreamEventRequest(BaseModel):
    """
    Body voor POST /api/analyse/events/{trace_id}.

    Vereenvoudigd model dat de pipeline gebruikt om events te publiceren.
    Het ``event``-veld mag elke geldige EventType-waarde zijn;
    validatie vindt plaats bij omzetting naar :class:`StreamEvent`.
    """

    event: EventType
    payload: dict[str, Any] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    """Antwoord op GET /api/analyse/status/{trace_id}."""

    trace_id: str
    last_event: StreamEvent


# ── EventStore ────────────────────────────────────────────────────────────────


class EventStore:
    """
    In-memory event-bus op basis van asyncio.Queue.

    Eén queue per actieve trace_id.  Zodra de SSE-verbinding sluit
    (via :meth:`cleanup`) wordt de queue verwijderd.

    Thread-safety: asyncio is single-threaded; alle methoden zijn safe
    zolang ze vanuit dezelfde event-loop worden aangeroepen.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[StreamEvent]] = {}
        self._last_event: dict[str, StreamEvent] = {}

    # ── Publiceren ────────────────────────────────────────────────────────────

    async def publish(self, trace_id: str, event: StreamEvent) -> None:
        """
        Voeg *event* toe aan de queue van *trace_id*.

        Als er nog geen queue bestaat wordt die aangemaakt (lazy init).
        Dit maakt het mogelijk dat de pipeline events stuurt vóórdat
        een client verbinding heeft gemaakt.
        """
        if trace_id not in self._queues:
            self._queues[trace_id] = asyncio.Queue(maxsize=_QUEUE_MAX_SIZE)
            logger.debug("EventStore: nieuwe queue aangemaakt voor trace_id=%s", trace_id)

        try:
            self._queues[trace_id].put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(
                "EventStore: queue vol voor trace_id=%s — event=%s weggegooid",
                trace_id,
                event.event,
            )

        self._last_event[trace_id] = event
        logger.debug(
            "EventStore: event gepubliceerd trace_id=%s event=%s",
            trace_id,
            event.event,
        )

    # ── Abonneren ─────────────────────────────────────────────────────────────

    async def subscribe(
        self,
        trace_id: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Async generator die events voor *trace_id* oplevert.

        Blokkeert tot er een event beschikbaar is of tot de timeout
        van :data:`_STREAM_TIMEOUT_SECONDS` verloopt.  Na timeout
        wordt automatisch een ``pipeline_done``-event gegenereerd.

        De generator eindigt altijd na een ``pipeline_done`` of
        ``pipeline_error`` event.

        Gebruik in een ``try/finally``-blok om :meth:`cleanup` zeker
        aan te roepen::

            async for event in store.subscribe(trace_id):
                yield event
        """
        if trace_id not in self._queues:
            self._queues[trace_id] = asyncio.Queue(maxsize=_QUEUE_MAX_SIZE)
            logger.debug(
                "EventStore: subscribe – queue aangemaakt voor trace_id=%s", trace_id
            )

        queue = self._queues[trace_id]

        while True:
            try:
                event = await asyncio.wait_for(
                    queue.get(),
                    timeout=float(_STREAM_TIMEOUT_SECONDS),
                )
            except TimeoutError:
                logger.info(
                    "EventStore: timeout na %ds voor trace_id=%s — stream afsluiten",
                    _STREAM_TIMEOUT_SECONDS,
                    trace_id,
                )
                timeout_event = StreamEvent(
                    event="pipeline_done",
                    trace_id=trace_id,
                    payload={"reden": "timeout", "timeout_seconden": _STREAM_TIMEOUT_SECONDS},
                )
                self._last_event[trace_id] = timeout_event
                yield timeout_event
                return

            yield event

            # Sluit de generator na een terminatie-event
            if event.event in ("pipeline_done", "pipeline_error"):
                logger.info(
                    "EventStore: terminatie-event '%s' voor trace_id=%s — stream sluit",
                    event.event,
                    trace_id,
                )
                return

    # ── Opvragen & opruimen ───────────────────────────────────────────────────

    def get_last_event(self, trace_id: str) -> StreamEvent | None:
        """Geef het laatste bekende event terug, of ``None`` als onbekend."""
        return self._last_event.get(trace_id)

    def cleanup(self, trace_id: str) -> None:
        """
        Verwijder de queue voor *trace_id*.

        Roep dit aan in de ``finally``-clausule van de SSE-generator
        zodat geheugen vrijgegeven wordt na een client-disconnect.
        Het ``_last_event``-record blijft bewaard voor status-lookups.
        """
        queue = self._queues.pop(trace_id, None)
        if queue is not None:
            logger.debug("EventStore: queue opgeruimd voor trace_id=%s", trace_id)


# Module-level singleton – gedeeld door alle requests in dezelfde process
_event_store = EventStore()

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter()


# ── SSE stream endpoint ───────────────────────────────────────────────────────


@router.get(
    "/stream/{trace_id}",
    summary="SSE stream voor analyse-voortgang",
    description=(
        "Opent een Server-Sent Events verbinding voor de opgegeven `trace_id`. "
        "Events worden gestreamd totdat de pipeline klaar is of de verbinding "
        f"na {_STREAM_TIMEOUT_SECONDS} seconden inactiviteit wordt gesloten."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "SSE-stream met analyse-events",
        }
    },
)
async def stream_analyse(
    trace_id: str,
    request: Request,
) -> StreamingResponse:
    """
    Stream real-time analyse-events als SSE.

    De response blijft open totdat:
    - de pipeline ``pipeline_done`` of ``pipeline_error`` publiceert,
    - de stream-timeout verloopt (5 min. inactiviteit), of
    - de client de verbinding verbreekt.
    """

    async def _event_generator() -> AsyncGenerator[str, None]:
        logger.info("SSE stream gestart voor trace_id=%s", trace_id)
        try:
            async for event in _event_store.subscribe(trace_id):
                # Stop zodra de client verbroken heeft (HTTP disconnect)
                if await request.is_disconnected():
                    logger.info(
                        "SSE client verbroken voor trace_id=%s", trace_id
                    )
                    return
                yield event.to_sse_line()
        finally:
            _event_store.cleanup(trace_id)
            logger.info("SSE stream gesloten voor trace_id=%s", trace_id)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Intern publish-endpoint ───────────────────────────────────────────────────

# INTERN ENDPOINT – uitsluitend bestemd voor de analyse-pipeline.
# Geen authenticatie vereist omdat het enkel intern (docker-netwerk /
# localhost) bereikbaar is.  Indien dit ooit publiek wordt, voeg dan
# een API-key of IP-whitelist toe.


@router.post(
    "/events/{trace_id}",
    summary="[INTERN] Publiceer een analyse-event",
    description=(
        "**Intern endpoint** – gebruikt door de analyse-pipeline om voortgang "
        "te publiceren.  Niet bedoeld voor externe clients."
    ),
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Event in de wachtrij geplaatst"},
    },
)
async def publish_event(
    trace_id: str,
    body: StreamEventRequest,
) -> dict[str, str]:
    """
    Voeg een event toe aan de queue voor *trace_id*.

    Gebruikt door de analyse-pipeline om voortgang te rapporteren.
    Returns HTTP 202 zodra het event in de queue staat.
    """
    event = StreamEvent(
        event=body.event,
        trace_id=trace_id,
        payload=body.payload,
    )
    await _event_store.publish(trace_id, event)
    logger.info(
        "Event gepubliceerd via API: trace_id=%s event=%s",
        trace_id,
        body.event,
    )
    return {"status": "geaccepteerd", "trace_id": trace_id, "event": body.event}


# ── Status endpoint ───────────────────────────────────────────────────────────


@router.get(
    "/status/{trace_id}",
    response_model=StatusResponse,
    summary="Laatste bekende status voor een trace",
    responses={
        200: {"description": "Laatste event voor de trace"},
        404: {"description": "Trace-id onbekend — nog geen events gepubliceerd"},
    },
)
async def get_status(trace_id: str) -> StatusResponse:
    """
    Geef het laatste bekende event terug voor *trace_id*.

    Handig voor polling-clients of voor een snelle status-check
    na het opnieuw verbinden.

    Geeft HTTP 404 als er nog geen enkel event voor deze trace is.
    """
    last = _event_store.get_last_event(trace_id)
    if last is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace-id '{trace_id}' onbekend — nog geen events gepubliceerd.",
        )
    return StatusResponse(trace_id=trace_id, last_event=last)
