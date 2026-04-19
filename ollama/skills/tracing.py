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
Optionele integratie met OpenTelemetry indien geïnstalleerd.
"""
import functools
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

logger = logging.getLogger("vorstersNV.tracing")

# Singleton OpenTelemetry tracer (None als OTEL niet geïnstalleerd)
_otel_tracer: Any = None


def _init_otel() -> None:
    """Initialiseer OpenTelemetry tracer indien beschikbaar."""
    global _otel_tracer
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

    def finish(self, output: str = "", error: str | None = None) -> None:
        """Sluit de span af en bereken latency."""
        self.end_time = time.monotonic()
        self.latency_ms = (self.end_time - self.start_time) * 1000
        self.output_length = len(output)
        if error:
            self.success = False
            self.error = error

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


# Singleton tracer
_tracer: AgentTracer | None = None


def get_tracer() -> AgentTracer:
    """Geef de singleton AgentTracer terug."""
    global _tracer
    if _tracer is None:
        _tracer = AgentTracer()
    return _tracer
