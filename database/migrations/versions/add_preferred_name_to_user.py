"""add preferred_name to users

Revision ID: add_preferred_name
Revises: add_conversation_state
Create Date: 2025-01-22 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_preferred_name'
down_revision = 'add_conversation_state'
branch_labels = None
depends_on = None


def upgrade():
    # Add preferred_name column to users table
    op.add_column('users', sa.Column('preferred_name', sa.String(), nullable=True))


def downgrade():
    # Remove preferred_name column
    op.drop_column('users', 'preferred_name')

