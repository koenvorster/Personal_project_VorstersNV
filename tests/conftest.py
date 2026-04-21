"""
Gedeelde pytest fixtures voor VorstersNV API tests.
Gebruikt een in-memory SQLite database zodat er geen PostgreSQL nodig is.
"""
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.auth.jwt import TokenData, require_admin
from api.main import app
from db.base import Base
from db.database import get_db
from db.models import Category, Product
from db.models.user import UserRole

SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def db_engine():
    """Maak een in-memory SQLite engine aan per test."""
    engine = create_async_engine(SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Geeft een AsyncSession gebonden aan de test-engine."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


def _fake_admin() -> TokenData:
    return TokenData(user_id="test-admin", email="admin@test.be", naam="Test Admin", rol=UserRole.admin)


@pytest.fixture(scope="function")
async def client(db_session):
    """
    HTTP-testclient met de get_db dependency overschreven naar de test-sessie.
    Anonieme client — geen auth bypass (voor publieke endpoints).
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def admin_client(db_session):
    """
    HTTP-testclient met admin-rol en database override.
    Gebruik voor endpoints die require_admin vereisen (PUT, DELETE, etc.).
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = _fake_admin
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


# ── Testdata helpers ──────────────────────────────────────────────────────────

async def maak_categorie(db: AsyncSession, naam: str = "Feminised", slug: str = "feminised") -> Category:
    cat = Category(naam=naam, slug=slug, omschrijving="Test categorie")
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def maak_product(
    db: AsyncSession,
    naam: str = "Test Zaadje",
    slug: str = "test-zaadje",
    prijs: Decimal = Decimal("12.50"),
    voorraad: int = 10,
    actief: bool = True,
    category_id: int | None = None,
) -> Product:
    p = Product(
        naam=naam,
        slug=slug,
        korte_beschrijving="Een testproduct",
        prijs=prijs,
        voorraad=voorraad,
        actief=actief,
        category_id=category_id,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p
