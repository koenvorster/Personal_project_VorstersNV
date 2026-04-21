---
name: order-lifecycle
version: "1.0"
domain: orders
audience: [agents, developers]
tags: [order, state-machine, lifecycle, retour, sla, timeout]
---

# Order Lifecycle

## Beschrijving
De volledige order lifecycle voor VorstersNV: alle statussen, toegestane transities,
timeout-regels, retouren en SLA-targets voor elke fase.

## Wanneer gebruiken
- Bij order verwerking en statusupdates
- Bij klantcommunicatie over orderstatus
- Bij het implementeren van state machine logica
- Bij SLA-monitoring en alerting
- Bij retour- en refund afhandeling
- Bij het debuggen van vastgelopen orders

## Kernkennis

### Order staten (happy path)
```
PENDING → VALIDATED → PAYMENT_PENDING → PAID → PROCESSING → SHIPPED → DELIVERED → COMPLETED
```

| Status            | Betekenis                                               |
|-------------------|---------------------------------------------------------|
| `PENDING`         | Order aangemaakt, nog niet bevestigd                    |
| `VALIDATED`       | Fraudecheck geslaagd, stock gereserveerd                |
| `PAYMENT_PENDING` | Klant doorgestuurd naar betaalpagina                    |
| `PAID`            | Mollie bevestigt betaling                               |
| `PROCESSING`      | Warehouse heeft order ontvangen, klaar voor verzending  |
| `SHIPPED`         | Track & trace code toegewezen                           |
| `DELIVERED`       | Bezorgbevestiging ontvangen van carrier                 |
| `COMPLETED`       | Herroepingstermijn verstreken, order gesloten           |

### Foutstromen
| Status            | Trigger                                                 |
|-------------------|---------------------------------------------------------|
| `PAYMENT_FAILED`  | Mollie: failed / expired / canceled                     |
| `FRAUD_BLOCKED`   | Fraudescore ≥ 75                                        |
| `OUT_OF_STOCK`    | Stock niet beschikbaar bij PROCESSING                   |
| `CANCELLED`       | Klant annuleert (enkel mogelijk t/m PAYMENT_PENDING)    |
| `REFUNDED`        | Terugbetaling volledig verwerkt                         |

### Toegestane transities (state machine)
```python
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {
        OrderStatus.VALIDATED,
        OrderStatus.FRAUD_BLOCKED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.VALIDATED: {
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.OUT_OF_STOCK,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAYMENT_PENDING: {
        OrderStatus.PAID,
        OrderStatus.PAYMENT_FAILED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAID: {
        OrderStatus.PROCESSING,
        OrderStatus.OUT_OF_STOCK,
    },
    OrderStatus.PROCESSING: {
        OrderStatus.SHIPPED,
        OrderStatus.OUT_OF_STOCK,
    },
    OrderStatus.SHIPPED: {
        OrderStatus.DELIVERED,
    },
    OrderStatus.DELIVERED: {
        OrderStatus.COMPLETED,
        OrderStatus.RETURN_REQUESTED,
    },
    OrderStatus.COMPLETED: {
        OrderStatus.RETURN_REQUESTED,  # binnen 14 dagen
    },
    OrderStatus.RETURN_REQUESTED: {
        OrderStatus.RETURN_RECEIVED,
    },
    OrderStatus.RETURN_RECEIVED: {
        OrderStatus.REFUNDED,
    },
    OrderStatus.PAYMENT_FAILED: {
        OrderStatus.PAYMENT_PENDING,  # klant kan opnieuw proberen
        OrderStatus.CANCELLED,
    },
}

def transition(order: Order, new_status: OrderStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"Transitie {order.status} → {new_status} niet toegestaan"
        )
    order.status = new_status
```

### Timeout regels
| Van status        | Timeout   | Actie                                          |
|-------------------|-----------|------------------------------------------------|
| `PENDING`         | 30 minuten| Auto-cancel: transitie naar `CANCELLED`        |
| `PAYMENT_PENDING` | 2 uur     | Herinnering e-mail naar klant                  |
| `PAYMENT_PENDING` | 4 uur     | Auto-cancel: transitie naar `CANCELLED`        |
| `PROCESSING`      | 3 werkdagen| Alert naar warehouse-team                     |
| `SHIPPED`         | 10 dagen  | Alert: pakket mogelijk verloren                |

