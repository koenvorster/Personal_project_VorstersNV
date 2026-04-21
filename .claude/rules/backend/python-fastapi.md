---
paths:
  - "**/*.py"
---

# Backend Conventies — Python 3.12 + FastAPI

## Project Context

Dit is het VorstersNV platform. De **primaire backend is FastAPI** in `api/` — niet Spring Boot in `backend/`.
Bij elke `.py` bestand: check eerst of het in `api/`, `webhooks/`, `tests/`, of `scripts/` staat.

---

## Strictheidsgraden

- **VERPLICHT** — alle Python bestanden in dit project
- **STRICT** — nieuwe code; refactor bestaande code alleen op expliciet verzoek
- **AANBEVOLEN** — best practice; suggereer maar dwing niet af

---

## Async/Await — VERPLICHT

**Alle database-operaties zijn async.** Gebruik nooit synchrone SQLAlchemy calls.

```python
# GOED
async def get_product(product_id: int, db: AsyncSession) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

# SLECHT — synchrone sessie in async context
def get_product(product_id: int, db: Session) -> Product:
    return db.query(Product).filter(Product.id == product_id).first()
```

FastAPI route handlers zijn altijd `async def`.

---

## Type Hints — VERPLICHT

Type hints zijn verplicht op alle functie-parameters en return types.

```python
# GOED
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    ...

# SLECHT
async def create_order(order_data, db, current_user=None):
    ...
```

- Gebruik `from __future__ import annotations` bovenaan voor forward references
- `Optional[X]` schrijf je als `X | None` (Python 3.10+ stijl)
- `Union[X, Y]` schrijf je als `X | Y`

---

## SQLAlchemy 2.x Async — VERPLICHT

```python
# GOED — SQLAlchemy 2.x stijl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Selecteren met eager loading (voorkom N+1 queries)
orders = await db.execute(
    select(Order)
    .options(selectinload(Order.order_lines).selectinload(OrderLine.product))
    .where(Order.klant_id == klant_id)
)

# Aanmaken
db.add(new_product)
await db.commit()
await db.refresh(new_product)

# SLECHT — legacy query API
db.query(Product).filter(Product.actief == True).all()
```

---

## Pydantic v2 — VERPLICHT

```python
# GOED — Pydantic v2 stijl
from pydantic import BaseModel, ConfigDict, field_validator

class ProductCreate(BaseModel):
    naam: str
    prijs: Decimal
    voorraad: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("prijs")
    @classmethod
    def prijs_positief(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Prijs moet positief zijn")
        return v

# SLECHT — Pydantic v1 syntax
class ProductCreate(BaseModel):
    class Config:
        orm_mode = True  # <-- VEROUDERD
```

Migratiecheatsheet:
- `orm_mode = True` → `model_config = ConfigDict(from_attributes=True)`
- `@validator` → `@field_validator` (met `@classmethod`)
- `.dict()` → `.model_dump()`
- `.parse_obj()` → `model_validate()`

---

## Logging — VERPLICHT

**Nooit `print()` in productiecode.**

```python
import logging
logger = logging.getLogger(__name__)

# GOED
async def process_order(order_id: int) -> None:
    logger.info("Order verwerking gestart", extra={"order_id": order_id})
    try:
        ...
    except Exception as e:
        logger.error("Order verwerking mislukt", extra={"order_id": order_id}, exc_info=True)
        raise

# SLECHT
print(f"Order {order_id} verwerking gestart")
```

Log levels:
- `debug` — ontwikkelingsdetails
- `info` — business events (order aangemaakt, betaling ontvangen)
- `warning` — onverwacht maar herstelbaar (retry, fallback)
- `error` — fout die actie vereist; altijd met `exc_info=True`
- `critical` — systeem kan niet verder

---

## Guard Clauses — VERPLICHT

Max 2 nesting levels. Gebruik early returns voor validatie.

```python
# GOED — guard clauses
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product niet gevonden")
    if not product.actief:
        raise HTTPException(status_code=400, detail="Inactief product")
    product.naam = data.naam or product.naam
    await db.commit()
    return product

# SLECHT — diep genest
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if product:
        if product.actief:
            ...  # te diep genest
```

## Anti-patterns

Fouten die **verplicht voorkomen** moeten worden. Deze patronen breken de DDD-architectuur,
introduceren security-risico's of maken de codebase moeilijk te testen.

```python
# ❌ ANTI-PATTERN 1: Business logica in route handler
@router.post("/orders")
async def create_order(payload: OrderCreate, db=Depends(get_db)):
    # Business logica hoort NIET in de router!
    product = await db.get(Product, payload.product_id)
    if product.voorraad < payload.quantity:
        raise HTTPException(400, "Onvoldoende voorraad")
    product.voorraad -= payload.quantity
    order = Order(**payload.dict())
    db.add(order)
    await db.commit()
    return order

# ✅ CORRECT: Dunne router, logica in service
@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(payload: OrderCreate, db=Depends(get_db)) -> OrderResponse:
    return await OrderService(db).create(payload)
```

```python
# ❌ ANTI-PATTERN 2: Synchrone DB calls in async context
def get_all_products(db: Session) -> list[Product]:
    return db.query(Product).all()  # Blokkeert de event loop!

# ✅ CORRECT
async def get_all_products(db: AsyncSession) -> list[Product]:
    result = await db.execute(select(Product))
    return result.scalars().all()
```

```python
# ❌ ANTI-PATTERN 3: SQL injectie via f-string
async def search(query: str, db: AsyncSession):
    results = await db.execute(
        text(f"SELECT * FROM products WHERE naam LIKE '%{query}%'")  # SQL injectie!
    )

# ✅ CORRECT: Parametriseerde query
async def search(query: str, db: AsyncSession):
    results = await db.execute(
        select(Product).where(Product.naam.ilike(f"%{query}%"))
    )
```

```python
# ❌ ANTI-PATTERN 4: print() in productiecode
async def process_order(order_id: int) -> None:
    print(f"Processing order {order_id}")  # Verschijnt niet in log aggregatie!

# ✅ CORRECT
import logging
logger = logging.getLogger(__name__)

async def process_order(order_id: int) -> None:
    logger.info("Order verwerking gestart", extra={"order_id": order_id})
```

```python
# ❌ ANTI-PATTERN 5: N+1 queries door lazy loading
orders = (await db.execute(select(Order))).scalars().all()
for order in orders:
    print(order.klant.email)  # Aparte DB query per order = N+1!

# ✅ CORRECT: Eager loading in één query
orders = (await db.execute(
    select(Order).options(selectinload(Order.klant))
)).scalars().all()
```

```python
# ❌ ANTI-PATTERN 6: Pydantic v1 syntax (ORM mode)
class ProductResponse(BaseModel):
    class Config:
        orm_mode = True  # Pydantic v1 — werkt niet in v2!

# ✅ CORRECT: Pydantic v2
class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

---

## DDD-structuur — STRICT

```
api/
  routers/          # FastAPI routers (controller layer) — max ~5 regels per endpoint
  models/           # SQLAlchemy ORM modellen — alleen datahouders, geen business logica
  schemas/          # Pydantic request/response schemas
  services/         # Business logica — alle DB-aanroepen gaan hier
  dependencies.py   # FastAPI Depends()
```

---

## Beveiliging — VERPLICHT

- Nooit secrets in code — gebruik `os.getenv()` of Pydantic `BaseSettings`
- Nooit `f"SELECT ... {user_input}"` — gebruik altijd SQLAlchemy parametrisatie
- Valideer alle input via Pydantic schema vóór database-operaties
- CORS: nooit `allow_origins=["*"]` in productie
