"""
Tests voor VorstersNV tracing — backward compatibility + OpenTelemetry GenAI 2025.
"""
from __future__ import annotations

import pytest

from ollama.skills.tracing import (
    AgentSpan,
    AgentTracer,
    OtelAgentTracer,
    OtelSpanContext,
    get_agent_group,
    get_otel_tracer,
    get_tracer,
    traced_agent_call,
)


# ─────────────────────────────────────────────────────────
# get_agent_group()
# ─────────────────────────────────────────────────────────

class TestGetAgentGroup:
    def test_fraude_prefix(self):
        assert get_agent_group("fraude_detector") == "RISK_DECISION"

    def test_fraud_prefix_english(self):
        assert get_agent_group("fraud_scoring_agent") == "RISK_DECISION"

    def test_test_prefix(self):
        assert get_agent_group("test_validator") == "TEST_INTELLIGENCE"

    def test_unit_prefix(self):
        assert get_agent_group("unit_runner") == "TEST_INTELLIGENCE"

    def test_integratie_prefix(self):
        assert get_agent_group("integratie_suite") == "TEST_INTELLIGENCE"

    def test_developer_prefix(self):
        assert get_agent_group("developer_agent") == "DEV_INTELLIGENCE"

    def test_architect_prefix(self):
        assert get_agent_group("architect_review") == "DEV_INTELLIGENCE"

    def test_klantenservice_prefix(self):
        assert get_agent_group("klantenservice_bot") == "EXPLANATION"

    def test_customer_prefix(self):
        assert get_agent_group("customer_support") == "EXPLANATION"

    def test_audit_prefix(self):
        assert get_agent_group("audit_trail") == "AUDIT"

    def test_unknown_defaults_to_dev_intelligence(self):
        assert get_agent_group("payroll_agent") == "DEV_INTELLIGENCE"

    def test_case_insensitive_fraude(self):
        assert get_agent_group("Fraude_checker") == "RISK_DECISION"


# ─────────────────────────────────────────────────────────
# AgentSpan — nieuw add_event + events veld
# ─────────────────────────────────────────────────────────

class TestAgentSpanEvents:
    def test_add_event_appended(self):
        span = AgentSpan(trace_id="t1", agent_name="test", model="llama3")
        span.add_event("MY_EVENT", {"key": "value"})
        assert len(span.events) == 1
        name, attrs, ts = span.events[0]
        assert name == "MY_EVENT"
        assert attrs["key"] == "value"

    def test_add_event_no_attributes(self):
        span = AgentSpan(trace_id="t1", agent_name="test", model="llama3")
        span.add_event("BARE_EVENT")
        assert span.events[0][0] == "BARE_EVENT"
        assert span.events[0][1] == {}

    def test_multiple_events(self):
        span = AgentSpan(trace_id="t1", agent_name="test", model="llama3")
        span.add_event("E1")
        span.add_event("E2")
        assert len(span.events) == 2


# ─────────────────────────────────────────────────────────
# AgentTracer — backward compatibility
# ─────────────────────────────────────────────────────────

class TestAgentTracerBackwardCompat:
    @pytest.mark.asyncio
    async def test_span_yields_agent_span(self):
        tracer = AgentTracer()
        async with tracer.span("klantenservice_agent", model="llama3") as span:
            assert isinstance(span, AgentSpan)
            assert span.agent_name == "klantenservice_agent"
            assert span.model == "llama3"

    @pytest.mark.asyncio
    async def test_span_custom_trace_id(self):
        tracer = AgentTracer()
        async with tracer.span("some_agent", trace_id="my-trace-123") as span:
            assert span.trace_id == "my-trace-123"

    @pytest.mark.asyncio
    async def test_span_finish_sets_latency(self):
        tracer = AgentTracer()
        async with tracer.span("agent_x") as span:
            span.finish(output="hello world")
        assert span.latency_ms is not None
        assert span.latency_ms >= 0
        assert span.output_length == len("hello world")

    @pytest.mark.asyncio
    async def test_span_error_marks_failure(self):
        tracer = AgentTracer()
        with pytest.raises(ValueError):
            async with tracer.span("error_agent") as span:
                raise ValueError("test error")
        assert span.success is False
        assert "test error" in (span.error or "")

    @pytest.mark.asyncio
    async def test_span_metadata_preserved(self):
        tracer = AgentTracer()
        async with tracer.span("agent_y", metadata={"foo": "bar"}) as span:
            pass
        assert span.metadata.get("foo") == "bar"

    def test_get_tracer_singleton(self):
        t1 = get_tracer()
        t2 = get_tracer()
        assert t1 is t2

    @pytest.mark.asyncio
    async def test_traced_agent_call_decorator(self):
        @traced_agent_call("klantenservice_agent", model="llama3")
        async def fake_agent(user_input: str) -> tuple[str, str]:
            return "antwoord", "interaction-1"

        result = await fake_agent("hallo")
        assert result == ("antwoord", "interaction-1")


# ─────────────────────────────────────────────────────────
# OtelAgentTracer
# ─────────────────────────────────────────────────────────

