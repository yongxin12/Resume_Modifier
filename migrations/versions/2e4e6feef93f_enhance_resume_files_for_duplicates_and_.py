"""enhance_resume_files_for_duplicates_and_google_drive

Revision ID: 2e4e6feef93f
Revises: 0edbd362e651
Create Date: 2025-11-14 16:32:52.208081

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e4e6feef93f'
down_revision = '0edbd362e651'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the unique constraint on file_hash to allow duplicates
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_constraint('resume_files_file_hash_key', type_='unique')
    
    # Add Google Drive integration fields
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('google_drive_file_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('google_doc_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('google_drive_link', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('google_doc_link', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('is_shared_with_user', sa.Boolean(), nullable=True, default=False))
    
    # Add duplicate handling fields
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_duplicate', sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column('duplicate_sequence', sa.Integer(), nullable=True, default=0))
        batch_op.add_column(sa.Column('original_file_id', sa.Integer(), nullable=True))
    
    # Add soft deletion fields  
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('deleted_by', sa.Integer(), nullable=True))
    
    # Add foreign key constraints
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_resume_files_original_file', 'resume_files', ['original_file_id'], ['id'])
        batch_op.create_foreign_key('fk_resume_files_deleted_by', 'users', ['deleted_by'], ['id'])
    
    # Add new indexes for better performance
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.create_index('idx_file_hash', ['file_hash'], unique=False)
        batch_op.create_index('idx_user_hash', ['user_id', 'file_hash'], unique=False)
        batch_op.create_index('idx_google_drive_file', ['google_drive_file_id'], unique=False)
        batch_op.create_index('idx_google_doc', ['google_doc_id'], unique=False)
        batch_op.create_index('idx_duplicates', ['original_file_id', 'duplicate_sequence'], unique=False)
        batch_op.create_index('idx_deleted_files', ['is_active', 'deleted_at'], unique=False)
    
    # Add check constraints
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.create_check_constraint('check_positive_duplicate_sequence', 'duplicate_sequence >= 0')


def downgrade():
    # Remove indexes
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_index('idx_deleted_files')
        batch_op.drop_index('idx_duplicates')
        batch_op.drop_index('idx_google_doc')
        batch_op.drop_index('idx_google_drive_file')
        batch_op.drop_index('idx_user_hash')
        batch_op.drop_index('idx_file_hash')
    
    # Remove check constraints
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_constraint('check_positive_duplicate_sequence', type_='check')
    
    # Remove foreign key constraints
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_constraint('fk_resume_files_deleted_by', type_='foreignkey')
        batch_op.drop_constraint('fk_resume_files_original_file', type_='foreignkey')
    
    # Remove soft deletion fields
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')
    
    # Remove duplicate handling fields
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_column('original_file_id')
        batch_op.drop_column('duplicate_sequence')
        batch_op.drop_column('is_duplicate')
    
    # Remove Google Drive integration fields
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.drop_column('is_shared_with_user')
        batch_op.drop_column('google_doc_link')
        batch_op.drop_column('google_drive_link')
        batch_op.drop_column('google_doc_id')
        batch_op.drop_column('google_drive_file_id')
    
    # Re-add the unique constraint on file_hash
    with op.batch_alter_table('resume_files', schema=None) as batch_op:
        batch_op.create_unique_constraint('resume_files_file_hash_key', ['file_hash'])
