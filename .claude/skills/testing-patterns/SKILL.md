---
name: testing-patterns
description: >
  Use when: writing pytest tests for FastAPI endpoints, setting up conftest.py fixtures,
  in-memory SQLite database overrides, async test patterns, or debugging pytest-asyncio config.
  Triggers: "schrijf test", "conftest", "fixture", "pytest", "test coverage", "asyncio test"
---

# SKILL: Testing Patterns — VorstersNV

Reference voor pytest async API-tests in het VorstersNV platform.

## Stack

- **pytest** + **pytest-asyncio** (`asyncio_mode = "auto"` in pyproject.toml)
- **anyio** voor backend-onafhankelijke async fixtures
- **httpx** + `ASGITransport` voor in-process HTTP-tests
- **SQLite + aiosqlite** voor in-memory database (geen PostgreSQL nodig in CI)
- Geen `@pytest.mark.asyncio` nodig — `asyncio_mode = "auto"` activeert dit globaal

## pyproject.toml config

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
asyncio_default_fixture_loop_scope = "function"
```

## Standaard conftest.py

```python
import pytest
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.main import app
from db.base import Base
from db.database import get_db

SQLITE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
```

## Test structuur (klasse-gebaseerd)

```python
class TestProductLijst:
    async def test_lege_lijst(self, client):
        r = await client.get("/api/products/")
        assert r.status_code == 200
        assert r.json()["items"] == []
        assert r.json()["totaal"] == 0

    async def test_actieve_producten(self, client, db_session):
        p = Product(naam="Test", slug="test", prijs=Decimal("10.00"), voorraad=5)
        db_session.add(p)
        await db_session.commit()

        r = await client.get("/api/products/")
        assert r.json()["totaal"] == 1
```

## Testdata helpers (in conftest.py)

```python
async def maak_product(
    db: AsyncSession,
    naam: str = "Test Zaadje",
    slug: str = "test-zaadje",
    prijs: Decimal = Decimal("12.50"),
    voorraad: int = 10,
    actief: bool = True,
) -> Product:
    p = Product(naam=naam, slug=slug, prijs=prijs, voorraad=voorraad, actief=actief)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p
```

## Mocking externe services

```python
from unittest.mock import AsyncMock, patch

async def test_met_mock(client, db_session):
    with patch("api.routers.betalingen.mollie_client") as mock_mollie:
        mock_mollie.payments.create.return_value = AsyncMock(
            id="PAY-test123",
            checkout_url="https://mollie.test/pay"
        )
        r = await client.post("/api/bestellingen", json={...})
    assert r.status_code == 201
```

## Bestaande tests (referentie)

| Bestand | Scope |
|---------|-------|
| `tests/conftest.py` | Gedeelde fixtures (db_engine, db_session, client, maak_product, maak_categorie) |
| `tests/test_products_api.py` | 15 tests: lijst, paginatie, zoek, categorie-filter, CRUD |
| `tests/test_betalingen_api.py` | 13 tests: bestelling aanmaken, voorraad, simuleer betaling |
| `tests/test_webhooks.py` | Mollie webhook tests (AsyncMock pattern) |

## CI commando

```bash
pytest tests/ -v --tb=short \
  --cov=api --cov=ollama --cov=webhooks \
  --cov-report=xml --cov-report=term-missing
```

## SQLite vs PostgreSQL gotcha's

| Issue | Oplossing |
|-------|----------|
| `Enum` kolommen | Gebruik `native_enum=False` of `String` in ORM voor SQLite-compat |
| `RETURNING` clause | Niet ondersteund in SQLite — gebruik `refresh()` na commit |
| `UUID` kolommen | SQLite slaat UUID op als string — gebruik `String(36)` of `Integer` PK |
| `NOW()` functies | SQLite gebruikt `CURRENT_TIMESTAMP` — gebruik Python `datetime.utcnow()` als default |

## Anti-patronen

| ❌ NIET | ✅ WEL |
|---------|-------|
| `@pytest.mark.asyncio` | asyncio_mode = "auto" — niet nodig |
| `loop = asyncio.get_event_loop()` | anyio managed loop via fixtures |
| `Session.query()` in tests | `select(Model).where(...)` |
| Echte PostgreSQL in CI | SQLite in-memory via aiosqlite |
| `scope="session"` voor db_session | `scope="function"` — anders shared state |
