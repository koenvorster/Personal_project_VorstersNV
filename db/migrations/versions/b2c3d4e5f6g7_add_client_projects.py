"""add client_projects table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-10 09:00:00.000000

Voegt de client_projects tabel toe voor het VorstersNV consultancy platform.
Elke rij vertegenwoordigt één analyseproject per klant-tenant.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_projects",

        # ── Primaire sleutel ─────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),

        # ── Externe UUID-referentie (vanuit Python ClientProjectSpace) ─
        sa.Column(
            "project_id",
            sa.String(length=36),
            nullable=False,
            unique=True,
        ),

        # ── Tenant / klant-velden ────────────────────────────────────
        sa.Column("klant_naam",  sa.String(length=200), nullable=False),
        sa.Column("klant_id",    sa.String(length=100), nullable=False),
        sa.Column("projecttype", sa.String(length=50),  nullable=False),

        # ── Bronpad (absoluut lokaal pad als tekst) ──────────────────
        sa.Column("bronpad", sa.Text(), nullable=False),

        # ── Lifecycle status ─────────────────────────────────────────
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="CREATED",
        ),

        # ── JSON configuratie (ProjectConfig serialisatie) ───────────
        sa.Column("config_json", sa.JSON(), nullable=True),

        # ── Rapport locatie (ingevuld na voltooiing) ─────────────────
        sa.Column("rapport_pad", sa.Text(), nullable=True),

        # ── Tijdstempels ─────────────────────────────────────────────
        sa.Column(
            "aangemaakt_op",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "bijgewerkt_op",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── Indexen ───────────────────────────────────────────────────────
    # Tenant-lookup: haal alle projecten op per klant
    op.create_index(
        "ix_client_projects_klant_id",
        "client_projects",
        ["klant_id"],
    )

    # Status-filter: zoek alle projecten in een bepaalde fase (bijv. SCANNING)
    op.create_index(
        "ix_client_projects_status",
        "client_projects",
        ["status"],
    )

    # Tijdlijn-query: sorteer en filter op aanmaakdatum
    op.create_index(
        "ix_client_projects_aangemaakt_op",
        "client_projects",
        ["aangemaakt_op"],
    )


def downgrade() -> None:
    op.drop_index("ix_client_projects_aangemaakt_op", table_name="client_projects")
    op.drop_index("ix_client_projects_status",        table_name="client_projects")
    op.drop_index("ix_client_projects_klant_id",      table_name="client_projects")
    op.drop_table("client_projects")
