"""Tests voor ollama/contracts.py en ollama/events.py"""
import asyncio
import pytest

from ollama.contracts import (
    ContentGenerationContract,
    FraudAssessmentContract,
    OrderAnalysisContract,
)
from ollama.events import (
    AnomalyDetectedEvent,
    DomainEvent,
    EventBus,
    EventType,
    FraudDetectedEvent,
    OrderCreatedEvent,
    PaymentFailedEvent,
    get_event_bus,
)


# ─────────────────────────────────────────────
# Contract Tests
# ─────────────────────────────────────────────

class TestOrderAnalysisContract:
    def _valid(self, **kwargs) -> OrderAnalysisContract:
        defaults = dict(
            order_id="ORD-001",
            customer_id="CUST-123",
            order_value=99.99,
            payment_method="ideal",
        )
        defaults.update(kwargs)
        return OrderAnalysisContract(**defaults)

    def test_valid_contract(self):
        c = self._valid()
        is_valid, errors = c.validate()
        assert is_valid, errors

    def test_missing_order_id(self):
        c = OrderAnalysisContract(order_value=50.0, payment_method="ideal")
        is_valid, errors = c.validate()
        assert not is_valid
        assert any("order_id" in e for e in errors)

    def test_zero_value(self):
        c = OrderAnalysisContract(order_id="ORD-001", order_value=0.0, payment_method="ideal")
        is_valid, errors = c.validate()
        assert not is_valid
        assert any("order_value" in e for e in errors)

    def test_to_prompt_input_contains_order_id(self):
        c = self._valid()
        prompt = c.to_prompt_input()
        assert "ORD-001" in prompt
        assert "€99.99" in prompt

    def test_from_agent_output_parses_json(self):
        json_output = '{"order_id": "ORD-XYZ", "order_value": 199.0, "payment_method": "bancontact"}'
        c = OrderAnalysisContract.from_agent_output(json_output)
        assert c.order_id == "ORD-XYZ"
        assert c.order_value == 199.0

    def test_from_agent_output_with_surrounding_text(self):
        output = "Hier is de analyse:\n```json\n{\"order_id\": \"ORD-ABC\", \"order_value\": 50.0, \"payment_method\": \"creditcard\"}\n```"
        c = OrderAnalysisContract.from_agent_output(output)
        assert c.order_id == "ORD-ABC"


class TestFraudAssessmentContract:
    def _valid(self, **kwargs) -> FraudAssessmentContract:
        defaults = dict(
            order_id="ORD-001",
            risk_score=45,
            risk_level="MEDIUM",
            rationale=["Nieuwe account", "Hoge waarde"],
            recommended_action="REVIEW",
            confidence=0.82,
        )
        defaults.update(kwargs)
        return FraudAssessmentContract(**defaults)

    def test_valid_contract(self):
        c = self._valid()
        is_valid, errors = c.validate()
        assert is_valid, errors

    def test_invalid_risk_level(self):
        c = self._valid(risk_level="EXTREME")
        is_valid, errors = c.validate()
        assert not is_valid
        assert any("risk_level" in e for e in errors)

    def test_score_out_of_range(self):
        c = self._valid(risk_score=110)
        is_valid, errors = c.validate()
        assert not is_valid
        assert any("risk_score" in e for e in errors)

    def test_auto_requires_human_above_75(self):
        c = FraudAssessmentContract(
            order_id="ORD-001", risk_score=80, risk_level="HIGH",
            rationale=["VPN gedetecteerd"], recommended_action="BLOCK", confidence=0.9,
        )
        assert c.requires_human is True

    def test_no_requires_human_below_75(self):
        c = FraudAssessmentContract(
            order_id="ORD-001", risk_score=50, risk_level="MEDIUM",
            rationale=["Eerste bestelling"], recommended_action="REVIEW", confidence=0.7,
        )
        assert c.requires_human is False

    def test_from_agent_output(self):
        json_out = '{"order_id": "ORD-999", "risk_score": 85, "risk_level": "HIGH", "rationale": ["VPN"], "recommended_action": "BLOCK", "confidence": 0.95}'
        c = FraudAssessmentContract.from_agent_output(json_out)
        assert c.risk_score == 85
        assert c.requires_human is True

    def test_to_prompt_input_contains_risk_info(self):
        c = self._valid()
        prompt = c.to_prompt_input()
        assert "45/100" in prompt
        assert "MEDIUM" in prompt
        assert "Nieuwe account" in prompt

    def test_empty_rationale_invalid(self):
        c = self._valid(rationale=[])
        is_valid, errors = c.validate()
        assert not is_valid
        assert any("rationale" in e for e in errors)


