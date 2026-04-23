"""
VorstersNV SQLAlchemy modellen.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Enum,
    Index, JSON, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


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


class ClientProject(Base):
    """
    Persistente opslag van een consultancy analyseproject.

    Spiegelt ClientProjectSpace (ollama/client_project_space.py) naar de database.
    project_id is de externe UUID-referentie die in Python als primaire sleutel
    van de in-memory registry fungeert. klant_id garandeert tenant-isolatie.
    """
    __tablename__ = "client_projects"

    # ── Primaire sleutel ─────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Externe UUID-referentie (Python ClientProjectSpace.project_id) ───────
    project_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
    )

    # ── Tenant / klant-velden ─────────────────────────────────────────────────
    klant_naam:  Mapped[str] = mapped_column(String(200), nullable=False)
    klant_id:    Mapped[str] = mapped_column(String(100), nullable=False)
    projecttype: Mapped[str] = mapped_column(String(50),  nullable=False)

    # ── Bronpad (absoluut lokaal pad als tekst) ───────────────────────────────
    bronpad: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Lifecycle status ──────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="CREATED",
        default="CREATED",
    )

    # ── JSON configuratie (ProjectConfig serialisatie) ────────────────────────
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Rapport locatie (ingevuld na voltooiing) ──────────────────────────────
    rapport_pad: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Tijdstempels ──────────────────────────────────────────────────────────
    aangemaakt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )
    bijgewerkt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    # ── Tabel-level indexen ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_client_projects_klant_id",     "klant_id"),
        Index("ix_client_projects_status",        "status"),
        Index("ix_client_projects_aangemaakt_op", "aangemaakt_op"),
    )


class VectorDocumentModel(Base):
    """
    Persistente opslag van een geïndexeerd code-fragment (RAG pipeline, W7-01).

    Spiegelt VectorDocument (ollama/rag_engine.py) naar de database.
    De embedding vector wordt als JSON-array opgeslagen in embedding_json;
    Wave 8+ kan dit vervangen door een pgvector VECTOR-kolom.

    Tenant-isolatie: project_id FK naar client_projects.project_id (CASCADE DELETE).
    """
    __tablename__ = "vector_documents"

    # ── Primaire sleutel ──────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Unieke documentreferentie (VectorDocument.doc_id — UUID-string) ───────
    doc_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
    )

    # ── Tenant-sleutel (FK naar ClientProject.project_id) ────────────────────
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("client_projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Referentie naar CodeChunk.chunk_id (adaptive_chunker) ────────────────
    chunk_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # ── Bronbestand (relatief of absoluut pad) ────────────────────────────────
    bestand: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Codetekst van het fragment ────────────────────────────────────────────
    inhoud: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Embedding vector opgeslagen als JSON-array van floats ─────────────────
    # Formaat: [0.123, -0.456, ...]  (384 elementen voor all-MiniLM-L6-v2)
    embedding_json: Mapped[list] = mapped_column(JSON, nullable=False)

    # ── Extra metadata (taal, lijn_start, lijn_eind, token_schatting, ...) ────
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Aanmaaktijdstip ───────────────────────────────────────────────────────
    aangemaakt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    # ── Relatie naar ClientProject ────────────────────────────────────────────
    project: Mapped["ClientProject"] = relationship(
        "ClientProject",
        foreign_keys=[project_id],
        primaryjoin="VectorDocumentModel.project_id == ClientProject.project_id",
    )

    # ── Tabel-level indexen ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_vd_project_id", "project_id"),
        Index("ix_vd_chunk_id",   "chunk_id"),
    )


class AgentVersionModel(Base):
    """
    Persistente opslag van één semantische agent-versie (W8-01).

    Spiegelt AgentVersion (ollama/agent_versioning.py) naar de database.
    Bewaart SHA-256 integriteitscheck, lifecycle-fase, evaluatiescore en
    run-teller voor kwaliteitsbewaking en auditlogs.

    Unieke constraint (agent_name, version) voorkomt dubbele versienummers
    per agent.
    """
    __tablename__ = "agent_versions"

    # ── Primaire sleutel (UUID, server-side gegenereerd) ──────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # ── Agent-naam (bijv. "klantenservice_agent") ─────────────────────────────
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── SemVer-string (bijv. "2.1.3") ─────────────────────────────────────────
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── SHA-256 hex-digest van de agent YAML-content (64 chars) ───────────────
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # ── Lifecycle-fase ────────────────────────────────────────────────────────
    lifecycle: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="draft",
    )

    # ── Relatief pad naar de agent YAML ──────────────────────────────────────
    yaml_path: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Evaluatiescore (0.0–1.0, rolling average) ─────────────────────────────
    eval_score: Mapped[float | None] = mapped_column(nullable=True)

    # ── Totaal aantal uitgevoerde runs ────────────────────────────────────────
    run_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    # ── Omschrijving van wijzigingen in deze versie ───────────────────────────
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── UTC-tijdstempel van deployement naar STABLE ───────────────────────────
    deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── UTC-tijdstempel van aanmaak (auto-ingevuld door DB) ───────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Tabel-level constraints en indexen ───────────────────────────────────
    __table_args__ = (
        UniqueConstraint("agent_name", "version", name="uq_agent_versions_name_version"),
        Index("ix_av_agent_name", "agent_name"),
        Index("ix_av_lifecycle",  "lifecycle"),
        Index("ix_av_created_at", "created_at"),
    )


class FeedbackRecordModel(Base):
    """
    Persistente opslag van één feedbackbeoordeling (Wave 8+).

    Elke rij bevat de sterrenratings van een klant of consultant voor één
    AI-agent run, geïsoleerd per project via de FK naar client_projects.

    ratings_json formaat: {"kwaliteit": 4, "duidelijkheid": 3, ...}
    gemiddelde_score is voorberekend bij opslaan voor snelle aggregatie.
    """
    __tablename__ = "feedback_records"

    # ── Primaire sleutel (UUID, gegenereerd door PostgreSQL) ──────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # ── Tenant-sleutel (FK naar ClientProject.project_id, CASCADE DELETE) ─
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("client_projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Agent-informatie ──────────────────────────────────────────────────
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Ratings als JSON-object { "kwaliteit": 4, "duidelijkheid": 3, … } ─
    ratings_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # ── Voorberekend gemiddelde van alle sectiescores ─────────────────────
    gemiddelde_score: Mapped[float] = mapped_column(nullable=False)

    # ── Vrije tekst opmerking (optioneel) ─────────────────────────────────
    opmerking: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Wie heeft beoordeeld: "klant" | "consultant" | "auto" ────────────
    beoordelaar: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Optionele referentie naar een trace/run-id ────────────────────────
    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # ── Aanmaaktijdstip met tijdzone (auto-ingevuld door DB) ──────────────
    aangemaakt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relatie naar ClientProject ────────────────────────────────────────
    project: Mapped["ClientProject"] = relationship(
        "ClientProject",
        foreign_keys=[project_id],
        primaryjoin="FeedbackRecordModel.project_id == ClientProject.project_id",
    )

    # ── Tabel-level indexen ───────────────────────────────────────────────
    __table_args__ = (
        Index("ix_fr_project_id",   "project_id"),
        Index("ix_fr_agent_name",   "agent_name"),
        Index("ix_fr_aangemaakt_op","aangemaakt_op"),
    )


class ReasoningLogModel(Base):
    """
    Persistente opslag van LLM reasoning/chain-of-thought logs (Wave 9+).

    Elke rij bevat de geëxtraheerde reasoning-tekst van één agent-run,
    met token-tellingen en het aantal chain-of-thought stappen.
    Gebruikt voor analyse van redeneerpatronen en kwaliteitsmonitoring.
    """
    __tablename__ = "agent_reasoning_logs"

    # ── Primaire sleutel (UUID-string, gegenereerd door Python) ──────────
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Naam van de agent die de reasoning genereerde ────────────────────
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Optionele koppeling naar een ClientProject (SET NULL bij verwijder)
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("client_projects.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Optioneel sessie-ID voor multi-turn correlatie ───────────────────
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # ── De geëxtraheerde reasoning-tekst ────────────────────────────────
    reasoning_text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Token-schattingen (input / reasoning / output) ───────────────────
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # ── Model dat de reasoning genereerde ───────────────────────────────
    model_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Aantal geïdentificeerde chain-of-thought stappen ─────────────────
    chain_of_thought_steps: Mapped[int] = mapped_column(Integer, default=0)

    # ── UTC-tijdstempel van aanmaak (auto-ingevuld door DB) ──────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Tabel-level indexen ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_rl_agent_name", "agent_name"),
        Index("ix_rl_project_id", "project_id"),
        Index("ix_rl_created_at", "created_at"),
    )
