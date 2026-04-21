"""
VorstersNV Agent Tracing
Lightweight structured tracing voor AI-agent aanroepen.

Registreert per agent call:
- latency (ms)
- token gebruik (indien beschikbaar)
- succes/fout
- agent naam + model
- correlation_id voor request tracing

Schrijft naar het standaard logging systeem in JSON-formaat.
Optionele integratie met OpenTelemetry GenAI Semantic Conventions 2025
(https://opentelemetry.io/docs/specs/semconv/gen-ai/) indien geïnstalleerd.
"""
from __future__ import annotations

import functools
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

logger = logging.getLogger("vorstersNV.tracing")

# Singleton legacy OpenTelemetry tracer (None als OTEL niet geïnstalleerd)
_otel_tracer: Any = None

# True als OTEL export is ingeschakeld via env var
OTEL_EXPORT_ENABLED: bool = os.getenv("OTEL_EXPORT_ENABLED", "false").lower() in ("1", "true", "yes")


def _init_otel() -> None:
    """Initialiseer OpenTelemetry tracer indien beschikbaar en export enabled."""
    global _otel_tracer
    if not OTEL_EXPORT_ENABLED:
        logger.debug("OTEL_EXPORT_ENABLED=false — alleen in-memory tracing actief.")
        return
    try:
        from opentelemetry import trace  # type: ignore[import]
        _otel_tracer = trace.get_tracer("vorstersNV.agents", "1.0.0")
        logger.info("OpenTelemetry tracer geïnitialiseerd")
    except ImportError:
        logger.debug(
            "opentelemetry-api niet geïnstalleerd — alleen JSON logging actief. "
            "Installeer met: pip install opentelemetry-api opentelemetry-sdk"
        )


_init_otel()

# ─────────────────────────────────────────────────────────
# Agent group helper
# ─────────────────────────────────────────────────────────

_GROUP_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(fraude|fraud)_", re.IGNORECASE), "RISK_DECISION"),
    (re.compile(r"^(test|unit|integratie)_", re.IGNORECASE), "TEST_INTELLIGENCE"),
    (re.compile(r"^(developer|architect)_", re.IGNORECASE), "DEV_INTELLIGENCE"),
    (re.compile(r"^(klantenservice|customer)_", re.IGNORECASE), "EXPLANATION"),
    (re.compile(r"^audit_", re.IGNORECASE), "AUDIT"),
]


def get_agent_group(agent_name: str) -> str:
    """Bepaal de agent group op basis van de agent naam."""
    for pattern, group in _GROUP_PATTERNS:
        if pattern.match(agent_name):
            return group
    return "DEV_INTELLIGENCE"


# ─────────────────────────────────────────────────────────
# AgentSpan — uitgebreid met events
# ─────────────────────────────────────────────────────────

