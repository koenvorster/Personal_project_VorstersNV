---
name: alembic-migrations
description: >
  Use when: creating Alembic migrations, troubleshooting schema drift, running upgrade/downgrade,
  handling async engine config for Alembic, or adding columns/tables to the VorstersNV database.
  Triggers: "migration", "alembic", "schema change", "kolom toevoegen", "tabel aanmaken", "upgrade head"
---

# SKILL: Alembic Migrations — VorstersNV

## ⚠️ VorstersNV heeft TWEE Alembic configuraties

```
alembic.ini             ← Hoofddatabase (api schema) — meest gebruikt
alembic_analytics.ini   ← Analytics schema (apart schema voor rapportage)
```

Bij alle commando's: specificeer welke config je gebruikt met `-c`:
```bash
# Hoofddatabase (default)
alembic upgrade head

# Analytics database
alembic -c alembic_analytics.ini upgrade head
```

## Project setup

```
alembic.ini                  ← Alembic config (sqlalchemy.url = ...)
alembic/
├── env.py                   ← Async engine setup + target_metadata
├── script.py.mako           ← Migration template
└── versions/
    └── xxxx_beschrijving.py ← Gegenereerde migrations
```

## Commando's

```bash
# Nieuwe migration genereren op basis van model-wijzigingen
alembic revision --autogenerate -m "add_product_afbeelding_column"

# Toepassen (naar HEAD)
alembic upgrade head

# Eén stap terug
alembic downgrade -1

# Huidige versie bekijken
alembic current

# Geschiedenis bekijken
alembic history --verbose

# Offline SQL genereren (voor review vóór uitvoering)
alembic upgrade head --sql > migration.sql
```

## env.py (async-compatible)

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from db.base import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    connectable = create_async_engine(config.get_main_option("sqlalchemy.url"))
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

## Migration bestand patroon

```python
"""add product afbeelding column

Revision ID: a1b2c3d4e5f6
Revises: 9z8y7x6w5v4u
Create Date: 2024-04-15 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '9z8y7x6w5v4u'

def upgrade() -> None:
    op.add_column('products',
        sa.Column('afbeelding_url', sa.String(500), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('products', 'afbeelding_url')
```

## Naamgevingsconventie

```
YYYYMMDD_omschrijving_in_snake_case
```

Voorbeelden:
- `20240415_add_product_afbeelding_column`
- `20240420_create_reviews_table`
- `20240501_add_order_tracking_status`

## Veelgebruikte operaties

### Kolom toevoegen
```python
def upgrade():
    op.add_column('products', sa.Column('gewicht_gram', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('products', 'gewicht_gram')
```

### Index toevoegen
```python
def upgrade():
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)

def downgrade():
    op.drop_index('ix_products_slug', table_name='products')
```

### Nieuwe tabel
```python
def upgrade():
    op.create_table('reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('tekst', sa.Text(), nullable=True),
        sa.Column('aangemaakt_op', sa.DateTime(), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('reviews')
```

## Gotcha's

| Probleem | Oplossing |
|---------|-----------|
| `autogenerate` mist wijzigingen | Controleer of alle modellen geïmporteerd zijn in `env.py` |
| `Target database is not up to date` | Voer `alembic upgrade head` uit vóór nieuwe migration |
| Asyncio conflict in `env.py` | Gebruik `asyncio.run()` niet in een reeds-draaiende loop |
| Productie rollback | Test `downgrade -1` altijd in staging vóór productie |
| Enum wijzigingen niet gedetecteerd | Autogenerate detecteert PostgreSQL ENUMs niet — handmatig toevoegen |
| `server_default` wijzigingen gemist | Autogenerate detecteert `server_default` wijzigingen niet |
| Analytics vs hoofddb confusion | Controleer altijd welke `alembic.ini` je gebruikt (`alembic current`) |

## Voorbeeld Gebruik

### Scenario: Voeg `tracking_code` toe aan orders tabel

**Stap 1 — Model aanpassen:**
```python
# db/models/order.py
class OrderModel(Base):
    __tablename__ = "orders"
    # ... bestaande kolommen ...
    tracking_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

**Stap 2 — Migration genereren:**
```bash
alembic revision --autogenerate -m "add_tracking_code_to_orders"
# Genereert: alembic/versions/20240501_add_tracking_code_to_orders.py
```

**Stap 3 — Gegenereerde migration controleren:**
```python
# alembic/versions/20240501_add_tracking_code_to_orders.py
def upgrade() -> None:
    op.add_column("orders",
        sa.Column("tracking_code", sa.String(100), nullable=True)
    )

def downgrade() -> None:
    op.drop_column("orders", "tracking_code")
```

**Stap 4 — Test de migration:**
```bash
alembic upgrade head      # Toepassen
alembic downgrade -1      # Terugdraaien
alembic upgrade head      # Opnieuw toepassen (idempotentiecheck)
```

**Stap 5 — In CI (GitHub Actions):**
```yaml
- name: Run migrations
  run: alembic upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Scenario: Complexe data migratie (prijs splitsen in excl/incl BTW)

```python
# alembic/versions/20240510_split_prijs_btw.py
def upgrade() -> None:
    # 1. Nieuwe kolommen toevoegen (nullable eerst)
    op.add_column("products", sa.Column("prijs_excl_btw", sa.Numeric(10, 2), nullable=True))
    op.add_column("products", sa.Column("btw_tarief", sa.Numeric(4, 2), nullable=True))

    # 2. Data migreren (21% BTW standaard)
    op.execute("""
        UPDATE products
        SET
            prijs_excl_btw = ROUND(prijs / 1.21, 2),
            btw_tarief = 0.21
        WHERE prijs IS NOT NULL
    """)

    # 3. NOT NULL maken na datavulling
    op.alter_column("products", "prijs_excl_btw", nullable=False)
    op.alter_column("products", "btw_tarief", nullable=False)

    # 4. Oude kolom verwijderen (aparte migratie aanbevolen!)
    # op.drop_column("products", "prijs")  # in volgende sprint

def downgrade() -> None:
    # Herstel prijs vanuit excl_btw + btw_tarief
    op.add_column("products", sa.Column("prijs", sa.Numeric(10, 2), nullable=True))
    op.execute("""
        UPDATE products
        SET prijs = ROUND(prijs_excl_btw * (1 + btw_tarief), 2)
    """)
    op.drop_column("products", "btw_tarief")
    op.drop_column("products", "prijs_excl_btw")
```

## Anti-patronen

| ❌ NIET | ✅ WEL |
|---------|-------|
| `downgrade()` met `pass` | Altijd functionele downgrade implementeren |
| `alembic revision -m "fix"` | Beschrijvende naam: `"add_slug_column_to_products"` |
| Direct `ALTER TABLE` in psql | Altijd via Alembic migration |
| Migration zonder te testen | Altijd `upgrade → downgrade → upgrade` cyclus draaien |
| Niet-nullable kolom direct toevoegen | Nullable toevoegen → data vullen → NOT NULL maken |
| Analytics en hoofd DB door elkaar | Altijd specificeer `-c alembic_analytics.ini` voor analytics |

## Gerelateerde skills
- fastapi-ddd
- database-explorer
