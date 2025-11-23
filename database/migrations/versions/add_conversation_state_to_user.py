"""Add conversation_state and conversation_context to User model

Revision ID: add_conversation_state
Revises: 540a08dbe64b
Create Date: 2025-01-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_conversation_state'
down_revision = '540a08dbe64b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add conversation_state column
    op.add_column('users', sa.Column('conversation_state', sa.String(), nullable=True, server_default='idle'))
    
    # Add conversation_context column (JSON)
    op.add_column('users', sa.Column('conversation_context', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('users', 'conversation_context')
    op.drop_column('users', 'conversation_state')

