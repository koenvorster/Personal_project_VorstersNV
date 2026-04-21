---
paths:
  - "db/migrations/**/*.py"
  - "alembic.ini"
  - "alembic_analytics.ini"
---

# Alembic Migratie Conventies

## Project Context

VorstersNV heeft TWO alembic configuraties:
- `alembic.ini` — hoofddatabase (api schema)
- `alembic_analytics.ini` — analytics schema

Migraties staan in `db/migrations/versions/`.

---

## Verplichte Regels

### upgrade EN downgrade — VERPLICHT

Elke migratie heeft ALTIJD een functionele `upgrade()` EN `downgrade()` functie.
Nooit `pass` of `raise NotImplementedError()` in `downgrade()`.

```python
# GOED
def upgrade() -> None:
    op.add_column("products", sa.Column("slug", sa.String(255), nullable=True))
    op.create_index("ix_products_slug", "products", ["slug"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_products_slug", table_name="products")
    op.drop_column("products", "slug")

# SLECHT
def downgrade() -> None:
    pass  # NOOIT — maak downgrade onmogelijk
```

### Nooit handmatig tabellen wijzigen — VERPLICHT

Alle schema-wijzigingen gaan via Alembic migraties. Nooit direct `ALTER TABLE`, `ADD COLUMN`
etc. uitvoeren op de database zonder bijbehorende migratie.

### Migration message is verplicht — VERPLICHT

```bash
# GOED — beschrijvende naam
alembic revision --autogenerate -m "add_slug_column_to_products"
alembic revision --autogenerate -m "add_klant_adres_table"
alembic revision -m "seed_initial_categories"

# SLECHT — vage naam
alembic revision -m "update"
alembic revision -m "changes"
alembic revision -m "fix"
```

### Test altijd na aanmaken — VERPLICHT

```bash
# Na het aanmaken van een migratie, test altijd:
alembic upgrade head      # migratie toepassen
alembic downgrade -1      # een stap terug
alembic upgrade head      # opnieuw toepassen (idempotentie check)
```

---

## Veelvoorkomende Patronen

### Kolom toevoegen (nullable eerst, dan not null)

```python
# Stap 1: voeg nullable kolom toe
def upgrade() -> None:
    op.add_column("orders", sa.Column("tracking_code", sa.String(100), nullable=True))

# Stap 2 (aparte migratie): vul data in + maak not null
def upgrade() -> None:
    op.execute("UPDATE orders SET tracking_code = 'ONBEKEND' WHERE tracking_code IS NULL")
    op.alter_column("orders", "tracking_code", nullable=False)
```

### Index aanmaken

```python
def upgrade() -> None:
    op.create_index(
        "ix_orders_klant_id_status",
        "orders",
        ["klant_id", "status"],
        unique=False
    )

def downgrade() -> None:
    op.drop_index("ix_orders_klant_id_status", table_name="orders")
```

### Foreign key toevoegen

```python
def upgrade() -> None:
    op.add_column("orders", sa.Column("klant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_orders_klant_id",
        "orders", "klanten",
        ["klant_id"], ["id"],
        ondelete="SET NULL"
    )

def downgrade() -> None:
    op.drop_constraint("fk_orders_klant_id", "orders", type_="foreignkey")
    op.drop_column("orders", "klant_id")
```

---

## Autogenerate Waarschuwingen

Autogenerate detecteert NIET altijd:
- Wijzigingen in `server_default`
- PostgreSQL ENUM wijzigingen
- Partial indexes
- Trigger wijzigingen

Controleer altijd de gegenereerde migratie vóór gebruik.

---

## Data Migraties

Gebruik `op.execute()` voor data-transformaties:

```python
def upgrade() -> None:
    # Schema wijziging
    op.add_column("products", sa.Column("prijs_excl_btw", sa.Numeric(10, 2)))
    
    # Data migratie
    op.execute("""
        UPDATE products 
        SET prijs_excl_btw = ROUND(prijs / 1.21, 2)
        WHERE prijs IS NOT NULL
    """)
```