@dataclass
class AgentSpan:
    """Gegevens van één agent aanroep (span)."""
    trace_id: str
    agent_name: str
    model: str
    start_time: float = field(default_factory=time.monotonic)
    end_time: float | None = None
    latency_ms: float | None = None
    success: bool = True
    error: str | None = None
    input_length: int = 0
    output_length: int = 0
    cached: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    events: list[tuple[str, dict[str, Any], datetime]] = field(default_factory=list)

    def finish(self, output: str = "", error: str | None = None) -> None:
        """Sluit de span af en bereken latency."""
        self.end_time = time.monotonic()
        self.latency_ms = (self.end_time - self.start_time) * 1000
        self.output_length = len(output)
        if error:
            self.success = False
            self.error = error

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Voeg een span event toe."""
        self.events.append((name, attributes or {}, datetime.now(timezone.utc)))

    def to_log_dict(self) -> dict[str, Any]:
        """Converteer naar een dict voor JSON logging."""
        return {
            "event": "agent_call",
            "trace_id": self.trace_id,
            "agent": self.agent_name,
            "model": self.model,
            "latency_ms": round(self.latency_ms or 0, 1),
            "success": self.success,
            "error": self.error,
            "input_chars": self.input_length,
            "output_chars": self.output_length,
            "cached": self.cached,
            **self.metadata,
        }


# ─────────────────────────────────────────────────────────
# AgentTracer — backward compatible
# ─────────────────────────────────────────────────────────

class AgentTracer:
    """
    Tracer voor AI-agent aanroepen.

    Gebruik als context manager of via de `traced_agent_call` decorator.
    """

    def new_trace_id(self) -> str:
        """Genereer een nieuw uniek trace-ID."""
        return str(uuid.uuid4())

    @asynccontextmanager
    async def span(
        self,
        agent_name: str,
        model: str = "",
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[AgentSpan]:
        """
        Async context manager voor het tracen van een agent aanroep.

        Gebruik:
            async with tracer.span("klantenservice_agent", model="llama3") as span:
                span.input_length = len(user_input)
                response = await agent.run(user_input)
                span.finish(output=response)
        """
        current_trace_id = trace_id or self.new_trace_id()
        agent_span = AgentSpan(
            trace_id=current_trace_id,
            agent_name=agent_name,
            model=model,
            metadata=metadata or {},
        )

        otel_span = None
        if _otel_tracer is not None:
            try:
                otel_span = _otel_tracer.start_span(f"agent/{agent_name}")
                otel_span.set_attribute("agent.name", agent_name)
                otel_span.set_attribute("agent.model", model)
                otel_span.set_attribute("trace.id", current_trace_id)
            except Exception:
                pass

        try:
            yield agent_span
        except Exception as exc:
            agent_span.finish(error=str(exc))
            if otel_span:
                try:
                    from opentelemetry.trace import StatusCode  # type: ignore[import]
                    otel_span.set_status(StatusCode.ERROR, str(exc))
                except Exception:
                    pass
            raise
        finally:
            if agent_span.end_time is None:
                agent_span.finish()

            log_data = agent_span.to_log_dict()
            if agent_span.success:
                logger.info("Agent span voltooid: %s", log_data)
            else:
                logger.error("Agent span mislukt: %s", log_data)

            if otel_span:
                try:
                    otel_span.set_attribute("agent.latency_ms", agent_span.latency_ms or 0)
                    otel_span.set_attribute("agent.cached", agent_span.cached)
                    otel_span.end()
                except Exception:
                    pass


# ─────────────────────────────────────────────────────────
# OtelAgentTracer — GenAI Semantic Conventions 2025
# ─────────────────────────────────────────────────────────

@dataclass
class OtelSpanContext:
    """In-memory span context voor OtelAgentTracer."""
    span: AgentSpan
    capability: str
    lane: str
    risk_score: int
    maturity: str
    agent_group: str
    temperature: float | None
    max_tokens: int | None
    _otel_span: Any = field(default=None, repr=False)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Voeg event toe aan de onderliggende AgentSpan én OTEL span."""
        self.span.add_event(name, attributes)
        if self._otel_span is not None:
            try:
                self._otel_span.add_event(name, attributes or {})
            except Exception:
                pass

    def set_fallback_triggered(self, original_model: str, fallback_model: str) -> None:
        """Log FALLBACK_TRIGGERED event."""
        self.add_event("FALLBACK_TRIGGERED", {
            "original_model": original_model,
            "fallback_model": fallback_model,
        })

    def set_hitl_escalation(self, reason: str, risk_score: int) -> None:
        """Log HITL_ESCALATION event."""
        self.add_event("HITL_ESCALATION", {
            "reason": reason,
            "risk_score": risk_score,
        })

    def set_quality_gate_failed(self, gate_id: str, verdict: str) -> None:
        """Log QUALITY_GATE_FAILED event."""
        self.add_event("QUALITY_GATE_FAILED", {
            "gate_id": gate_id,
            "verdict": verdict,
        })


