---
name: ddd-patterns
version: "1.0"
domain: architecture
audience: [agents, developers]
tags: [ddd, aggregates, domain-events, bounded-context, repository, value-objects]
---

# DDD Patterns

## Beschrijving
Domain-Driven Design patronen voor het VorstersNV platform: bounded contexts,
aggregates, domain events, repository pattern, value objects en anti-corruption layers.

## Wanneer gebruiken
- Bij het ontwerpen van nieuwe features
- Bij refactoring van bestaande modules
- Bij API contract design
- Bij het modelleren van businesslogica
- Bij het definiëren van service-grenzen

## Kernkennis

### Bounded Contexts
| Context    | Verantwoordelijkheid                                        |
|------------|-------------------------------------------------------------|
| Order      | Orderlevenscyclus: aanmaken, valideren, verwerken, annuleren|
| Payment    | Betaalintegratie (Mollie), betalingsstatus, refunds         |
| Inventory  | Voorraad, reserveringen, stockbeheer                        |
| Customer   | Klantprofiel, authenticatie, adresbeheer                    |
| Fraud      | Risicobeoordeling, blocklist, audit trail                   |

Communicatie tussen contexts via **domain events** — nooit directe DB-calls.

### Aggregates
**Order Aggregate** (meest centraal):
```
Order (Aggregate Root)
├── OrderLine (Entity)
│   ├── product_id: str
│   ├── quantity: int
│   └── unit_price: Money (Value Object)
├── shipping_address: Address (Value Object)
├── customer_id: CustomerId (Value Object)
└── status: OrderStatus (Enum)
```

Regels:
- Alleen de aggregate root heeft een repository
- Alle mutaties verlopen via methodes op de root
- Invarianten worden gehandhaafd binnen de aggregate

```python
class Order:  # Aggregate Root
    def add_line(self, product_id: str, qty: int, price: Money) -> None:
        if self.status != OrderStatus.PENDING:
            raise DomainError("Kan geen items toevoegen aan bevestigde order")
        self._lines.append(OrderLine(product_id, qty, price))
        self._events.append(OrderLineAdded(self.id, product_id, qty))

    def confirm(self) -> None:
        if not self._lines:
            raise DomainError("Order heeft geen orderregels")
        self.status = OrderStatus.VALIDATED
        self._events.append(OrderCreated(self.id, self.customer_id, self.total))

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events
```

### Domain Events
| Event               | Trigger                            | Consumers                          |
|---------------------|------------------------------------|------------------------------------|
| `OrderCreated`      | Order bevestigd door klant         | Payment, Inventory, Fraud          |
| `OrderPaid`         | Mollie webhook: status = paid      | Order (→ PAID), Inventory, Email   |
| `OrderShipped`      | Track & trace code toegevoegd      | Order (→ SHIPPED), Email           |
| `FraudDetected`     | Risk score ≥ 75                    | Order (→ FRAUD_BLOCKED), Alert     |
| `StockReserved`     | Voorraad gereserveerd voor order   | Order (→ PROCESSING)               |
| `RefundInitiated`   | Terugbetaling gestart              | Payment, Order (→ REFUNDED)        |

```python
@dataclass(frozen=True)
class OrderPaid:
    order_id: str
    payment_id: str
    amount: Money
    paid_at: datetime = field(default_factory=datetime.now)
    event_type: str = "OrderPaid"
```

### Repository Pattern
```python
class OrderRepository(ABC):
    @abstractmethod
    async def get(self, order_id: str) -> Order:
        ...

    @abstractmethod
    async def save(self, order: Order) -> None:
        ...

    @abstractmethod
    async def find_by_customer(self, customer_id: str) -> list[Order]:
        ...

class SqlOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, order_id: str) -> Order:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise OrderNotFoundError(order_id)
        return self._to_domain(model)

    async def save(self, order: Order) -> None:
        model = self._to_model(order)
        await self._session.merge(model)
        # Publiceer events na succesvolle opslag
        for event in order.pull_events():
            await self._event_bus.publish(event)
```

### Value Objects
```python
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "EUR"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Valuta mismatch: {self.currency} ≠ {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"

@dataclass(frozen=True)
class Address:
    street: str
    number: str
    postal_code: str
    city: str
    country: str = "BE"

@dataclass(frozen=True)
class CustomerEmail:
    value: str

    def __post_init__(self):
        if "@" not in self.value or "." not in self.value.split("@")[-1]:
            raise ValueError(f"Ongeldig e-mailadres: {self.value}")
```

### Anti-corruption Layer
Beschermt het domeinmodel tegen externe API-veranderingen (bv. Mollie).

```python
class MolliePaymentAdapter:
    """ACL: vertaalt Mollie response naar domein Payment."""

    def to_domain(self, mollie_payment: dict) -> Payment:
        status_map = {
            "paid": PaymentStatus.PAID,
            "pending": PaymentStatus.PENDING,
            "failed": PaymentStatus.FAILED,
            "expired": PaymentStatus.EXPIRED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return Payment(
            id=mollie_payment["id"],
            order_id=mollie_payment["metadata"]["order_id"],
            status=status_map.get(mollie_payment["status"], PaymentStatus.UNKNOWN),
            amount=Money(Decimal(mollie_payment["amount"]["value"])),
        )
```

### Ubiquitous Language — Glossary
| Term              | Definitie                                                      |
|-------------------|----------------------------------------------------------------|
| Order             | Bevestigde aankoopintentie van een klant                       |
| OrderLine         | Eén productregel binnen een order (product + qty + prijs)      |
| Betaling          | Financiële transactie gekoppeld aan een order                  |
| Retour            | Terugsturen van product binnen herroepingstermijn              |
| Refund            | Terugbetaling van (deel van) het orderbedrag                   |
| Fraude            | Verdachte activiteit die order-verwerking blokkeert            |
| Reservering       | Tijdelijke stockverlaging voor een openstaande order           |
| Levering          | Fysiek transport van producten naar klant                      |

## Voorbeelden

### Volledige order aanmaken
```python
async def create_order(cmd: CreateOrderCommand, repo: OrderRepository) -> str:
    order = Order.create(
        customer_id=cmd.customer_id,
        shipping_address=Address(**cmd.shipping_address),
    )
    for line in cmd.lines:
        order.add_line(line.product_id, line.quantity, Money(line.price))
    order.confirm()
    await repo.save(order)  # publiceert OrderCreated event
    return order.id
```

## Gerelateerde skills
- order-lifecycle
- mollie-payments
- fraud-patterns
