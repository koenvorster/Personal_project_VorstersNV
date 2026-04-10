"""
VorstersNV Analytics Database – Ster-schema
Tweede PostgreSQL database voor rapportage en KPI-dashboards.

Architectuur (ster-model):
                    ┌─────────────┐
                    │  dim_date   │
                    └──────┬──────┘
                           │
┌──────────────┐   ┌───────┴──────┐   ┌──────────────┐
│ dim_product  ├───┤ sales_facts  ├───┤ dim_customer  │
└──────────────┘   └───────┬──────┘   └──────────────┘
                           │
                    ┌──────┴──────┐
                    │  dim_agent  │
                    └─────────────┘
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

ANALYTICS_DB_URL = os.environ.get(
    "ANALYTICS_DB_URL",
    "postgresql+asyncpg://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV_analytics",
)


class AnalyticsBase(DeclarativeBase):
    pass


analytics_engine = create_async_engine(ANALYTICS_DB_URL, echo=False)
AnalyticsSessionLocal = async_sessionmaker(
    analytics_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_analytics_db() -> AsyncSession:
    """FastAPI dependency – geeft een async analytics DB-sessie terug."""
    async with AnalyticsSessionLocal() as session:
        yield session
