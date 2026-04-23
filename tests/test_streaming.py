"""
Tests voor api/routers/streaming.py  –  W6-02 SSE streaming endpoint.

Getest:
- EventStore.publish / get_last_event / cleanup (unit)
- EventStore.subscribe generator (unit, incl. terminatie-events)
- POST /api/analyse/events/{trace_id}  → 202 Accepted
- GET  /api/analyse/status/{trace_id}  → 200 / 404
- GET  /api/analyse/stream/{trace_id}  → SSE-frames
- SSE-stream eindigt na pipeline_done / pipeline_error
- SSE-frame serialisatie (data: prefix, dubbele newline)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from api.routers.streaming import EventStore, StreamEvent, _event_store


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
async def bare_client() -> AsyncClient:
    """AsyncClient zonder database-override — streaming endpoints gebruiken geen DB."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture()
def fresh_store() -> EventStore:
    """Geïsoleerde EventStore voor unit-tests (niet de module-singleton)."""
    return EventStore()


# ── Helperfuncties ────────────────────────────────────────────────────────────


def _make_event(
    event_type: str = "pipeline_started",
    trace_id: str = "trace-001",
    payload: dict | None = None,
) -> StreamEvent:
    return StreamEvent(
        event=event_type,  # type: ignore[arg-type]
        trace_id=trace_id,
        payload=payload or {},
    )


# ── Unit-tests: StreamEvent model ─────────────────────────────────────────────


