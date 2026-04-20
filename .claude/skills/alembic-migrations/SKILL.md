---
name: alembic-migrations
description: >
  Use when: creating Alembic migrations, troubleshooting schema drift, running upgrade/downgrade,
  handling async engine config for Alembic, or adding columns/tables to the VorstersNV database.
  Triggers: "migration", "alembic", "schema change", "kolom toevoegen", "tabel aanmaken", "upgrade head"
---

# SKILL: Alembic Migrations — VorstersNV

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
