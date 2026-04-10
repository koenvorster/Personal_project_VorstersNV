"""
VorstersNV SQLAlchemy modellen.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Enum,
    JSON, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ── Enums ────────────────────────────────────────────────────────────────────

class OrderStatus(str, PyEnum):
    pending = "pending"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    returned = "returned"
    cancelled = "cancelled"


class ToneOfVoice(str, PyEnum):
    professioneel = "professioneel"
    vriendelijk = "vriendelijk"
    luxe = "luxe"
    technisch = "technisch"


# ── Modellen ─────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    omschrijving: Mapped[str | None] = mapped_column(Text)
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    korte_beschrijving: Mapped[str | None] = mapped_column(String(500))
    beschrijving: Mapped[str | None] = mapped_column(Text)
    seo_titel: Mapped[str | None] = mapped_column(String(70))
    seo_omschrijving: Mapped[str | None] = mapped_column(String(160))
    prijs: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    voorraad: Mapped[int] = mapped_column(Integer, default=0)
    laag_voorraad_drempel: Mapped[int] = mapped_column(Integer, default=5)
    afbeelding_url: Mapped[str | None] = mapped_column(String(500))
    extra_afbeeldingen: Mapped[list | None] = mapped_column(JSON)
    kenmerken: Mapped[dict | None] = mapped_column(JSON)
    tags: Mapped[list | None] = mapped_column(JSON)
    actief: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    bijgewerkt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    category: Mapped["Category | None"] = relationship("Category", back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    telefoon: Mapped[str | None] = mapped_column(String(20))
    straat: Mapped[str | None] = mapped_column(String(200))
    postcode: Mapped[str | None] = mapped_column(String(10))
    stad: Mapped[str | None] = mapped_column(String(100))
    land: Mapped[str] = mapped_column(String(2), default="NL")
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_nummer: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.pending, nullable=False
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    totaal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    btw_bedrag: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    verzendkosten: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    betaalmethode: Mapped[str | None] = mapped_column(String(50))
    payment_id: Mapped[str | None] = mapped_column(String(100))
    tracking_code: Mapped[str | None] = mapped_column(String(100))
    notities: Mapped[str | None] = mapped_column(Text)
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    bijgewerkt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")
    invoice: Mapped["Invoice | None"] = relationship("Invoice", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    aantal: Mapped[int] = mapped_column(Integer, nullable=False)
    stukprijs: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotaal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    factuur_nummer: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    totaal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    btw_bedrag: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(500))
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    order: Mapped["Order"] = relationship("Order", back_populates="invoice")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_naam: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(50))
    user_input: Mapped[str] = mapped_column(Text)
    agent_output: Mapped[str] = mapped_column(Text)
    prompt_versie: Mapped[str] = mapped_column(String(10), default="1.0")
    rating: Mapped[int | None] = mapped_column(Integer)
    verwerkingstijd_ms: Mapped[int | None] = mapped_column(Integer)
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