class OtelAgentTracer:
    """
    Uitgebreide tracer conform OpenTelemetry GenAI Semantic Conventions 2025.

    Voegt gen_ai.* en agent.* attributes toe per span.
    Als OTEL_EXPORT_ENABLED=false (default) worden spans in-memory opgeslagen.
    """

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())

    @asynccontextmanager
    async def span(
        self,
        agent_name: str,
        model: str = "",
        trace_id: str | None = None,
        capability: str = "",
        lane: str = "",
        risk_score: int = 0,
        temperature: float | None = None,
        max_tokens: int | None = None,
        maturity: str = "L1",
        selection_reason: str = "",
        policy_violations: str = "",
    ) -> AsyncIterator[OtelSpanContext]:
        """
        Async context manager voor GenAI-gecompliantie tracing.

        Gebruik:
            async with otel_tracer.span("fraud_agent", model="llama3",
                                         capability="fraud-detection") as ctx:
                ctx.span.input_length = len(prompt)
                response = await agent.run(prompt)
                ctx.span.finish(output=response)
        """
        current_trace_id = trace_id or self.new_trace_id()
        agent_group = get_agent_group(agent_name)

        agent_span = AgentSpan(
            trace_id=current_trace_id,
            agent_name=agent_name,
            model=model,
            metadata={
                "gen_ai.system": "ollama",
                "gen_ai.request.model": model,
                "gen_ai.conversation.id": current_trace_id,
                "agent.name": agent_name,
                "agent.group": agent_group,
                "agent.capability": capability,
                "agent.lane": lane,
                "agent.maturity": maturity,
                "agent.risk_score": risk_score,
                "agent.selection.reason": selection_reason,
                "policy.violations": policy_violations,
            },
        )
        if temperature is not None:
            agent_span.metadata["gen_ai.request.temperature"] = temperature
        if max_tokens is not None:
            agent_span.metadata["gen_ai.request.max_tokens"] = max_tokens

        # Log system message event bij start
        agent_span.add_event("gen_ai.system.message", {
            "agent": agent_name,
            "model": model,
            "capability": capability,
        })

        otel_span = None
        if _otel_tracer is not None:
            try:
                otel_span = _otel_tracer.start_span(f"gen_ai/{agent_name}")
                for key, val in agent_span.metadata.items():
                    otel_span.set_attribute(key, val)
            except Exception:
                pass

        ctx = OtelSpanContext(
            span=agent_span,
            capability=capability,
            lane=lane,
            risk_score=risk_score,
            maturity=maturity,
            agent_group=agent_group,
            temperature=temperature,
            max_tokens=max_tokens,
            _otel_span=otel_span,
        )

        try:
            yield ctx
        except Exception as exc:
            agent_span.finish(error=str(exc))
            agent_span.metadata["gen_ai.response.finish_reason"] = "error"
            if otel_span:
                try:
                    from opentelemetry.trace import StatusCode  # type: ignore[import]
                    otel_span.set_status(StatusCode.ERROR, str(exc))
                except Exception:
                    pass
            raise
        finally:
            if agent_span.end_time is None:
                agent_span.finish()

            # Estimate token usage: 1 token ≈ 4 chars
            prompt_tokens = max(1, agent_span.input_length // 4)
            completion_tokens = max(0, agent_span.output_length // 4)
            agent_span.metadata["gen_ai.usage.prompt_tokens"] = prompt_tokens
            agent_span.metadata["gen_ai.usage.completion_tokens"] = completion_tokens

            if "gen_ai.response.finish_reason" not in agent_span.metadata:
                agent_span.metadata["gen_ai.response.finish_reason"] = "stop"

            log_data = agent_span.to_log_dict()
            if agent_span.success:
                logger.info("OtelAgent span voltooid: %s", log_data)
            else:
                logger.error("OtelAgent span mislukt: %s", log_data)

            if otel_span:
                try:
                    otel_span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
                    otel_span.set_attribute("gen_ai.usage.completion_tokens", completion_tokens)
                    otel_span.set_attribute(
                        "gen_ai.response.finish_reason",
                        agent_span.metadata.get("gen_ai.response.finish_reason", "stop"),
                    )
                    otel_span.end()
                except Exception:
                    pass


# ─────────────────────────────────────────────────────────
# Decorator
# ─────────────────────────────────────────────────────────

def traced_agent_call(agent_name: str, model: str = "") -> Callable:
    """
    Decorator voor het automatisch tracen van agent-aanroepen.

    Gebruik op async functies die een (response, interaction_id) tuple retourneren.

    Voorbeeld:
        @traced_agent_call("klantenservice_agent", model="llama3")
        async def run_klantenservice(user_input: str) -> tuple[str, str]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            async with tracer.span(agent_name, model=model) as span:
                if args:
                    span.input_length = len(str(args[0]))
                try:
                    result = await func(*args, **kwargs)
                    if isinstance(result, tuple) and len(result) >= 1:
                        span.finish(output=str(result[0]))
                    else:
                        span.finish(output=str(result))
                    return result
                except Exception as exc:
                    span.finish(error=str(exc))
                    raise
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────
# Singletons
# ─────────────────────────────────────────────────────────

_tracer: AgentTracer | None = None
_otel_agent_tracer: OtelAgentTracer | None = None


def get_tracer() -> AgentTracer:
    """Geef de singleton AgentTracer terug."""
    global _tracer
    if _tracer is None:
        _tracer = AgentTracer()
    return _tracer


def get_otel_tracer() -> OtelAgentTracer:
    """Geef de singleton OtelAgentTracer terug."""
    global _otel_agent_tracer
    if _otel_agent_tracer is None:
        _otel_agent_tracer = OtelAgentTracer()
    return _otel_agent_tracer
