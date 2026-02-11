"""add processing progress and status fields

Revision ID: b3f8e2a1d4c5
Revises: adf64c4b102c
Create Date: 2026-02-11 12:38:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3f8e2a1d4c5'
down_revision = 'adf64c4b102c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add processing_progress and current_step columns to books table
    op.add_column('books', sa.Column('processing_progress', sa.Integer(), server_default='0', nullable=False))
    op.add_column('books', sa.Column('current_step', sa.String(length=50), nullable=True))
    
    # Create indexes for better query performance
    op.create_index('idx_books_status', 'books', ['status'])
    op.create_index('idx_sections_status', 'sections', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_sections_status', table_name='sections')
    op.drop_index('idx_books_status', table_name='books')
    
    # Drop columns
    op.drop_column('books', 'current_step')
    op.drop_column('books', 'processing_progress')
