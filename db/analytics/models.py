"""
VorstersNV Analytics – Ster-schema modellen

Dimensietabellen (dim_*): beschrijvende attributen
Feitentabel (sales_facts): meetbare feiten met foreign keys naar dimensies
"""
from datetime import datetime, date, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Integer, Numeric, String, Text,
    ForeignKey, Index, SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import AnalyticsBase


def utcnow():
    return datetime.now(timezone.utc)


# ── Dimensietabellen ──────────────────────────────────────────────────────────

class DimDate(AnalyticsBase):
    """
    Datums dimensie – vooraf gevuld voor rapportageperiode.
    Sleutel: YYYYMMDD integer (bijv. 20250403)
    """
    __tablename__ = "dim_date"

    date_key: Mapped[int] = mapped_column(Integer, primary_key=True)  # YYYYMMDD
    datum: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    dag: Mapped[int] = mapped_column(SmallInteger)          # 1-31
    dag_naam: Mapped[str] = mapped_column(String(10))       # Maandag
    dag_van_week: Mapped[int] = mapped_column(SmallInteger) # 1=Ma, 7=Zo
    week: Mapped[int] = mapped_column(SmallInteger)         # ISO weeknummer
    maand: Mapped[int] = mapped_column(SmallInteger)        # 1-12
    maand_naam: Mapped[str] = mapped_column(String(10))     # Januari
    kwartaal: Mapped[int] = mapped_column(SmallInteger)     # 1-4
    jaar: Mapped[int] = mapped_column(Integer)
    is_weekend: Mapped[bool] = mapped_column(Boolean, default=False)
    is_feestdag: Mapped[bool] = mapped_column(Boolean, default=False)

    sales: Mapped[list["SalesFact"]] = relationship("SalesFact", back_populates="datum")

    __table_args__ = (
        Index("ix_dim_date_datum", "datum"),
        Index("ix_dim_date_jaar_maand", "jaar", "maand"),
    )


class DimProduct(AnalyticsBase):
    """Product dimensie – snapshot van productgegevens ten tijde van verkoop."""
    __tablename__ = "dim_product"

    product_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)  # FK naar webshop DB
    naam: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220))
    categorie: Mapped[str | None] = mapped_column(String(100))
    prijs: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_actief: Mapped[bool] = mapped_column(Boolean, default=True)
    geldig_vanaf: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    geldig_tot: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # SCD Type 2

    sales: Mapped[list["SalesFact"]] = relationship("SalesFact", back_populates="product")

    __table_args__ = (Index("ix_dim_product_product_id", "product_id"),)


class DimCustomer(AnalyticsBase):
    """Klantendimensie – segment en geografische gegevens."""
    __tablename__ = "dim_customer"

    customer_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    naam: Mapped[str] = mapped_column(String(200))
    stad: Mapped[str | None] = mapped_column(String(100))
    land: Mapped[str] = mapped_column(String(2), default="NL")
    segment: Mapped[str] = mapped_column(String(50), default="particulier")  # particulier / zakelijk / vip
    eerste_aankoop: Mapped[date | None] = mapped_column(Date)
    totaal_orders: Mapped[int] = mapped_column(Integer, default=0)
    totaal_besteed: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    geldig_vanaf: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sales: Mapped[list["SalesFact"]] = relationship("SalesFact", back_populates="customer")

    __table_args__ = (Index("ix_dim_customer_customer_id", "customer_id"),)


class DimAgent(AnalyticsBase):
    """AI-agent dimensie – welke agent + prompt-versie werd gebruikt."""
    __tablename__ = "dim_agent"

    agent_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_naam: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(50))
    prompt_versie: Mapped[str] = mapped_column(String(10), default="1.0")
    omschrijving: Mapped[str | None] = mapped_column(Text)
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sales: Mapped[list["SalesFact"]] = relationship("SalesFact", back_populates="agent")
    agent_facts: Mapped[list["AgentPerformanceFact"]] = relationship(
        "AgentPerformanceFact", back_populates="agent"
    )


# ── Feitentabellen ────────────────────────────────────────────────────────────

class SalesFact(AnalyticsBase):
    """
    Centrale verkoop-feitentabel.
    Granulariteit: één rij per orderregel (order + product combinatie).
    """
    __tablename__ = "sales_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Dimensie-sleutels
    date_key: Mapped[int] = mapped_column(ForeignKey("dim_date.date_key"), nullable=False)
    product_key: Mapped[int] = mapped_column(ForeignKey("dim_product.product_key"), nullable=False)
    customer_key: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_key"), nullable=False)
    agent_key: Mapped[int | None] = mapped_column(ForeignKey("dim_agent.agent_key"))

    # Degenerate dimensies (geen aparte tabel nodig)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False)
    order_nummer: Mapped[str] = mapped_column(String(20))
    betaalmethode: Mapped[str | None] = mapped_column(String(50))
    order_status: Mapped[str] = mapped_column(String(30))

    # Meetwaarden (feiten)
    aantal: Mapped[int] = mapped_column(Integer, nullable=False)
    stukprijs: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotaal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    btw_bedrag: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    korting: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    netto_omzet: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_retour: Mapped[bool] = mapped_column(Boolean, default=False)
    verwerkingstijd_minuten: Mapped[int | None] = mapped_column(Integer)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relaties
    datum: Mapped["DimDate"] = relationship("DimDate", back_populates="sales")
    product: Mapped["DimProduct"] = relationship("DimProduct", back_populates="sales")
    customer: Mapped["DimCustomer"] = relationship("DimCustomer", back_populates="sales")
    agent: Mapped["DimAgent | None"] = relationship("DimAgent", back_populates="sales")

    __table_args__ = (
        Index("ix_sales_facts_date_key", "date_key"),
        Index("ix_sales_facts_product_key", "product_key"),
        Index("ix_sales_facts_customer_key", "customer_key"),
        Index("ix_sales_facts_order_id", "order_id"),
        Index("ix_sales_facts_order_status", "order_status"),
    )


class AgentPerformanceFact(AnalyticsBase):
    """
    Agent-prestatie feitentabel.
    Granulariteit: één rij per agent-interactie.
    """
    __tablename__ = "agent_performance_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_key: Mapped[int] = mapped_column(ForeignKey("dim_date.date_key"), nullable=False)
    agent_key: Mapped[int] = mapped_column(ForeignKey("dim_agent.agent_key"), nullable=False)

    # Meetwaarden
    rating: Mapped[int | None] = mapped_column(SmallInteger)       # 1-5
    verwerkingstijd_ms: Mapped[int | None] = mapped_column(Integer)
    tokens_gebruikt: Mapped[int | None] = mapped_column(Integer)
    escalatie: Mapped[bool] = mapped_column(Boolean, default=False)
    succesvol: Mapped[bool] = mapped_column(Boolean, default=True)

    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    agent: Mapped["DimAgent"] = relationship("DimAgent", back_populates="agent_facts")

    __table_args__ = (
        Index("ix_agent_perf_date_key", "date_key"),
        Index("ix_agent_perf_agent_key", "agent_key"),
    )
