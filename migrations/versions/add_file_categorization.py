"""Add file categorization system

Revision ID: add_file_categorization
Revises: previous_migration
Create Date: 2025-11-16 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_file_categorization'
down_revision = '2e4e6feef93f'  # Points to the enhance_resume_files migration
branch_labels = None
depends_on = None


def upgrade():
    """Add file categorization columns to resume_files table."""
    
    # Add category column with default value
    op.add_column('resume_files', 
        sa.Column('category', sa.String(length=20), nullable=False, server_default='active')
    )
    
    # Add category tracking columns
    op.add_column('resume_files', 
        sa.Column('category_updated_at', sa.DateTime(), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('category_updated_by', sa.Integer(), nullable=True)
    )
    
    # Add foreign key constraint for category_updated_by
    op.create_foreign_key(
        'fk_resume_files_category_updated_by', 
        'resume_files', 
        'users', 
        ['category_updated_by'], 
        ['id']
    )
    
    # Add check constraint for valid categories
    op.create_check_constraint(
        'check_valid_category',
        'resume_files',
        "category IN ('active', 'archived', 'draft')"
    )
    
    # Add indexes for efficient category queries
    op.create_index(
        'idx_resume_files_category', 
        'resume_files', 
        ['user_id', 'category', 'is_active']
    )
    
    op.create_index(
        'idx_resume_files_category_updated', 
        'resume_files', 
        ['category_updated_at']
    )


def downgrade():
    """Remove file categorization columns from resume_files table."""
    
    # Drop indexes
    op.drop_index('idx_resume_files_category_updated', table_name='resume_files')
    op.drop_index('idx_resume_files_category', table_name='resume_files')
    
    # Drop check constraint
    op.drop_constraint('check_valid_category', 'resume_files', type_='check')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_resume_files_category_updated_by', 'resume_files', type_='foreignkey')
    
    # Drop columns
    op.drop_column('resume_files', 'category_updated_by')
    op.drop_column('resume_files', 'category_updated_at')
    op.drop_column('resume_files', 'category')