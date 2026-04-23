"""add agent_versions table

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-06-11 09:00:00.000000

Voegt de agent_versions tabel toe voor het semantisch versionsysteem
van Ollama runtime agents (W8-01: agent_versioning.py).

Elke rij vertegenwoordigt één semantische versie van een agent YAML met:
  - SHA-256 digest voor integriteitscontrole
  - lifecycle-status (draft → shadow → canary → stable → deprecated → archived)
  - evaluatiescore en run-teller voor kwaliteitsbewaking
  - deployed_at tijdstempel voor auditlogs

Unieke constraint (agent_name, version) voorkomt dubbele versienummers
per agent.  Indexen op agent_name, lifecycle en created_at zorgen voor
snelle lookups bij routing en changelog-queries.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_versions",

        # ── Primaire sleutel (UUID, server-side gegenereerd) ──────────
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),

        # ── Agent-naam (bijv. "klantenservice_agent") ─────────────────
        sa.Column(
            "agent_name",
            sa.String(length=100),
            nullable=False,
        ),

        # ── SemVer-string (bijv. "2.1.3") ─────────────────────────────
        sa.Column(
            "version",
            sa.String(length=20),
            nullable=False,
        ),

        # ── SHA-256 hex-digest van de agent YAML-content (64 chars) ───
        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=False,
        ),

        # ── Lifecycle-fase (draft/shadow/canary/stable/deprecated/archived)
        sa.Column(
            "lifecycle",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),

        # ── Relatief pad naar de agent YAML ───────────────────────────
        sa.Column(
            "yaml_path",
            sa.Text(),
            nullable=False,
        ),

        # ── Evaluatiescore (0.0–1.0, rolling average, nullable) ───────
        sa.Column(
            "eval_score",
            sa.Float(),
            nullable=True,
        ),

        # ── Totaal aantal uitgevoerde runs ────────────────────────────
        sa.Column(
            "run_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        # ── Omschrijving van wijzigingen in deze versie ───────────────
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        # ── UTC-tijdstempel van deployement naar STABLE (nullable) ────
        sa.Column(
            "deployed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        # ── UTC-tijdstempel van aanmaak (auto-ingevuld door DB) ───────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        # ── Unieke constraint: één versienummer per agent ─────────────
        sa.UniqueConstraint(
            "agent_name",
            "version",
            name="uq_agent_versions_name_version",
        ),
    )

    # ── Indexen ───────────────────────────────────────────────────────────────

    # Snel alle versies van één agent opvragen (changelog, get_active_version)
    op.create_index(
        "ix_av_agent_name",
        "agent_versions",
        ["agent_name"],
    )

    # Snel alle versies in een bepaalde lifecycle-fase opvragen (dashboard, routing)
    op.create_index(
        "ix_av_lifecycle",
        "agent_versions",
        ["lifecycle"],
    )

    # Tijdlijn-queries en pagination (changelog nieuwste eerst)
    op.create_index(
        "ix_av_created_at",
        "agent_versions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_av_created_at", table_name="agent_versions")
    op.drop_index("ix_av_lifecycle",  table_name="agent_versions")
    op.drop_index("ix_av_agent_name", table_name="agent_versions")
    op.drop_table("agent_versions")
