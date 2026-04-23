"""add agent reasoning logs

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-04-23

"""
from alembic import op
import sqlalchemy as sa

revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_reasoning_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('client_projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('reasoning_text', sa.Text, nullable=False),
        sa.Column('input_tokens', sa.Integer, default=0),
        sa.Column('reasoning_tokens', sa.Integer, default=0),
        sa.Column('output_tokens', sa.Integer, default=0),
        sa.Column('model_name', sa.String(50), nullable=True),
        sa.Column('chain_of_thought_steps', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_reasoning_logs_agent_name', 'agent_reasoning_logs', ['agent_name'])
    op.create_index('ix_reasoning_logs_project_id', 'agent_reasoning_logs', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_reasoning_logs_project_id', 'agent_reasoning_logs')
    op.drop_index('ix_reasoning_logs_agent_name', 'agent_reasoning_logs')
    op.drop_table('agent_reasoning_logs')
