---
mode: agent
description: Maak een Alembic database migratie aan voor VorstersNV. Genereert het SQLAlchemy model en de bijbehorende migratiefile.
---

# Database Migratie Generator

Maak een complete Alembic-migratie aan voor VorstersNV.

## Gevraagde informatie
- **Wat verandert**: [nieuwe tabel / kolom toevoegen / kolom wijzigen / index]
- **Bounded context**: [Catalog / Orders / Inventory / Customer / Payments]
- **Tabel naam**: [snake_case meervoud, bijv. "products"]

## Wat te genereren

### 1. SQLAlchemy Model update (`db/models/<resource>.py`)

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Boolean, ForeignKey, Index
from db.models.base import Base, TimestampMixin
import uuid
from decimal import Decimal

class <Model>(Base, TimestampMixin):
    __tablename__ = "<tabel>"
    __table_args__ = (
        Index("idx_<tabel>_<kolom>", "<kolom>"),  # voeg indexen toe
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # ... kolommen
```

### 2. Alembic Autogenerate Commando
```bash
# Vanuit project root
alembic revision --autogenerate -m "<beschrijving van de wijziging>"

# Controleer de gegenereerde migratie in db/migrations/versions/
# Pas aan indien nodig (autogenerate is niet altijd perfect)

# Toepassen
alembic upgrade head
```

### 3. Handmatige Migratie (indien nodig)
```python
# db/migrations/versions/<timestamp>_<beschrijving>.py
def upgrade() -> None:
    op.create_table("<tabel>",
        sa.Column("id", sa.UUID(), nullable=False),
        # ...
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_<tabel>_<kolom>", "<tabel>", ["<kolom>"])

def downgrade() -> None:
    op.drop_index("idx_<tabel>_<kolom>")
    op.drop_table("<tabel>")
```

### 4. Alembic Configuratie Check
Zorg dat `alembic.ini` correct verwijst naar de database:
```ini
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/vorsternsnv
```

En `db/migrations/env.py` importeert alle modellen:
```python
from db.models import Base  # importeer alle models
target_metadata = Base.metadata
```

## Migratie Regels
- Elke migratie heeft een `upgrade()` EN `downgrade()`
- Geen data-destructieve operaties zonder backup-stap
- Indexen aanmaken voor alle foreign keys en veelgebruikte filterkolommen
- Test: `alembic downgrade -1 && alembic upgrade head` moet foutloos werken
