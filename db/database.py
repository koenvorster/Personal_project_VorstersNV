"""
VorstersNV Database configuratie.
Async SQLAlchemy engine + sessie factory.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.base import Base  # noqa: F401 – re-export voor backward compat

DATABASE_URL = os.environ.get(
    "DB_URL",
    "postgresql+asyncpg://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV",
)


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency – geeft een async DB-sessie terug."""
    async with AsyncSessionLocal() as session:
        yield session
