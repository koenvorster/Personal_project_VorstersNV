"""
VorstersNV Typed Event Taxonomy
Definieert alle domein-events als typed dataclasses met idempotency garanties.

Gebruik:
    from ollama.events import EventType, DomainEvent, OrderCreatedEvent

    event = OrderCreatedEvent(
        order_id="ORD-2024-1234",
        customer_id="CUST-789",
        order_value=389.00,
    )
    bus = EventBus()
    await bus.publish(event)
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Event Types
# ─────────────────────────────────────────────

class EventType(str, Enum):
    """Alle domein-events in het VorstersNV platform."""

    # Orders
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"

    # Payments
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_EXPIRED = "payment.expired"

    # Fraude
    FRAUD_DETECTED = "fraud.detected"
    FRAUD_CLEARED = "fraud.cleared"
    FRAUD_BLOCKED = "fraud.blocked"

    # Inventory
    INVENTORY_LOW = "inventory.low"
    INVENTORY_DEPLETED = "inventory.depleted"
    INVENTORY_RESTOCKED = "inventory.restocked"

    # Customers
    CUSTOMER_REGISTERED = "customer.registered"
    CUSTOMER_FLAGGED = "customer.flagged"

    # Dev / AI
    CODE_RELEASED = "code.released"
    ANOMALY_DETECTED = "anomaly.detected"
    QUALITY_GATE_FAILED = "quality_gate.failed"
    HITL_REQUIRED = "hitl.required"
    HITL_RESOLVED = "hitl.resolved"


# ─────────────────────────────────────────────
# Base Event
# ─────────────────────────────────────────────

@dataclass
class DomainEvent:
    """
    Basis domein-event met idempotency garantie.

    event_id is deterministisch bepaald op basis van event_type + trace_id,
    zodat duplicate events veilig verwerkt kunnen worden.
    Subclasses overschrijven event_type via field(default=..., init=False).
    """
    event_type: EventType = field(default=EventType.ORDER_CREATED, init=False)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(init=False)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.event_id = self._compute_event_id()

    def _compute_event_id(self) -> str:
        """Deterministisch event_id voor idempotency (event_type + trace_id)."""
        key = f"{self.event_type.value}:{self.trace_id}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            **self.metadata,
        }


# ─────────────────────────────────────────────
# Concrete Event Types
# ─────────────────────────────────────────────

@dataclass
class OrderCreatedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.ORDER_CREATED, init=False)
    order_id: str = ""
    customer_id: str = ""
    order_value: float = 0.0
    payment_method: str = ""
    delivery_country: str = "BE"

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class PaymentFailedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.PAYMENT_FAILED, init=False)
    order_id: str = ""
    payment_id: str = ""
    mollie_status: str = ""
    failure_reason: str = ""
    retry_count: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class FraudDetectedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.FRAUD_DETECTED, init=False)
    order_id: str = ""
    customer_id: str = ""
    risk_score: int = 0
    risk_level: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL
    signals: list[str] = field(default_factory=list)
    requires_human: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class InventoryLowEvent(DomainEvent):
    event_type: EventType = field(default=EventType.INVENTORY_LOW, init=False)
    product_id: str = ""
    product_name: str = ""
    current_stock: int = 0
    threshold: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class HitlRequiredEvent(DomainEvent):
    """Trigger voor menselijke review — state machine pauzeert."""
    event_type: EventType = field(default=EventType.HITL_REQUIRED, init=False)
    capability: str = ""
    reason: str = ""
    risk_score: int = 0
    workflow_checkpoint_id: str = ""
    assigned_to: str = ""  # team of gebruiker voor review

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass
class AnomalyDetectedEvent(DomainEvent):
    event_type: EventType = field(default=EventType.ANOMALY_DETECTED, init=False)
    agent_name: str = ""
    metric: str = ""
    observed_value: float = 0.0
    threshold: float = 0.0
    description: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()


# ─────────────────────────────────────────────
# Chain Mapping — welke chain hoort bij welk event?
# ─────────────────────────────────────────────

CHAIN_FOR_EVENT: dict[EventType, str] = {
    EventType.ORDER_CREATED:     "ORDER_VALIDATION",
    EventType.PAYMENT_FAILED:    "PAYMENT_RECOVERY",
    EventType.FRAUD_DETECTED:    "FRAUD_EXPLANATION",
    EventType.INVENTORY_LOW:     "REORDER_NOTIFICATION",
    EventType.CODE_RELEASED:     "DEV_INTELLIGENCE",
    EventType.ANOMALY_DETECTED:  "ANOMALY_ACTION",
    EventType.HITL_REQUIRED:     "HITL_ESCALATION",
}


# ─────────────────────────────────────────────
# EventBus
# ─────────────────────────────────────────────

class EventBus:
    """
    Eenvoudige in-memory event bus met idempotency en handler registratie.

    In productie: vervang door Redis Streams of PostgreSQL LISTEN/NOTIFY.
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list] = {}
        self._processed_ids: set[str] = set()

    def subscribe(self, event_type: EventType, handler: Any) -> None:
        """Registreer een handler voor een event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> bool:
        """
        Publiceer een event naar alle geregistreerde handlers.

        Returns:
            True als verwerkt, False als al eerder verwerkt (idempotent skip).
        """
        if event.event_id in self._processed_ids:
            logger.debug(
                "Event %s (%s) al eerder verwerkt — skip (idempotent)",
                event.event_id, event.event_type.value,
            )
            return False

        self._processed_ids.add(event.event_id)
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug("Geen handlers voor event type: %s", event.event_type.value)
            return True

        for handler in handlers:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception:
                logger.exception(
                    "Handler fout bij event %s (%s)",
                    event.event_type.value, event.event_id,
                )

        logger.info(
            "Event gepubliceerd: type=%s event_id=%s trace_id=%s",
            event.event_type.value, event.event_id, event.trace_id,
        )
        return True

    def get_chain(self, event_type: EventType) -> str | None:
        """Geef de skill chain terug die hoort bij dit event type."""
        return CHAIN_FOR_EVENT.get(event_type)


# Singleton event bus
_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Geef de singleton EventBus terug."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