class TestOtelAgentTracer:
    @pytest.mark.asyncio
    async def test_span_yields_otel_span_context(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3") as ctx:
            assert isinstance(ctx, OtelSpanContext)
            assert isinstance(ctx.span, AgentSpan)

    @pytest.mark.asyncio
    async def test_gen_ai_system_attribute(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3") as ctx:
            pass
        assert ctx.span.metadata["gen_ai.system"] == "ollama"

    @pytest.mark.asyncio
    async def test_gen_ai_request_model_attribute(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3") as ctx:
            pass
        assert ctx.span.metadata["gen_ai.request.model"] == "llama3"

    @pytest.mark.asyncio
    async def test_gen_ai_conversation_id_is_trace_id(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3", trace_id="abc-123") as ctx:
            pass
        assert ctx.span.metadata["gen_ai.conversation.id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_agent_group_set_correctly(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_scoring_agent", model="llama3") as ctx:
            pass
        assert ctx.span.metadata["agent.group"] == "RISK_DECISION"

    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3",
                                temperature=0.7, max_tokens=512) as ctx:
            pass
        assert ctx.span.metadata["gen_ai.request.temperature"] == 0.7
        assert ctx.span.metadata["gen_ai.request.max_tokens"] == 512

    @pytest.mark.asyncio
    async def test_finish_reason_stop_on_success(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3") as ctx:
            ctx.span.finish(output="result")
        assert ctx.span.metadata["gen_ai.response.finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_finish_reason_error_on_exception(self):
        tracer = OtelAgentTracer()
        with pytest.raises(RuntimeError):
            async with tracer.span("fraud_detector", model="llama3") as ctx:
                raise RuntimeError("boom")
        assert ctx.span.metadata["gen_ai.response.finish_reason"] == "error"

    @pytest.mark.asyncio
    async def test_usage_tokens_estimated(self):
        tracer = OtelAgentTracer()
        async with tracer.span("audit_agent", model="llama3") as ctx:
            ctx.span.input_length = 400
            ctx.span.finish(output="x" * 200)
        assert ctx.span.metadata["gen_ai.usage.prompt_tokens"] == 100
        assert ctx.span.metadata["gen_ai.usage.completion_tokens"] == 50

    @pytest.mark.asyncio
    async def test_system_message_event_added_at_start(self):
        tracer = OtelAgentTracer()
        async with tracer.span("klantenservice_agent", model="llama3",
                                capability="support") as ctx:
            pass
        event_names = [e[0] for e in ctx.span.events]
        assert "gen_ai.system.message" in event_names

    @pytest.mark.asyncio
    async def test_fallback_triggered_event(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3") as ctx:
            ctx.set_fallback_triggered("llama3", "phi3")
        names = [e[0] for e in ctx.span.events]
        assert "FALLBACK_TRIGGERED" in names
        fb_event = next(e for e in ctx.span.events if e[0] == "FALLBACK_TRIGGERED")
        assert fb_event[1]["original_model"] == "llama3"
        assert fb_event[1]["fallback_model"] == "phi3"

    @pytest.mark.asyncio
    async def test_hitl_escalation_event(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3") as ctx:
            ctx.set_hitl_escalation("high risk score", 85)
        names = [e[0] for e in ctx.span.events]
        assert "HITL_ESCALATION" in names
        ev = next(e for e in ctx.span.events if e[0] == "HITL_ESCALATION")
        assert ev[1]["risk_score"] == 85

    @pytest.mark.asyncio
    async def test_quality_gate_failed_event(self):
        tracer = OtelAgentTracer()
        async with tracer.span("test_validator", model="llama3") as ctx:
            ctx.set_quality_gate_failed("QG-001", "NEEDS_DISCUSSION")
        names = [e[0] for e in ctx.span.events]
        assert "QUALITY_GATE_FAILED" in names
        ev = next(e for e in ctx.span.events if e[0] == "QUALITY_GATE_FAILED")
        assert ev[1]["verdict"] == "NEEDS_DISCUSSION"

    @pytest.mark.asyncio
    async def test_add_event_via_context(self):
        tracer = OtelAgentTracer()
        async with tracer.span("audit_agent", model="llama3") as ctx:
            ctx.add_event("CHECKPOINT_SAVED", {"step": 3})
        names = [e[0] for e in ctx.span.events]
        assert "CHECKPOINT_SAVED" in names

    def test_get_otel_tracer_singleton(self):
        t1 = get_otel_tracer()
        t2 = get_otel_tracer()
        assert t1 is t2

    @pytest.mark.asyncio
    async def test_no_crash_when_otel_export_disabled(self):
        """Export disabled (default) = geen crash, in-memory werkt."""
        import ollama.skills.tracing as tracing_mod
        assert tracing_mod._otel_tracer is None  # OTEL_EXPORT_ENABLED=false by default

        tracer = OtelAgentTracer()
        async with tracer.span("audit_agent", model="llama3") as ctx:
            ctx.span.finish(output="ok")
        assert ctx.span.success is True

    @pytest.mark.asyncio
    async def test_capability_and_lane_stored(self):
        tracer = OtelAgentTracer()
        async with tracer.span("fraud_detector", model="llama3",
                                capability="fraud-detection", lane="deterministic") as ctx:
            pass
        assert ctx.span.metadata["agent.capability"] == "fraud-detection"
        assert ctx.span.metadata["agent.lane"] == "deterministic"

    @pytest.mark.asyncio
    async def test_policy_violations_attribute(self):
        tracer = OtelAgentTracer()
        async with tracer.span("audit_agent", model="llama3",
                                policy_violations="POL-001,POL-002") as ctx:
            pass
        assert ctx.span.metadata["policy.violations"] == "POL-001,POL-002"
