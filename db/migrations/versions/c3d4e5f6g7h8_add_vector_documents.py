"""add vector_documents table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-06-10 10:00:00.000000

Voegt de vector_documents tabel toe voor de RAG-pipeline (W7-01).
Elke rij bevat één geïndexeerd code-fragment (CodeChunk) als JSON-embedding
en is geïsoleerd per project via de foreign key naar client_projects.

Embedding opslag:
    De embedding vector (384 floats) wordt opgeslagen als JSON-array in
    embedding_json.  Wave 8+ kan dit vervangen door een pgvector VECTOR-kolom
    voor efficiëntere ANN-zoekopdrachten zodra pgvector beschikbaar is.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vector_documents",

        # ── Primaire sleutel ─────────────────────────────────────────
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),

        # ── Unieke documentreferentie (Python VectorDocument.doc_id) ──
        sa.Column(
            "doc_id",
            sa.String(length=36),
            nullable=False,
            unique=True,
        ),

        # ── Tenant-sleutel (FK naar client_projects.project_id) ───────
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey(
                "client_projects.project_id",
                name="fk_vd_project_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        # ── Referentie naar AdaptiveChunker.CodeChunk.chunk_id ────────
        sa.Column(
            "chunk_id",
            sa.String(length=36),
            nullable=False,
        ),

        # ── Bronbestand ───────────────────────────────────────────────
        sa.Column(
            "bestand",
            sa.Text(),
            nullable=False,
        ),

        # ── Codetekst van het fragment ────────────────────────────────
        sa.Column(
            "inhoud",
            sa.Text(),
            nullable=False,
        ),

        # ── Embedding vector als JSON-array van floats ────────────────
        # Formaat: [0.123, -0.456, ...]  (384 elementen, all-MiniLM-L6-v2)
        sa.Column(
            "embedding_json",
            sa.JSON(),
            nullable=False,
        ),

        # ── Extra metadata (taal, lijn_start, lijn_eind, ...) ────────
        sa.Column(
            "metadata_json",
            sa.JSON(),
            nullable=True,
        ),

        # ── Aanmaaktijdstip (auto-ingevuld door DB) ───────────────────
        sa.Column(
            "aangemaakt_op",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── Indexen ───────────────────────────────────────────────────────────────

    # Tenant-lookup: alle documenten per project opvragen
    op.create_index(
        "ix_vd_project_id",
        "vector_documents",
        ["project_id"],
    )

    # Chunk-lookup: document terugvinden via CodeChunk referentie
    op.create_index(
        "ix_vd_chunk_id",
        "vector_documents",
        ["chunk_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_vd_chunk_id",   table_name="vector_documents")
    op.drop_index("ix_vd_project_id", table_name="vector_documents")
    op.drop_table("vector_documents")
