---
name: database-explorer
description: >
  Use when: querying the PostgreSQL database, understanding the VorstersNV schema,
  writing SQLAlchemy async queries, debugging lazy loading errors, analyzing
  Alembic migration history, or exploring data patterns.
  Triggers: "database query", "SQLAlchemy", "wat staat er in de DB", "schema bekijken",
  "alembic migration", "lazy loading fout", "PostgreSQL query", "data bekijken"
---

# SKILL: Database Explorer — VorstersNV

Referentiekennis voor het bevragen en begrijpen van de VorstersNV PostgreSQL database via SQLAlchemy async.

## Schema Overzicht

### Catalog Context

```sql
-- Producten en categorieën
products (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(100) UNIQUE NOT NULL,
    naam            VARCHAR(255) NOT NULL,
    beschrijving    TEXT,
    prijs_excl_btw  NUMERIC(10,2) NOT NULL,  -- Altijd excl. BTW!
    btw_tarief      NUMERIC(4,2) DEFAULT 0.21,
    categorie_id    INTEGER REFERENCES categories(id),
    actief          BOOLEAN DEFAULT TRUE,
    aangemaakt_op   TIMESTAMP DEFAULT NOW(),
    bijgewerkt_op   TIMESTAMP DEFAULT NOW()
)

categories (
    id          SERIAL PRIMARY KEY,
    naam        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    parent_id   INTEGER REFERENCES categories(id)
)
```

### Orders Context

```sql
orders (
    id              SERIAL PRIMARY KEY,
    klant_id        INTEGER REFERENCES customers(id),
    status          VARCHAR(50) DEFAULT 'aangemaakt',
    -- statussen: aangemaakt | bevestigd | verzonden | afgeleverd | geannuleerd
    aangemaakt_op   TIMESTAMP DEFAULT NOW(),
    bijgewerkt_op   TIMESTAMP DEFAULT NOW()
)

order_lines (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id      INTEGER REFERENCES products(id),
    hoeveelheid     INTEGER NOT NULL CHECK (hoeveelheid > 0),
    eenheidsprijs   NUMERIC(10,2) NOT NULL  -- Prijs op moment van bestelling
)
```

### Customer Context

```sql
customers (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    naam                VARCHAR(255) NOT NULL,
    telefoon            VARCHAR(20),
    aangemaakt_op       TIMESTAMP DEFAULT NOW(),
    geanonimiseerd_op   TIMESTAMP  -- Ingevuld na GDPR verwijderverzoek
)

addresses (
    id          SERIAL PRIMARY KEY,
    klant_id    INTEGER REFERENCES customers(id),
    type        VARCHAR(20),  -- 'levering' | 'factuur'
    straat      VARCHAR(255),
    huisnummer  VARCHAR(20),
    postcode    VARCHAR(10),
    gemeente    VARCHAR(100),
    land        VARCHAR(2) DEFAULT 'BE'
)
```

### Payments Context

```sql
payments (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(id),
    mollie_id       VARCHAR(100) UNIQUE,  -- Mollie payment ID (tr_xxx)
    status          VARCHAR(50),
    -- statussen: open | pending | paid | failed | expired | canceled | refunded
    bedrag          NUMERIC(10,2),
    aangemaakt_op   TIMESTAMP DEFAULT NOW(),
    bijgewerkt_op   TIMESTAMP DEFAULT NOW()
)
```

### Inventory Context

```sql
stock_items (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER REFERENCES products(id) UNIQUE,
    hoeveelheid     INTEGER NOT NULL DEFAULT 0,
    reorder_drempel INTEGER DEFAULT 10,
    magazijn_id     INTEGER REFERENCES warehouses(id)
)

warehouses (
    id      SERIAL PRIMARY KEY,
    naam    VARCHAR(100),
    locatie VARCHAR(255)
)
```

## SQLAlchemy Async Query Patronen

### Basis SELECT

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Enkelvoudig record
async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()

# Meerdere records met filter
async def get_active_products(session: AsyncSession) -> list[Product]:
    result = await session.execute(
        select(Product)
        .where(Product.actief == True)
        .order_by(Product.naam)
        .limit(100)
    )
    return result.scalars().all()
```

### JOIN queries

```python
from sqlalchemy.orm import selectinload, joinedload

