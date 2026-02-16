"""Add GlobalReferences and update models for bibliography system

Revision ID: e7f9a2b3c4d5
Revises: ff34493e6a47
Create Date: 2026-02-15 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7f9a2b3c4d5'
down_revision = 'ff34493e6a47'
branch_labels = None
depends_on = None


def upgrade():
    # Create global_references table
    op.create_table(
        'global_references',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_key', sa.String(), nullable=False),
        sa.Column('reference_number', sa.Integer(), nullable=False),
        sa.Column('full_reference_abnt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id', 'reference_key', name='uq_book_reference_key'),
        sa.UniqueConstraint('book_id', 'reference_number', name='uq_book_reference_number')
    )
    
    # Create section_references association table
    op.create_table(
        'section_references',
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reference_id'], ['global_references.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('section_id', 'reference_id')
    )
    
    # Remove bibliography column from sections table
    op.drop_column('sections', 'bibliography')
    
    # Add source_type column to section_assets
    op.add_column('section_assets', sa.Column('source_type', sa.String(), nullable=False, server_default='SLIDE'))
    
    # Make timestamp nullable in section_assets
    op.alter_column('section_assets', 'timestamp',
                    existing_type=sa.Float(),
                    nullable=True)


def downgrade():
    # Revert timestamp to NOT NULL
    op.alter_column('section_assets', 'timestamp',
                    existing_type=sa.Float(),
                    nullable=False)
    
    # Remove source_type column
    op.drop_column('section_assets', 'source_type')
    
    # Re-add bibliography column to sections
    op.add_column('sections', sa.Column('bibliography', postgresql.JSONB(), nullable=True))
    
    # Drop association table
    op.drop_table('section_references')
    
    # Drop global_references table
    op.drop_table('global_references')
