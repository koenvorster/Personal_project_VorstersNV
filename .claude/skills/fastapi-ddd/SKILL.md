---
name: fastapi-ddd
description: >
  Use when: implementing FastAPI endpoints, SQLAlchemy async patterns, DDD aggregates/services/
  repositories, Pydantic v2 schemas, Alembic migrations, pytest async API tests.
  Triggers: "fastapi", "sqlalchemy", "async endpoint", "alembic", "pydantic", "ddd", "repository"
---

# SKILL: FastAPI + DDD Patterns

Reference knowledge for implementing FastAPI endpoints using Domain-Driven Design patterns in the VorstersNV platform.

## Project Layout

```
api/
├── main.py                 ← app factory, lifespan, middleware
├── auth/                   ← auth dependencies
├── routers/                ← thin route handlers (no business logic)
│   ├── products.py
│   ├── orders.py
│   ├── inventory.py
│   ├── betalingen.py       ← Mollie webhooks
│   └── ...
├── schemas/                ← Pydantic v2 request/response models
├── services/               ← domain services (business logic)
├── repositories/           ← data access layer
├── models/                 ← SQLAlchemy ORM models
└── domain/                 ← DDD: aggregates, value objects, events
tests/
```

## FastAPI Patterns

### App Factory
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await db.connect()
    yield
    # shutdown
    await db.disconnect()

app = FastAPI(title="VorstersNV API", lifespan=lifespan)
app.include_router(orders.router)
```

### Dependency Injection
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
```

### Route Handler (thin)
```python
@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    payload: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> OrderResponse:
    return await OrderService(db).create(payload, user.id)
```

### Background Tasks
```python
@router.post("/orders/{id}/confirm")
async def confirm_order(id: int, background_tasks: BackgroundTasks, db=Depends(get_db)):
    order = await OrderService(db).confirm(id)
    background_tasks.add_task(notify_customer, order.customer_email)
    return {"status": "confirmed"}
```

## Pydantic v2 Schemas

```python
from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    price: Decimal
    stock: int = 0

class ProductCreate(ProductBase):
    category_id: int

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be positive")
        return v
```

## SQLAlchemy Async Models

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
import datetime

class Base(DeclarativeBase):
    pass

class OrderModel(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    lines: Mapped[list["OrderLineModel"]] = relationship(back_populates="order", lazy="selectin")
```

## Alembic Commands

```bash
# Init (once)
alembic init alembic

# Generate from model changes
alembic revision --autogenerate -m "add_orders_table"

# Apply
alembic upgrade head

# Rollback one
alembic downgrade -1

# Show history
alembic history --verbose
```

## Domain Events Pattern

```python
# In service layer, after business operation:
order = await repo.get(order_id)
order.confirm()                    # emits OrderConfirmed event
events = order.pull_events()

for event in events:
    await event_bus.publish(event)  # async publish
```

## Error Handling

```python
from fastapi import HTTPException

class DomainError(Exception):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

# In route handler:
try:
    order = await service.cancel(order_id)
except DomainError as e:
    raise HTTPException(status_code=422, detail={"code": e.code, "message": e.message})
```

## Testing

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.anyio
async def test_create_product(client):
    resp = await client.post("/products/", json={"name": "Widget", "price": "9.99", "category_id": 1})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Widget"
```

## Mollie Webhook

```python
import mollie
from fastapi import Request

client = mollie.api.client.Client()
client.set_api_key(settings.MOLLIE_API_KEY)

@router.post("/webhook/mollie")
async def mollie_webhook(request: Request, db=Depends(get_db)) -> dict:
    form = await request.form()
    payment_id = form.get("id")
    if not payment_id:
        raise HTTPException(400, "Missing payment id")
    payment = client.payments.get(payment_id)
    if payment.status == "paid":
        await OrderService(db).mark_paid(payment.metadata["order_id"])
    return {"received": True}
```

## Common Patterns Anti-Patterns

| ✅ DO | ❌ DON'T |
|-------|---------|
| `async def` for all routes | Sync route handlers in async app |
| Guard clauses (early return) | Deep nesting with multiple else blocks |
| Pydantic v2 `model_validate()` | `parse_obj()` (removed in v2) |
| `select(Model).where(...)` | `session.query(Model).filter(...)` |
| Domain logic in services | Business logic in route handlers |
| Alembic for schema changes | `Base.metadata.create_all()` in production |
| `model_config = ConfigDict(from_attributes=True)` | `class Config: orm_mode = True` (Pydantic v1) |