# Eager loading (voorkomt lazy loading errors)
async def get_order_with_lines(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .options(
            selectinload(Order.lines).selectinload(OrderLine.product),
            selectinload(Order.customer)
        )
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()

# Complexe JOIN met aggregatie
async def get_customer_totals(session: AsyncSession, klant_id: int):
    result = await session.execute(
        select(
            func.count(Order.id).label("aantal_orders"),
            func.sum(OrderLine.hoeveelheid * OrderLine.eenheidsprijs).label("totaal_besteed")
        )
        .join(OrderLine, OrderLine.order_id == Order.id)
        .where(Order.klant_id == klant_id)
        .where(Order.status != 'geannuleerd')
    )
    return result.one()
```

### INSERT / UPDATE

```python
# INSERT
async def create_order(session: AsyncSession, data: OrderCreateRequest) -> Order:
    order = Order(
        klant_id=data.klant_id,
        status="aangemaakt"
    )
    session.add(order)
    await session.flush()  # Geeft ID terug zonder commit
    return order

# UPDATE via ORM (veilig)
async def confirm_order(session: AsyncSession, order_id: int) -> None:
    order = await session.get(Order, order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    order.status = "bevestigd"
    order.bijgewerkt_op = datetime.utcnow()
    await session.flush()
```

## Handige Queries (Copy-Paste Klaar)

### Dashboard queries

```sql
-- Dagelijkse omzet laatste 30 dagen
SELECT
    DATE(o.aangemaakt_op) as datum,
    COUNT(DISTINCT o.id) as orders,
    SUM(ol.hoeveelheid * ol.eenheidsprijs) as omzet_excl_btw
FROM orders o
JOIN order_lines ol ON ol.order_id = o.id
WHERE o.status IN ('bevestigd', 'verzonden', 'afgeleverd')
AND o.aangemaakt_op > NOW() - INTERVAL '30 days'
GROUP BY DATE(o.aangemaakt_op)
ORDER BY datum DESC;

-- Top 10 producten per omzet
SELECT
    p.naam,
    p.sku,
    SUM(ol.hoeveelheid) as totaal_verkocht,
    SUM(ol.hoeveelheid * ol.eenheidsprijs) as totaal_omzet
FROM order_lines ol
JOIN products p ON ol.product_id = p.id
JOIN orders o ON ol.order_id = o.id
WHERE o.status NOT IN ('geannuleerd')
GROUP BY p.id, p.naam, p.sku
ORDER BY totaal_omzet DESC
LIMIT 10;
```

### Operationele queries

```sql
-- Openstaande bestellingen ouder dan 24 uur
SELECT o.id, o.aangemaakt_op, c.email,
       COUNT(ol.id) as lijnen,
       SUM(ol.hoeveelheid * ol.eenheidsprijs) as totaal
FROM orders o
JOIN customers c ON o.klant_id = c.id
JOIN order_lines ol ON ol.order_id = o.id
WHERE o.status = 'aangemaakt'
AND o.aangemaakt_op < NOW() - INTERVAL '24 hours'
GROUP BY o.id, o.aangemaakt_op, c.email
ORDER BY o.aangemaakt_op ASC
LIMIT 50;

-- Voorraad kritiek (onder reorder-drempel)
SELECT p.naam, p.sku, si.hoeveelheid, si.reorder_drempel,
       (si.reorder_drempel - si.hoeveelheid) as tekort
FROM stock_items si
JOIN products p ON si.product_id = p.id
WHERE si.hoeveelheid <= si.reorder_drempel
AND p.actief = TRUE
ORDER BY tekort DESC;
```

## Veelvoorkomende Fouten

### MissingGreenlet / DetachedInstance

```python
# ❌ FOUT: Toegang tot lazy-loaded relatie buiten session
order = await session.get(Order, 1)
# Session gesloten...
print(order.lines)  # DetachedInstanceError!

# ✅ FIX: Gebruik selectinload of joinedload
result = await session.execute(
    select(Order)
    .options(selectinload(Order.lines))
    .where(Order.id == 1)
)
order = result.scalar_one()
print(order.lines)  # ✅ Werkt
```

### N+1 Query probleem

```python
# ❌ FOUT: N+1 queries
orders = (await session.execute(select(Order))).scalars().all()
for order in orders:
    print(order.klant.email)  # Aparte query per order!

# ✅ FIX: Join in één query
orders = (await session.execute(
    select(Order).options(selectinload(Order.klant))
)).scalars().all()
```

## Alembic Commando's

```bash
# Status bekijken
alembic current          # Huidige versie
alembic history          # Alle migraties
alembic heads            # Laatste versie(s)

# Nieuwe migratie
alembic revision --autogenerate -m "add_kolom_aan_tabel"

# Uitvoeren
alembic upgrade head     # Naar laatste
alembic upgrade +1       # Één stap vooruit

# Terugdraaien
alembic downgrade -1     # Één stap terug
alembic downgrade [rev]  # Naar specifieke revisie
```
