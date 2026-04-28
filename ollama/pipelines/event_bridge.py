"""
EventBridge — lightweight bridge between webhook payloads and the typed EventBus.

Responsibilities:
1. Map raw webhook payloads to typed DomainEvent instances.
2. Emit those events on the singleton EventBus.
3. For high-risk events (fraud risk_score >= 75), trigger the SkillChainOrchestrator.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from ..core.events import (
    DomainEvent,
    EventType,
    FraudDetectedEvent,
    InventoryLowEvent,
    OrderCreatedEvent,
    PaymentFailedEvent,
    EventBus,
    get_event_bus,
)
from ..agents.skill_chain_orchestrator import SkillChainOrchestrator, get_skill_chain_orchestrator

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Local event dataclasses for types without a dedicated class in events.py
# ─────────────────────────────────────────────

@dataclass
class OrderShippedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.ORDER_SHIPPED, init=False)
    order_id: str = ""
    tracking_code: str = ""
    carrier: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class PaymentCompletedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.PAYMENT_COMPLETED, init=False)
    order_id: str = ""
    payment_id: str = ""
    amount: float = 0.0
    payment_method: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class PaymentRefundedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.PAYMENT_REFUNDED, init=False)
    order_id: str = ""
    return_reason: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()


# ─────────────────────────────────────────────
# BridgeResult
# ─────────────────────────────────────────────

@dataclass
class BridgeResult:
    event_type: str
    emitted: bool
    chain_triggered: bool
    chain_result: Optional[str] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────
# EventBridge
# ─────────────────────────────────────────────

class EventBridge:
    """
    Translates webhook payloads into typed domain events and routes them
    through the EventBus. For fraud events with risk_score >= 75, the
    SkillChainOrchestrator is also invoked.
    """

    def __init__(
        self,
        bus: Optional[EventBus] = None,
        orchestrator: Optional[SkillChainOrchestrator] = None,
    ) -> None:
        self._bus = bus
        self._orchestrator = orchestrator

    @property
    def bus(self) -> EventBus:
        return self._bus if self._bus is not None else get_event_bus()

    @property
    def orchestrator(self) -> SkillChainOrchestrator:
        return self._orchestrator if self._orchestrator is not None else get_skill_chain_orchestrator()

    async def emit_order_created(self, payload: dict) -> BridgeResult:
        try:
            customer = payload.get("customer") or {}
            event = OrderCreatedEvent(
                order_id=payload.get("order_id", ""),
                customer_id=customer.get("id", "") or payload.get("customer_id", ""),
                order_value=float(payload.get("total", payload.get("order_value", 0.0)) or 0.0),
                payment_method=payload.get("payment_method", ""),
                delivery_country=payload.get("delivery_country", "BE"),
            )
            await self.bus.publish(event)
            logger.debug("EventBridge: emitted %s for order %s", event.event_type.value, event.order_id)
            return BridgeResult(
                event_type=EventType.ORDER_CREATED.value,
                emitted=True,
                chain_triggered=False,
            )
        except Exception as exc:
            logger.error("EventBridge emit_order_created failed: %s", exc)
            return BridgeResult(
                event_type=EventType.ORDER_CREATED.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )

    async def emit_order_shipped(self, payload: dict) -> BridgeResult:
        try:
            event = OrderShippedEvent(
                order_id=payload.get("order_id", ""),
                tracking_code=payload.get("tracking_code", ""),
                carrier=payload.get("carrier", ""),
            )
            await self.bus.publish(event)
            return BridgeResult(
                event_type=EventType.ORDER_SHIPPED.value,
                emitted=True,
                chain_triggered=False,
            )
        except Exception as exc:
            logger.error("EventBridge emit_order_shipped failed: %s", exc)
            return BridgeResult(
                event_type=EventType.ORDER_SHIPPED.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )

    async def emit_order_returned(self, payload: dict) -> BridgeResult:
        try:
            event = PaymentRefundedEvent(
                order_id=payload.get("order_id", ""),
                return_reason=payload.get("return_reason", ""),
            )
            await self.bus.publish(event)
            return BridgeResult(
                event_type=EventType.PAYMENT_REFUNDED.value,
                emitted=True,
                chain_triggered=False,
            )
        except Exception as exc:
            logger.error("EventBridge emit_order_returned failed: %s", exc)
            return BridgeResult(
                event_type=EventType.PAYMENT_REFUNDED.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )

    async def emit_payment_failed(self, payload: dict) -> BridgeResult:
        try:
            event = PaymentFailedEvent(
                order_id=payload.get("order_id", ""),
                payment_id=payload.get("payment_id", ""),
                mollie_status=payload.get("mollie_status", ""),
                failure_reason=payload.get("failure_reason", payload.get("reden", "")),
                retry_count=int(payload.get("retry_count", 0) or 0),
            )
            await self.bus.publish(event)
            return BridgeResult(
                event_type=EventType.PAYMENT_FAILED.value,
                emitted=True,
                chain_triggered=False,
            )
        except Exception as exc:
            logger.error("EventBridge emit_payment_failed failed: %s", exc)
            return BridgeResult(
                event_type=EventType.PAYMENT_FAILED.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )

    async def emit_payment_completed(self, payload: dict) -> BridgeResult:
        try:
            event = PaymentCompletedEvent(
                order_id=payload.get("order_id", ""),
                payment_id=payload.get("payment_id", ""),
                amount=float(payload.get("amount", 0.0) or 0.0),
                payment_method=payload.get("method", payload.get("payment_method", "")),
            )
            await self.bus.publish(event)
            return BridgeResult(
                event_type=EventType.PAYMENT_COMPLETED.value,
                emitted=True,
                chain_triggered=False,
            )
        except Exception as exc:
            logger.error("EventBridge emit_payment_completed failed: %s", exc)
            return BridgeResult(
                event_type=EventType.PAYMENT_COMPLETED.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )

    async def emit_fraud_detected(self, payload: dict, risk_score: int) -> BridgeResult:
        """
        Emits a FraudDetectedEvent. If risk_score >= 75, the SkillChainOrchestrator
        is also triggered with the prc-decision-support chain.
        """
        try:
            customer = payload.get("customer") or {}
            signals = payload.get("signals", [])
            risk_level = _classify_risk_level(risk_score)
            event = FraudDetectedEvent(
                order_id=payload.get("order_id", ""),
                customer_id=customer.get("id", "") or payload.get("customer_id", ""),
                risk_score=risk_score,
                risk_level=risk_level,
                signals=signals if isinstance(signals, list) else [],
                requires_human=risk_score >= 75,
            )
            await self.bus.publish(event)

            chain_triggered = False
            chain_result: Optional[str] = None

            if risk_score >= 75:
                chain_name, _ = self.orchestrator.select_chain(
                    event_type="fraud_detected",
                    risk_score=risk_score,
                )
                result = await self.orchestrator.run(
                    chain_name=chain_name,
                    inputs={"fraud_event": event.to_dict(), "payload": payload},
                    risk_score=risk_score,
                    environment="prod",
                )
                chain_triggered = True
                chain_result = f"{result.status.value}:{result.chain_name}"
                logger.info(
                    "EventBridge: chain %s triggered for fraud risk_score=%d → status=%s",
                    chain_name,
                    risk_score,
                    result.status.value,
                )

            return BridgeResult(
                event_type=EventType.FRAUD_DETECTED.value,
                emitted=True,
                chain_triggered=chain_triggered,
                chain_result=chain_result,
            )
        except Exception as exc:
            logger.error("EventBridge emit_fraud_detected failed: %s", exc)
            return BridgeResult(
                event_type=EventType.FRAUD_DETECTED.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )

    async def emit_inventory_low(self, payload: dict) -> BridgeResult:
        try:
            event = InventoryLowEvent(
                product_id=payload.get("product_id", ""),
                product_name=payload.get("product_name", ""),
                current_stock=int(payload.get("current_stock", 0) or 0),
                threshold=int(payload.get("threshold", 0) or 0),
            )
            await self.bus.publish(event)
            return BridgeResult(
                event_type=EventType.INVENTORY_LOW.value,
                emitted=True,
                chain_triggered=False,
            )
        except Exception as exc:
            logger.error("EventBridge emit_inventory_low failed: %s", exc)
            return BridgeResult(
                event_type=EventType.INVENTORY_LOW.value,
                emitted=False,
                chain_triggered=False,
                error=str(exc),
            )


def _classify_risk_level(risk_score: int) -> str:
    if risk_score >= 90:
        return "CRITICAL"
    if risk_score >= 75:
        return "HIGH"
    if risk_score >= 50:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

_bridge: Optional[EventBridge] = None


def get_event_bridge() -> EventBridge:
    """Return the singleton EventBridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = EventBridge()
    return _bridge
