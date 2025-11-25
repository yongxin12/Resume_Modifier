"""Add Railway compatibility columns to resume_files

Revision ID: railway_compatibility
Revises: add_file_categorization
Create Date: 2025-11-23 00:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'railway_compatibility'
down_revision = 'add_file_categorization'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to match Railway database schema."""
    
    # Add display_filename column
    op.add_column('resume_files', 
        sa.Column('display_filename', sa.String(length=255), nullable=True)
    )
    
    # Add content analysis columns
    op.add_column('resume_files', 
        sa.Column('page_count', sa.Integer(), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('paragraph_count', sa.Integer(), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('language', sa.String(length=10), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('keywords', sa.JSON(), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('processing_time', sa.Float(), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('processing_metadata', sa.JSON(), nullable=True)
    )
    
    # Add thumbnail columns
    op.add_column('resume_files', 
        sa.Column('has_thumbnail', sa.Boolean(), nullable=False, server_default='false')
    )
    
    op.add_column('resume_files', 
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('thumbnail_status', sa.String(length=20), nullable=False, server_default='pending')
    )
    
    op.add_column('resume_files', 
        sa.Column('thumbnail_generated_at', sa.DateTime(), nullable=True)
    )
    
    op.add_column('resume_files', 
        sa.Column('thumbnail_error', sa.Text(), nullable=True)
    )
    
    # Add Google Drive link columns (if not already present)
    try:
        op.add_column('resume_files', 
            sa.Column('google_drive_link', sa.String(length=500), nullable=True)
        )
    except:
        pass  # Column might already exist
    
    try:
        op.add_column('resume_files', 
            sa.Column('google_doc_link', sa.String(length=500), nullable=True)
        )
    except:
        pass  # Column might already exist
    
    # Add check constraint for thumbnail_status
    op.create_check_constraint(
        'check_valid_thumbnail_status',
        'resume_files',
        "thumbnail_status IN ('pending', 'generating', 'completed', 'failed')"
    )


def downgrade():
    """Remove Railway compatibility columns."""
    
    # Drop check constraint
    op.drop_constraint('check_valid_thumbnail_status', 'resume_files', type_='check')
    
    # Drop columns
    op.drop_column('resume_files', 'thumbnail_error')
    op.drop_column('resume_files', 'thumbnail_generated_at')
    op.drop_column('resume_files', 'thumbnail_status')
    op.drop_column('resume_files', 'thumbnail_path')
    op.drop_column('resume_files', 'has_thumbnail')
    op.drop_column('resume_files', 'processing_metadata')
    op.drop_column('resume_files', 'processing_time')
    op.drop_column('resume_files', 'keywords')
    op.drop_column('resume_files', 'language')
    op.drop_column('resume_files', 'paragraph_count')
    op.drop_column('resume_files', 'page_count')
    op.drop_column('resume_files', 'display_filename')
    
    # Only drop Google Drive columns if they were added by this migration
    try:
        op.drop_column('resume_files', 'google_doc_link')
        op.drop_column('resume_files', 'google_drive_link')
    except:
        pass  # Columns might not have been added by this migration