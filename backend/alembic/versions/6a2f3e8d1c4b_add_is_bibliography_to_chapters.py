"""Add is_bibliography to chapters

Revision ID: 6a2f3e8d1c4b
Revises: e7f9a2b3c4d5
Create Date: 2026-02-23 22:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a2f3e8d1c4b'
down_revision = 'e7f9a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_bibliography column with default False
    op.add_column('chapters', sa.Column('is_bibliography', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    # Drop is_bibliography column
    op.drop_column('chapters', 'is_bibliography')
