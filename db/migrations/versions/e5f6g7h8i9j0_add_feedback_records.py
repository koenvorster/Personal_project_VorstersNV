"""add feedback_records table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-06-17 10:00:00.000000

Voegt de feedback_records tabel toe voor het Wave 8 feedbacksysteem.
Elke rij bevat één beoordeling van een AI-agent door een klant of consultant,
geïsoleerd per project via de foreign key naar client_projects.project_id.

Kolommen:
    id              – UUID primary key (gen_random_uuid())
    project_id      – FK naar client_projects.project_id (CASCADE DELETE)
    agent_name      – naam van de beoordeelde AI-agent
    prompt_version  – versie van de prompt die beoordeeld wordt
    ratings_json    – JSON dict met sectie→score mapping (1-5 per sectie)
    gemiddelde_score– voorberekend gemiddelde over alle secties
    opmerking       – optionele vrije tekst van de beoordelaar
    beoordelaar     – "klant" | "consultant" | "auto"
    trace_id        – optionele referentie naar een trace/run-id
    aangemaakt_op   – tijdstempel met tijdzone (auto-ingevuld)

Indexen: ix_fr_project_id, ix_fr_agent_name, ix_fr_aangemaakt_op
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6g7h8i9j0"
down_revision: Union[str, None] = "d4e5f6g7h8i9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback_records",

        # ── Primaire sleutel (UUID, gegenereerd door PostgreSQL) ───────────
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),

        # ── Tenant-sleutel (FK naar client_projects.project_id) ───────────
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey(
                "client_projects.project_id",
                name="fk_fr_project_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        # ── Agent-informatie ──────────────────────────────────────────────
        sa.Column(
            "agent_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "prompt_version",
            sa.String(length=20),
            nullable=False,
        ),

        # ── Ratings als JSON-object { "kwaliteit": 4, "duidelijkheid": 3, … }
        sa.Column(
            "ratings_json",
            sa.JSON(),
            nullable=False,
        ),

        # ── Voorberekend gemiddelde van alle sectiescores ─────────────────
        sa.Column(
            "gemiddelde_score",
            sa.Float(),
            nullable=False,
        ),

        # ── Vrije tekst opmerking (optioneel) ─────────────────────────────
        sa.Column(
            "opmerking",
            sa.Text(),
            nullable=True,
        ),

        # ── Wie heeft beoordeeld: "klant" | "consultant" | "auto" ─────────
        sa.Column(
            "beoordelaar",
            sa.String(length=20),
            nullable=False,
        ),

        # ── Optionele referentie naar een trace/run-id ────────────────────
        sa.Column(
            "trace_id",
            sa.String(length=36),
            nullable=True,
        ),

        # ── Aanmaaktijdstip met tijdzone (auto-ingevuld door DB) ──────────
        sa.Column(
            "aangemaakt_op",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── Indexen ───────────────────────────────────────────────────────────────

    # Meest gebruikte query: alle beoordelingen voor één project ophalen
    op.create_index(
        "ix_fr_project_id",
        "feedback_records",
        ["project_id"],
    )

    # Vergelijken welke agent het beste scoort binnen een project
    op.create_index(
        "ix_fr_agent_name",
        "feedback_records",
        ["agent_name"],
    )

    # Tijdlijn-queries: feedback per periode filteren
    op.create_index(
        "ix_fr_aangemaakt_op",
        "feedback_records",
        ["aangemaakt_op"],
    )


def downgrade() -> None:
    op.drop_index("ix_fr_aangemaakt_op", table_name="feedback_records")
    op.drop_index("ix_fr_agent_name",    table_name="feedback_records")
    op.drop_index("ix_fr_project_id",    table_name="feedback_records")
    op.drop_table("feedback_records")
