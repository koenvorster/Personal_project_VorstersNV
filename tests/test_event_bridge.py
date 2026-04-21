"""
Tests for ollama/event_bridge.py

Coverage:
- BridgeResult dataclass
- EventBridge.emit_order_created()
- EventBridge.emit_order_shipped()
- EventBridge.emit_order_returned()
- EventBridge.emit_payment_failed()
- EventBridge.emit_payment_completed()
- EventBridge.emit_fraud_detected() — chain trigger logic
- EventBridge.emit_inventory_low()
- get_event_bridge() singleton identity
- Error handling (EventBus raises → BridgeResult.error is set)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ollama.event_bridge import (
    BridgeResult,
    EventBridge,
    OrderShippedEvent,
    PaymentCompletedEvent,
    PaymentRefundedEvent,
    get_event_bridge,
)
from ollama.events import EventType


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _make_mock_bus(*, publish_return=True):
    bus = MagicMock()
    bus.publish = AsyncMock(return_value=publish_return)
    return bus


def _make_mock_orchestrator(*, status="completed"):
    from ollama.skill_chain_orchestrator import ChainResult, ChainStatus
    orc = MagicMock()
    orc.select_chain = MagicMock(return_value=("prc-decision-support", ["fraud_detected → prc"]))
    chain_result = ChainResult(
        chain_name="prc-decision-support",
        status=ChainStatus.COMPLETED,
        outputs={},
        selection_reasons=[],
        completed_steps=[],
        skipped_steps=[],
    )
    if status == "failed":
        from ollama.skill_chain_orchestrator import ChainStatus as CS
        chain_result.status = CS.FAILED
        chain_result.error = "mock error"
    orc.run = AsyncMock(return_value=chain_result)
    return orc


ORDER_PAYLOAD = {
    "order_id": "ORD-100",
    "customer": {"id": "CUST-42", "name": "Testklant"},
    "items": [{"product_id": "P1", "qty": 1}],
    "total": 99.95,
    "payment_method": "ideal",
    "delivery_country": "NL",
}

PAYMENT_FAILED_PAYLOAD = {
    "order_id": "ORD-200",
    "payment_id": "PAY-XYZ",
    "failure_reason": "insufficient_funds",
    "mollie_status": "failed",
    "retry_count": 1,
}

PAYMENT_COMPLETED_PAYLOAD = {
    "order_id": "ORD-201",
    "payment_id": "PAY-ABC",
    "amount": 149.00,
    "method": "creditcard",
}

FRAUD_PAYLOAD = {
    "order_id": "ORD-300",
    "customer_id": "CUST-99",
    "signals": ["velocity_abuse", "address_mismatch"],
}

INVENTORY_PAYLOAD = {
    "product_id": "PROD-50",
    "product_name": "Zaadje X",
    "current_stock": 2,
    "threshold": 5,
}

RETURN_PAYLOAD = {
    "order_id": "ORD-150",
    "return_reason": "Verkeerde maat",
}


# ─────────────────────────────────────────────
# BridgeResult tests
# ─────────────────────────────────────────────

class TestBridgeResult:
    def test_bridge_result_defaults(self):
        result = BridgeResult(event_type="order.created", emitted=True, chain_triggered=False)
        assert result.chain_result is None
        assert result.error is None

    def test_bridge_result_with_error(self):
        result = BridgeResult(
            event_type="fraud.detected", emitted=False, chain_triggered=False, error="boom"
        )
        assert result.error == "boom"
        assert not result.emitted

    def test_bridge_result_with_chain_result(self):
        result = BridgeResult(
            event_type="fraud.detected",
            emitted=True,
            chain_triggered=True,
            chain_result="completed:prc-decision-support",
        )
        assert result.chain_triggered is True
        assert "completed" in result.chain_result


# ─────────────────────────────────────────────
# emit_order_created
# ─────────────────────────────────────────────

class TestEmitOrderCreated:
    async def test_returns_bridge_result(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_created(ORDER_PAYLOAD)
        assert isinstance(result, BridgeResult)

    async def test_emitted_true(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_created(ORDER_PAYLOAD)
        assert result.emitted is True

    async def test_event_type_value(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_created(ORDER_PAYLOAD)
        assert result.event_type == EventType.ORDER_CREATED.value

    async def test_chain_not_triggered(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_created(ORDER_PAYLOAD)
        assert result.chain_triggered is False

    async def test_bus_publish_called(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_order_created(ORDER_PAYLOAD)
        bus.publish.assert_called_once()

    async def test_publishes_order_created_event(self):
        from ollama.events import OrderCreatedEvent
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_order_created(ORDER_PAYLOAD)
        published_event = bus.publish.call_args[0][0]
        assert isinstance(published_event, OrderCreatedEvent)

    async def test_event_fields_from_payload(self):
        from ollama.events import OrderCreatedEvent
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_order_created(ORDER_PAYLOAD)
        event: OrderCreatedEvent = bus.publish.call_args[0][0]
        assert event.order_id == "ORD-100"
        assert event.order_value == 99.95
        assert event.delivery_country == "NL"

    async def test_error_handling_bus_raises(self):
        bus = MagicMock()
        bus.publish = AsyncMock(side_effect=RuntimeError("bus down"))
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_created(ORDER_PAYLOAD)
        assert result.emitted is False
        assert result.error is not None
        assert "bus down" in result.error

    async def test_missing_total_defaults_to_zero(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_created({"order_id": "X"})
        assert result.emitted is True


# ─────────────────────────────────────────────
# emit_order_shipped
# ─────────────────────────────────────────────

class TestEmitOrderShipped:
    async def test_emitted_true(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_shipped(
            {"order_id": "ORD-10", "tracking_code": "TRK-1", "carrier": "PostNL"}
        )
        assert result.emitted is True
        assert result.event_type == EventType.ORDER_SHIPPED.value

    async def test_publishes_order_shipped_event(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_order_shipped({"order_id": "ORD-10", "tracking_code": "T1"})
        event = bus.publish.call_args[0][0]
        assert isinstance(event, OrderShippedEvent)
        assert event.order_id == "ORD-10"

    async def test_error_handling(self):
        bus = MagicMock()
        bus.publish = AsyncMock(side_effect=Exception("network"))
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_shipped({"order_id": "ORD-10"})
        assert result.emitted is False
        assert result.error is not None


# ─────────────────────────────────────────────
# emit_order_returned
# ─────────────────────────────────────────────

class TestEmitOrderReturned:
    async def test_emitted_true(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_returned(RETURN_PAYLOAD)
        assert result.emitted is True

    async def test_event_type_is_refunded(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_order_returned(RETURN_PAYLOAD)
        assert result.event_type == EventType.PAYMENT_REFUNDED.value

    async def test_publishes_refund_event(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_order_returned(RETURN_PAYLOAD)
        event = bus.publish.call_args[0][0]
        assert isinstance(event, PaymentRefundedEvent)
        assert event.order_id == "ORD-150"


# ─────────────────────────────────────────────
# emit_payment_failed
# ─────────────────────────────────────────────

class TestEmitPaymentFailed:
    async def test_emitted_true(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_payment_failed(PAYMENT_FAILED_PAYLOAD)
        assert result.emitted is True

    async def test_correct_event_type(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_payment_failed(PAYMENT_FAILED_PAYLOAD)
        assert result.event_type == EventType.PAYMENT_FAILED.value

    async def test_publishes_payment_failed_event(self):
        from ollama.events import PaymentFailedEvent
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_payment_failed(PAYMENT_FAILED_PAYLOAD)
        event = bus.publish.call_args[0][0]
        assert isinstance(event, PaymentFailedEvent)
        assert event.order_id == "ORD-200"
        assert event.failure_reason == "insufficient_funds"

    async def test_chain_not_triggered(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_payment_failed(PAYMENT_FAILED_PAYLOAD)
        assert result.chain_triggered is False

    async def test_error_handling(self):
        bus = MagicMock()
        bus.publish = AsyncMock(side_effect=ValueError("bad"))
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_payment_failed(PAYMENT_FAILED_PAYLOAD)
        assert result.emitted is False
        assert "bad" in result.error


# ─────────────────────────────────────────────
# emit_payment_completed
# ─────────────────────────────────────────────

class TestEmitPaymentCompleted:
    async def test_emitted_true(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_payment_completed(PAYMENT_COMPLETED_PAYLOAD)
        assert result.emitted is True

    async def test_correct_event_type(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_payment_completed(PAYMENT_COMPLETED_PAYLOAD)
        assert result.event_type == EventType.PAYMENT_COMPLETED.value

    async def test_publishes_payment_completed_event(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_payment_completed(PAYMENT_COMPLETED_PAYLOAD)
        event = bus.publish.call_args[0][0]
        assert isinstance(event, PaymentCompletedEvent)
        assert event.order_id == "ORD-201"
        assert event.amount == 149.00


# ─────────────────────────────────────────────
# emit_fraud_detected
# ─────────────────────────────────────────────

class TestEmitFraudDetected:
    async def test_emitted_true_high_risk(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=80)
        assert result.emitted is True

    async def test_chain_triggered_when_risk_gte_75(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=75)
        assert result.chain_triggered is True
        orc.run.assert_called_once()

    async def test_chain_triggered_at_exactly_75(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=75)
        assert result.chain_triggered is True

    async def test_chain_NOT_triggered_when_risk_lt_75(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=74)
        assert result.chain_triggered is False
        orc.run.assert_not_called()

    async def test_chain_NOT_triggered_risk_zero(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=0)
        assert result.chain_triggered is False

    async def test_chain_result_contains_status(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=90)
        assert result.chain_result is not None
        assert "completed" in result.chain_result

    async def test_event_type_value(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=50)
        assert result.event_type == EventType.FRAUD_DETECTED.value

    async def test_publishes_fraud_event(self):
        from ollama.events import FraudDetectedEvent
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=80)
        event = bus.publish.call_args[0][0]
        assert isinstance(event, FraudDetectedEvent)
        assert event.risk_score == 80

    async def test_requires_human_set_true_for_high_risk(self):
        from ollama.events import FraudDetectedEvent
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=80)
        event: FraudDetectedEvent = bus.publish.call_args[0][0]
        assert event.requires_human is True

    async def test_requires_human_false_for_low_risk(self):
        from ollama.events import FraudDetectedEvent
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=40)
        event: FraudDetectedEvent = bus.publish.call_args[0][0]
        assert event.requires_human is False

    async def test_error_handling_bus_raises(self):
        bus = MagicMock()
        bus.publish = AsyncMock(side_effect=RuntimeError("bus down"))
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=80)
        assert result.emitted is False
        assert result.error is not None

    async def test_orchestrator_select_chain_called_with_fraud_type(self):
        bus = _make_mock_bus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=bus, orchestrator=orc)
        await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=80)
        orc.select_chain.assert_called_once_with(event_type="fraud_detected", risk_score=80)


# ─────────────────────────────────────────────
# emit_inventory_low
# ─────────────────────────────────────────────

class TestEmitInventoryLow:
    async def test_emitted_true(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_inventory_low(INVENTORY_PAYLOAD)
        assert result.emitted is True

    async def test_correct_event_type(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_inventory_low(INVENTORY_PAYLOAD)
        assert result.event_type == EventType.INVENTORY_LOW.value

    async def test_publishes_inventory_low_event(self):
        from ollama.events import InventoryLowEvent
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        await bridge.emit_inventory_low(INVENTORY_PAYLOAD)
        event = bus.publish.call_args[0][0]
        assert isinstance(event, InventoryLowEvent)
        assert event.product_id == "PROD-50"
        assert event.current_stock == 2

    async def test_chain_not_triggered(self):
        bus = _make_mock_bus()
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_inventory_low(INVENTORY_PAYLOAD)
        assert result.chain_triggered is False

    async def test_error_handling(self):
        bus = MagicMock()
        bus.publish = AsyncMock(side_effect=Exception("oops"))
        bridge = EventBridge(bus=bus)
        result = await bridge.emit_inventory_low(INVENTORY_PAYLOAD)
        assert result.emitted is False
        assert result.error is not None


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

class TestSingleton:
    def test_get_event_bridge_returns_same_instance(self):
        import ollama.event_bridge as eb_module
        # Reset singleton for clean test
        eb_module._bridge = None
        bridge1 = get_event_bridge()
        bridge2 = get_event_bridge()
        assert bridge1 is bridge2

    def test_singleton_is_event_bridge_instance(self):
        import ollama.event_bridge as eb_module
        eb_module._bridge = None
        bridge = get_event_bridge()
        assert isinstance(bridge, EventBridge)

    def test_singleton_identity_across_calls(self):
        import ollama.event_bridge as eb_module
        eb_module._bridge = None
        instances = [get_event_bridge() for _ in range(5)]
        assert all(i is instances[0] for i in instances)


# ─────────────────────────────────────────────
# Integration: EventBridge with real EventBus
# ─────────────────────────────────────────────

class TestEventBridgeWithRealBus:
    async def test_real_bus_emit_order_created(self):
        from ollama.events import EventBus
        real_bus = EventBus()
        bridge = EventBridge(bus=real_bus)
        result = await bridge.emit_order_created(ORDER_PAYLOAD)
        assert result.emitted is True
        assert result.error is None

    async def test_real_bus_emit_payment_failed(self):
        from ollama.events import EventBus
        real_bus = EventBus()
        bridge = EventBridge(bus=real_bus)
        result = await bridge.emit_payment_failed(PAYMENT_FAILED_PAYLOAD)
        assert result.emitted is True

    async def test_real_bus_subscriber_receives_event(self):
        from ollama.events import EventBus, EventType
        real_bus = EventBus()
        received = []

        async def on_order_created(event):
            received.append(event)

        real_bus.subscribe(EventType.ORDER_CREATED, on_order_created)
        bridge = EventBridge(bus=real_bus)
        await bridge.emit_order_created(ORDER_PAYLOAD)
        assert len(received) == 1
        assert received[0].order_id == "ORD-100"

    async def test_real_bus_fraud_low_risk_no_chain(self):
        from ollama.events import EventBus
        from ollama.skill_chain_orchestrator import SkillChainOrchestrator
        real_bus = EventBus()
        orc = _make_mock_orchestrator()
        bridge = EventBridge(bus=real_bus, orchestrator=orc)
        result = await bridge.emit_fraud_detected(FRAUD_PAYLOAD, risk_score=50)
        assert result.chain_triggered is False
        orc.run.assert_not_called()
