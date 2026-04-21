"""add leads table

Revision ID: a1b2c3d4e5f6
Revises: ee41826e747a
Create Date: 2026-06-01 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ee41826e747a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("naam", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("bedrijf", sa.String(length=200), nullable=True),
        sa.Column("dienst", sa.String(length=100), nullable=True),
        sa.Column("bericht", sa.Text(), nullable=True),
        sa.Column(
            "aangemaakt_op",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("verwerkt", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("notificatie_verzonden", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_email", "leads", ["email"])
    op.create_index("ix_leads_aangemaakt_op", "leads", ["aangemaakt_op"])


def downgrade() -> None:
    op.drop_index("ix_leads_aangemaakt_op", table_name="leads")
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_table("leads")