class TestStreamEvent:
    def test_default_timestamp_is_utc(self) -> None:
        ev = _make_event()
        assert ev.timestamp.tzinfo is not None

    def test_to_sse_line_format(self) -> None:
        """SSE-frame moet beginnen met 'data: ' en eindigen met dubbele newline."""
        ev = _make_event(event_type="pipeline_started", trace_id="t-1")
        line = ev.to_sse_line()
        assert line.startswith("data: ")
        assert line.endswith("\n\n")

    def test_to_sse_line_contains_valid_json(self) -> None:
        ev = _make_event(event_type="scan_completed", payload={"bestandsaantal": 5})
        raw = ev.to_sse_line()[len("data: "):].strip()
        parsed = json.loads(raw)
        assert parsed["event"] == "scan_completed"
        assert parsed["payload"]["bestandsaantal"] == 5
        assert parsed["trace_id"] is not None

    def test_all_event_types_are_valid(self) -> None:
        valid_types = [
            "pipeline_started",
            "scan_completed",
            "chunk_processed",
            "pii_detected",
            "rapport_ready",
            "pipeline_error",
            "pipeline_done",
        ]
        for et in valid_types:
            ev = StreamEvent(event=et, trace_id="x")  # type: ignore[arg-type]
            assert ev.event == et

    def test_invalid_event_type_raises(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            StreamEvent(event="onbekend_event", trace_id="x")  # type: ignore[arg-type]


# ── Unit-tests: EventStore ─────────────────────────────────────────────────────


class TestEventStore:
    async def test_get_last_event_none_voor_onbekende_trace(
        self, fresh_store: EventStore
    ) -> None:
        assert fresh_store.get_last_event("niet-bestaat") is None

    async def test_publish_slaat_last_event_op(self, fresh_store: EventStore) -> None:
        ev = _make_event(trace_id="t-100")
        await fresh_store.publish("t-100", ev)
        assert fresh_store.get_last_event("t-100") is ev

    async def test_publish_maakt_queue_aan(self, fresh_store: EventStore) -> None:
        ev = _make_event(trace_id="t-200")
        await fresh_store.publish("t-200", ev)
        assert "t-200" in fresh_store._queues

    async def test_cleanup_verwijdert_queue(self, fresh_store: EventStore) -> None:
        ev = _make_event(trace_id="t-300")
        await fresh_store.publish("t-300", ev)
        fresh_store.cleanup("t-300")
        assert "t-300" not in fresh_store._queues

    async def test_cleanup_bewaart_last_event(self, fresh_store: EventStore) -> None:
        ev = _make_event(trace_id="t-400")
        await fresh_store.publish("t-400", ev)
        fresh_store.cleanup("t-400")
        # last_event blijft bewaard voor status-lookups
        assert fresh_store.get_last_event("t-400") is ev

    async def test_cleanup_onbekende_trace_is_veilig(
        self, fresh_store: EventStore
    ) -> None:
        fresh_store.cleanup("bestaat-niet")  # mag geen exception gooien

    async def test_subscribe_levert_gepubliceerde_events(
        self, fresh_store: EventStore
    ) -> None:
        trace = "t-sub-1"
        events_to_send = [
            _make_event("pipeline_started", trace),
            _make_event("scan_completed", trace),
            _make_event("pipeline_done", trace),
        ]

        # Publiceer alle events vóór subscribe
        for ev in events_to_send:
            await fresh_store.publish(trace, ev)

        received: list[StreamEvent] = []
        async for ev in fresh_store.subscribe(trace):
            received.append(ev)

        assert len(received) == 3
        assert received[0].event == "pipeline_started"
        assert received[2].event == "pipeline_done"

    async def test_subscribe_stopt_na_pipeline_error(
        self, fresh_store: EventStore
    ) -> None:
        trace = "t-sub-err"
        await fresh_store.publish(trace, _make_event("pipeline_started", trace))
        await fresh_store.publish(trace, _make_event("pipeline_error", trace))
        # Extra event ná terminatie-event moet NIET geleverd worden
        await fresh_store.publish(trace, _make_event("pipeline_done", trace))

        received: list[StreamEvent] = []
        async for ev in fresh_store.subscribe(trace):
            received.append(ev)

        # Stopt bij pipeline_error — pipeline_done erna wordt niet geleverd
        assert received[-1].event == "pipeline_error"
        assert len(received) == 2

    async def test_concurrent_publish_en_subscribe(
        self, fresh_store: EventStore
    ) -> None:
        """Publisher en subscriber draaien concurrent via asyncio.gather."""
        trace = "t-concurrent"
        collected: list[StreamEvent] = []

        async def producer() -> None:
            for i in range(3):
                await fresh_store.publish(
                    trace,
                    _make_event("chunk_processed", trace, {"chunk_nr": i}),
                )
                await asyncio.sleep(0)  # yield naar event-loop
            await fresh_store.publish(trace, _make_event("pipeline_done", trace))

        async def consumer() -> None:
            async for ev in fresh_store.subscribe(trace):
                collected.append(ev)

        await asyncio.gather(producer(), consumer())
        assert len(collected) == 4
        assert collected[-1].event == "pipeline_done"


# ── Integratietests: POST /api/analyse/events/{trace_id} ─────────────────────


class TestPublishEndpoint:
    async def test_202_bij_geldig_event(self, bare_client: AsyncClient) -> None:
        trace = "int-pub-1"
        r = await bare_client.post(
            f"/api/analyse/events/{trace}",
            json={"event": "pipeline_started", "payload": {}},
        )
        assert r.status_code == 202
        data = r.json()
        assert data["trace_id"] == trace
        assert data["event"] == "pipeline_started"

    async def test_202_met_payload(self, bare_client: AsyncClient) -> None:
        trace = "int-pub-2"
        r = await bare_client.post(
            f"/api/analyse/events/{trace}",
            json={
                "event": "scan_completed",
                "payload": {"bestandsaantal": 42, "talen": ["Python", "SQL"]},
            },
        )
        assert r.status_code == 202

    async def test_422_bij_ongeldig_event_type(self, bare_client: AsyncClient) -> None:
        r = await bare_client.post(
            "/api/analyse/events/invalid-trace",
            json={"event": "dit_bestaat_niet", "payload": {}},
        )
        assert r.status_code == 422

    async def test_422_zonder_event_veld(self, bare_client: AsyncClient) -> None:
        r = await bare_client.post(
            "/api/analyse/events/trace-missing",
            json={"payload": {}},
        )
        assert r.status_code == 422

    async def test_alle_event_types_worden_geaccepteerd(
        self, bare_client: AsyncClient
    ) -> None:
        valid_types = [
            "pipeline_started",
            "scan_completed",
            "chunk_processed",
            "pii_detected",
            "rapport_ready",
            "pipeline_error",
            "pipeline_done",
        ]
        for et in valid_types:
            r = await bare_client.post(
                f"/api/analyse/events/trace-alltype-{et}",
                json={"event": et, "payload": {}},
            )
            assert r.status_code == 202, f"Verwacht 202 voor event type '{et}'"


# ── Integratietests: GET /api/analyse/status/{trace_id} ──────────────────────


class TestStatusEndpoint:
    async def test_404_voor_onbekende_trace(self, bare_client: AsyncClient) -> None:
        r = await bare_client.get("/api/analyse/status/bestaat-helemaal-niet-xyz")
        assert r.status_code == 404
        assert "bestaat-helemaal-niet-xyz" in r.json()["detail"]

    async def test_200_na_publish(self, bare_client: AsyncClient) -> None:
        trace = "int-status-1"
        # Publiceer via POST endpoint
        await bare_client.post(
            f"/api/analyse/events/{trace}",
            json={"event": "scan_completed", "payload": {"bestandsaantal": 7}},
        )

        r = await bare_client.get(f"/api/analyse/status/{trace}")
        assert r.status_code == 200
        data = r.json()
        assert data["trace_id"] == trace
        assert data["last_event"]["event"] == "scan_completed"
        assert data["last_event"]["payload"]["bestandsaantal"] == 7

    async def test_geeft_meest_recente_event(self, bare_client: AsyncClient) -> None:
        trace = "int-status-latest"
        for event_type in ("pipeline_started", "scan_completed", "rapport_ready"):
            await bare_client.post(
                f"/api/analyse/events/{trace}",
                json={"event": event_type, "payload": {}},
            )

        r = await bare_client.get(f"/api/analyse/status/{trace}")
        assert r.status_code == 200
        # Laatste gepubliceerde event moet terug
        assert r.json()["last_event"]["event"] == "rapport_ready"

    async def test_response_bevat_timestamp(self, bare_client: AsyncClient) -> None:
        trace = "int-status-ts"
        await bare_client.post(
            f"/api/analyse/events/{trace}",
            json={"event": "pipeline_started", "payload": {}},
        )
        r = await bare_client.get(f"/api/analyse/status/{trace}")
        assert r.status_code == 200
        ts = r.json()["last_event"]["timestamp"]
        # Moet parseerbaar zijn als ISO-datetime
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo is not None


# ── Integratietests: GET /api/analyse/stream/{trace_id} ──────────────────────


class TestStreamEndpoint:
    async def test_stream_headers_zijn_correct(self, bare_client: AsyncClient) -> None:
        """
        Verifieer Content-Type en SSE-control headers.
        We publiceren onmiddellijk pipeline_done zodat de stream sluit.
        """
        trace = "int-stream-headers"

        # Pre-publiceer pipeline_done zodat de stream meteen sluit
        await _event_store.publish(trace, _make_event("pipeline_done", trace))

        async with bare_client.stream("GET", f"/api/analyse/stream/{trace}") as resp:
            assert resp.status_code == 200
            ct = resp.headers.get("content-type", "")
            assert "text/event-stream" in ct
            assert resp.headers.get("cache-control") == "no-cache"
            assert resp.headers.get("x-accel-buffering") == "no"

    async def test_stream_levert_sse_frames(self, bare_client: AsyncClient) -> None:
        """Events moeten als 'data: ...\\n\\n' frames binnenkomen."""
        trace = "int-stream-frames"

        await _event_store.publish(trace, _make_event("pipeline_started", trace))
        await _event_store.publish(trace, _make_event("pipeline_done", trace))

        frames: list[str] = []
        async with bare_client.stream("GET", f"/api/analyse/stream/{trace}") as resp:
            assert resp.status_code == 200
            async for chunk in resp.aiter_text():
                frames.append(chunk)

        combined = "".join(frames)
        # Elk SSE-frame begint met "data: "
        assert "data: " in combined
        # Elk frame eindigt met dubbele newline
        parts = [p for p in combined.split("\n\n") if p.strip()]
        assert len(parts) >= 1

    async def test_stream_frame_bevat_geldig_json(
        self, bare_client: AsyncClient
    ) -> None:
        trace = "int-stream-json"

        payload = {"bestandsaantal": 10, "talen": ["Python"]}
        await _event_store.publish(
            trace,
            StreamEvent(event="scan_completed", trace_id=trace, payload=payload),
        )
        await _event_store.publish(trace, _make_event("pipeline_done", trace))

        raw_frames: list[str] = []
        async with bare_client.stream("GET", f"/api/analyse/stream/{trace}") as resp:
            async for chunk in resp.aiter_text():
                raw_frames.append(chunk)

        combined = "".join(raw_frames)
        for line in combined.strip().split("\n\n"):
            line = line.strip()
            if not line:
                continue
            assert line.startswith("data: "), f"Frame begint niet met 'data: ': {line!r}"
            parsed = json.loads(line[len("data: "):])
            assert "event" in parsed
            assert "trace_id" in parsed
            assert "timestamp" in parsed
            assert "payload" in parsed

    async def test_stream_eindigt_na_pipeline_done(
        self, bare_client: AsyncClient
    ) -> None:
        """Stream moet afsluiten zodra pipeline_done ontvangen is."""
        trace = "int-stream-done"

        await _event_store.publish(trace, _make_event("pipeline_started", trace))
        await _event_store.publish(trace, _make_event("pipeline_done", trace))

        event_types: list[str] = []
        async with bare_client.stream("GET", f"/api/analyse/stream/{trace}") as resp:
            async for chunk in resp.aiter_text():
                for line in chunk.strip().split("\n\n"):
                    line = line.strip()
                    if line.startswith("data: "):
                        parsed = json.loads(line[len("data: "):])
                        event_types.append(parsed["event"])

        assert "pipeline_done" in event_types
        # Na pipeline_done mogen er geen verdere events zijn
        done_idx = event_types.index("pipeline_done")
        assert done_idx == len(event_types) - 1, (
            "Er zijn events na pipeline_done ontvangen"
        )

    async def test_stream_eindigt_na_pipeline_error(
        self, bare_client: AsyncClient
    ) -> None:
        trace = "int-stream-error"

        await _event_store.publish(trace, _make_event("pipeline_started", trace))
        await _event_store.publish(
            trace,
            StreamEvent(
                event="pipeline_error",
                trace_id=trace,
                payload={"fout": "Iets ging mis"},
            ),
        )

        event_types: list[str] = []
        async with bare_client.stream("GET", f"/api/analyse/stream/{trace}") as resp:
            async for chunk in resp.aiter_text():
                for line in chunk.strip().split("\n\n"):
                    line = line.strip()
                    if line.startswith("data: "):
                        parsed = json.loads(line[len("data: "):])
                        event_types.append(parsed["event"])

        assert "pipeline_error" in event_types
        assert event_types[-1] == "pipeline_error"

    async def test_publish_en_stream_concurrent(
        self, bare_client: AsyncClient
    ) -> None:
        """
        Simuleer een echte pipeline: events worden gepubliceerd terwijl
        de client al luistert.
        """
        trace = "int-stream-concurrent"
        received_events: list[str] = []

        async def pipeline() -> None:
            await asyncio.sleep(0.05)
            for et in ("pipeline_started", "scan_completed", "chunk_processed"):
                await _event_store.publish(trace, _make_event(et, trace))
                await asyncio.sleep(0.02)
            await _event_store.publish(trace, _make_event("pipeline_done", trace))

        async def listener() -> None:
            async with bare_client.stream(
                "GET", f"/api/analyse/stream/{trace}"
            ) as resp:
                async for chunk in resp.aiter_text():
                    for line in chunk.strip().split("\n\n"):
                        line = line.strip()
                        if line.startswith("data: "):
                            parsed = json.loads(line[len("data: "):])
                            received_events.append(parsed["event"])

        await asyncio.gather(pipeline(), listener())

        assert "pipeline_started" in received_events
        assert "pipeline_done" in received_events
        assert received_events[-1] == "pipeline_done"