class TestContentGenerationContract:
    def _valid(self, **kwargs) -> ContentGenerationContract:
        defaults = dict(
            product_id="PROD-001",
            product_name="Groene Thee",
            titel="Biologische Groene Thee 100g",
            beschrijving="Een heerlijke biologische groene thee van Japanse oorsprong met een frisse smaak.",
            seo_keywords=["groene thee", "biologisch", "Japan"],
            btw_categorie="6%",
        )
        defaults.update(kwargs)
        return ContentGenerationContract(**defaults)

    def test_valid_contract(self):
        c = self._valid()
        is_valid, errors = c.validate()
        assert is_valid, errors

    def test_empty_titel_invalid(self):
        c = self._valid(titel="")
        is_valid, errors = c.validate()
        assert not is_valid

    def test_beschrijving_too_short(self):
        c = self._valid(beschrijving="Kort")
        is_valid, errors = c.validate()
        assert not is_valid

    def test_invalid_btw(self):
        c = self._valid(btw_categorie="12%")
        is_valid, errors = c.validate()
        assert not is_valid

    def test_from_agent_output_word_count(self):
        json_out = '{"titel": "Test Titel", "beschrijving": "Een twee drie vier vijf zes zeven acht negen tien elf twaalf dertien veertien vijftien zestien zeventien achttien.", "seo_keywords": ["test"], "btw_categorie": "21%"}'
        c = ContentGenerationContract.from_agent_output(json_out)
        assert c.word_count > 0


# ─────────────────────────────────────────────
# Events Tests
# ─────────────────────────────────────────────

class TestDomainEvents:
    def test_order_created_event_type(self):
        e = OrderCreatedEvent(order_id="ORD-001", customer_id="CUST-1", order_value=100.0)
        assert e.event_type == EventType.ORDER_CREATED

    def test_event_id_is_deterministic(self):
        """Zelfde trace_id + event_type → zelfde event_id (idempotency)."""
        e1 = OrderCreatedEvent(trace_id="fixed-trace-123", order_id="ORD-001")
        e2 = OrderCreatedEvent(trace_id="fixed-trace-123", order_id="ORD-001")
        assert e1.event_id == e2.event_id

    def test_different_trace_ids_different_event_ids(self):
        e1 = OrderCreatedEvent(trace_id="trace-aaa", order_id="ORD-001")
        e2 = OrderCreatedEvent(trace_id="trace-bbb", order_id="ORD-001")
        assert e1.event_id != e2.event_id

    def test_fraud_detected_auto_set(self):
        e = FraudDetectedEvent(order_id="ORD-001", risk_score=80)
        assert e.event_type == EventType.FRAUD_DETECTED

    def test_payment_failed_event(self):
        e = PaymentFailedEvent(order_id="ORD-001", mollie_status="failed")
        assert e.event_type == EventType.PAYMENT_FAILED

    def test_to_dict_contains_type(self):
        e = OrderCreatedEvent(order_id="ORD-001")
        d = e.to_dict()
        assert d["event_type"] == "order.created"
        assert "trace_id" in d
        assert "timestamp" in d


class TestEventBus:
    def test_handler_called(self):
        bus = EventBus()
        received = []

        def handler(event: DomainEvent):
            received.append(event)

        bus.subscribe(EventType.ORDER_CREATED, handler)
        event = OrderCreatedEvent(order_id="ORD-001")
        asyncio.run(bus.publish(event))
        assert len(received) == 1
        assert received[0].event_type == EventType.ORDER_CREATED

    def test_idempotency_skip_duplicate(self):
        bus = EventBus()
        received = []

        def handler(event: DomainEvent):
            received.append(event)

        bus.subscribe(EventType.ORDER_CREATED, handler)
        event = OrderCreatedEvent(trace_id="same-trace", order_id="ORD-001")
        asyncio.run(bus.publish(event))
        asyncio.run(bus.publish(event))  # duplicate
        assert len(received) == 1  # slechts 1x verwerkt

    def test_no_handler_does_not_raise(self):
        bus = EventBus()
        event = OrderCreatedEvent(order_id="ORD-001")
        result = asyncio.run(bus.publish(event))
        assert result is True

    def test_get_chain_for_order_created(self):
        bus = EventBus()
        chain = bus.get_chain(EventType.ORDER_CREATED)
        assert chain == "ORDER_VALIDATION"

    def test_get_chain_for_payment_failed(self):
        bus = EventBus()
        chain = bus.get_chain(EventType.PAYMENT_FAILED)
        assert chain == "PAYMENT_RECOVERY"

    def test_get_chain_unknown_returns_none(self):
        bus = EventBus()
        chain = bus.get_chain(EventType.ORDER_SHIPPED)  # niet in map
        assert chain is None

    def test_async_handler(self):
        bus = EventBus()
        received = []

        async def async_handler(event: DomainEvent):
            received.append(event)

        bus.subscribe(EventType.FRAUD_DETECTED, async_handler)
        event = FraudDetectedEvent(order_id="ORD-001", risk_score=85)
        asyncio.run(bus.publish(event))
        assert len(received) == 1

    def test_singleton_bus(self):
        b1 = get_event_bus()
        b2 = get_event_bus()
        assert b1 is b2
