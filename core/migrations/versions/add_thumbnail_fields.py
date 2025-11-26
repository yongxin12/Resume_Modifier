"""Add thumbnail fields to resume_files table

Revision ID: add_thumbnail_fields
Revises: 2e4e6feef93f
Create Date: 2025-11-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_thumbnail_fields'
down_revision = '2e4e6feef93f'  # Fixed: now correctly depends on previous migration
branch_labels = None
depends_on = None


def upgrade():
    """Add thumbnail-related fields to resume_files table"""
    # Add thumbnail fields
    op.add_column('resume_files', sa.Column('has_thumbnail', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('resume_files', sa.Column('thumbnail_path', sa.String(length=500), nullable=True))
    op.add_column('resume_files', sa.Column('thumbnail_status', sa.String(length=50), nullable=False, server_default='pending'))
    op.add_column('resume_files', sa.Column('thumbnail_generated_at', sa.DateTime(), nullable=True))
    op.add_column('resume_files', sa.Column('thumbnail_error', sa.Text(), nullable=True))


def downgrade():
    """Remove thumbnail fields from resume_files table"""
    op.drop_column('resume_files', 'thumbnail_error')
    op.drop_column('resume_files', 'thumbnail_generated_at')
    op.drop_column('resume_files', 'thumbnail_status')
    op.drop_column('resume_files', 'thumbnail_path')
    op.drop_column('resume_files', 'has_thumbnail')