```python
TIMEOUTS: dict[OrderStatus, timedelta] = {
    OrderStatus.PENDING: timedelta(minutes=30),
    OrderStatus.PAYMENT_PENDING: timedelta(hours=4),
    OrderStatus.PROCESSING: timedelta(days=3),
    OrderStatus.SHIPPED: timedelta(days=10),
}

async def check_timeouts(repo: OrderRepository) -> None:
    """Periodieke job (elke 5 min) — controleert verlopen orders."""
    for status, timeout in TIMEOUTS.items():
        cutoff = datetime.now() - timeout
        expired_orders = await repo.find_older_than(status, cutoff)
        for order in expired_orders:
            await handle_timeout(order, status)
```

### Retour flow
```
DELIVERED/COMPLETED → RETURN_REQUESTED → RETURN_RECEIVED → REFUNDED
```

Regels:
- Maximaal **14 kalenderdagen** na levering (herroepingsrecht)
- Klant initieert retour via portaal of klantenservice
- Retourbevestiging per e-mail met retourlabel
- Bij ontvangst retour: inspectie, dan refund initiëren via Mollie
- Gedeeltelijke retour: enkel de geretourneerde orderregels terugbetalen

```python
async def request_return(order_id: str, reason: str, lines: list[str]) -> Return:
    order = await repo.get(order_id)
    if order.status not in (OrderStatus.DELIVERED, OrderStatus.COMPLETED):
        raise DomainError("Retour enkel mogelijk na levering")
    days_since_delivery = (datetime.now() - order.delivered_at).days
    if days_since_delivery > 14:
        raise DomainError("Herroepingstermijn van 14 dagen verstreken")
    return_request = Return(order_id=order_id, reason=reason, lines=lines)
    transition(order, OrderStatus.RETURN_REQUESTED)
    await repo.save(order)
    return return_request
```

### SLA targets
| Fase                       | SLA Target        | Meting                          |
|----------------------------|-------------------|---------------------------------|
| Order validatie            | < 2 seconden      | PENDING → VALIDATED             |
| Betaalverificatie          | < 5 seconden      | Mollie webhook verwerking       |
| Verzendbevestiging         | < 1 uur           | PAID → PROCESSING               |
| Levering binnenland (BE)   | 1-2 werkdagen     | SHIPPED → DELIVERED             |
| Refund verwerking          | ≤ 14 dagen        | RETURN_RECEIVED → REFUNDED      |
| Klantcommunicatie statuswijziging | < 5 min   | Statuswijziging → e-mail verstuurd |

## Voorbeelden

### Order flow in service
```python
async def process_order(cmd: ConfirmOrderCommand) -> Order:
    order = await repo.get(cmd.order_id)

    # Stap 1: Fraudecheck
    fraud_result = await fraud_service.check(order)
    if fraud_result.is_blocked:
        transition(order, OrderStatus.FRAUD_BLOCKED)
        await repo.save(order)
        raise FraudBlockedException(order.id)

    # Stap 2: Stock reserveren
    await inventory_service.reserve(order)

    # Stap 3: Naar VALIDATED
    transition(order, OrderStatus.VALIDATED)

    # Stap 4: Betaallink aanmaken
    payment = await mollie_service.create_payment(order)
    transition(order, OrderStatus.PAYMENT_PENDING)

    await repo.save(order)
    return order, payment.checkout_url
```

### Status monitoring query
```python
async def get_stuck_orders() -> list[Order]:
    """Geeft orders terug die langer dan verwacht in een status zitten."""
    stuck = []
    for status, timeout in TIMEOUTS.items():
        cutoff = datetime.now() - timeout
        orders = await repo.find_older_than(status, cutoff)
        stuck.extend(orders)
    return stuck
```

## Gerelateerde skills
- mollie-payments
- fraud-patterns
- ddd-patterns
- belgian-commerce
