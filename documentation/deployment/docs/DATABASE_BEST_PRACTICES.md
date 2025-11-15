# 🗄️ Database Management Best Practices

**Project:** Resume Modifier  
**Last Updated:** October 24, 2025  
**Status:** Comprehensive Guide for Development & Production

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Development Workflow](#development-workflow)
3. [Migration Management](#migration-management)
4. [Local Development with Existing Data](#local-development-with-existing-data)
5. [Production Deployment](#production-deployment)
6. [Data Safety & Backup](#data-safety--backup)
7. [Common Scenarios](#common-scenarios)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Core Principles

1. **🔄 Always Use Migrations** - Never modify database schema manually
2. **🧪 Test in Development First** - Always test migrations locally before production
3. **💾 Backup Before Changes** - Always backup production data before migrations
4. **📝 Version Control Everything** - Commit migration files to git
5. **🔒 Never Delete Migrations** - Migrations are immutable once applied

### Your Current Setup

```
Development:  PostgreSQL in Docker (localhost:5432)
Production:   Railway PostgreSQL (managed)
ORM:          SQLAlchemy with Flask-SQLAlchemy
Migrations:   Alembic via Flask-Migrate
Models:       app/models/temp.py (primary models file)
```

---

## Development Workflow

### Initial Setup (New Developer)

```bash
# 1. Clone repository
git clone https://github.com/Andrlulu/Resume_Modifier.git
cd Resume_Modifier

# 2. Setup environment
cp .env.example .env
# Edit .env with your local configuration

# 3. Start database
docker-compose up -d db

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run migrations (creates tables)
flask db upgrade

# 7. Verify database structure
python3 verify_database_schema.py

# 8. Start application
docker-compose up --build
```

### Daily Development Flow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Check for new migrations
flask db current  # See current version
ls migrations/versions/  # See all migrations

# 3. Apply any new migrations
flask db upgrade

# 4. Start development
docker-compose up
```

---

## Migration Management

### Creating Migrations (The Right Way)

#### Step 1: Modify Your Models

Edit `app/models/temp.py`:

```python
class User(db.Model):
    __tablename__ = 'users'
    
    # Existing fields
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # NEW: Add a field
    phone = db.Column(db.String(20))  # New field
```

#### Step 2: Generate Migration

```bash
# Auto-generate migration from model changes
flask db migrate -m "add phone field to users"

# This creates: migrations/versions/xxxx_add_phone_field_to_users.py
```

#### Step 3: Review Generated Migration

**CRITICAL**: Always review the generated migration file!

```python
# migrations/versions/xxxx_add_phone_field_to_users.py

def upgrade():
    # Check this code - does it match your intent?
    op.add_column('users', 
        sa.Column('phone', sa.String(20), nullable=True)
    )

def downgrade():
    # Ensure rollback is possible
    op.drop_column('users', 'phone')
```

#### Step 4: Test Migration Locally

```bash
# Apply migration
flask db upgrade

# Verify it worked
python3 verify_database_schema.py

# Test application functionality
pytest app/tests/ -v

# If there are issues, rollback
flask db downgrade  # Goes back one migration
```

#### Step 5: Commit to Version Control

```bash
git add migrations/versions/xxxx_add_phone_field_to_users.py
git add app/models/temp.py
git commit -m "feat: add phone field to User model"
git push origin feature/add-phone-field
```

### Migration Best Practices

#### ✅ DO:

```python
# 1. Use descriptive migration messages
flask db migrate -m "add email verification fields to users"

# 2. Make migrations reversible
def downgrade():
    op.drop_column('users', 'email_verified')

# 3. Add default values for NOT NULL columns
op.add_column('users', 
    sa.Column('status', sa.String(20), 
              nullable=False, 
              server_default='active')  # ✅ Has default
)

# 4. Handle data transformations
def upgrade():
    # Add column as nullable first
    op.add_column('users', sa.Column('full_name', sa.String(100)))
    
    # Populate with existing data
    op.execute("""
        UPDATE users 
        SET full_name = CONCAT(first_name, ' ', last_name)
        WHERE first_name IS NOT NULL OR last_name IS NOT NULL
    """)
    
    # Then make it not null if needed
    op.alter_column('users', 'full_name', nullable=False)

# 5. Use batch operations for SQLite compatibility
def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(20)))
        batch_op.create_index('idx_phone', ['phone'])
```

#### ❌ DON'T:

```python
# 1. Don't add NOT NULL without defaults to existing tables
op.add_column('users', 
    sa.Column('required_field', sa.String(50), nullable=False)
)  # ❌ Will fail if table has data!

# 2. Don't drop columns without downgrade
def downgrade():
    pass  # ❌ Can't rollback!

# 3. Don't use db.create_all() in production
with app.app_context():
    db.create_all()  # ❌ Bypasses migration system!

# 4. Don't modify existing migrations
# If migration is already pushed, create NEW migration to fix it

# 5. Don't use raw SQL without op.execute()
# Use: op.execute("SQL HERE")
# Not: conn.execute("SQL HERE")
```

---

## Local Development with Existing Data

### Scenario 1: Adding a Nullable Column

**Safe - No data loss risk**

```python
# Model change
class Resume(db.Model):
    # Existing fields...
    last_modified_by = db.Column(db.Integer)  # New nullable field
```

```bash
# 1. Generate migration
flask db migrate -m "add last_modified_by to resumes"

# 2. Apply migration
flask db upgrade

# Your existing data remains intact!
```

### Scenario 2: Adding a Required (NOT NULL) Column

**Risky - Needs careful handling**

```python
# Step 1: Add as nullable first
class Resume(db.Model):
    status = db.Column(db.String(20))  # Nullable initially
```

```bash
flask db migrate -m "add status to resumes (nullable)"
flask db upgrade
```

```python
# Step 2: Populate existing records
def upgrade():
    # After adding column as nullable
    op.execute("""
        UPDATE resumes 
        SET status = 'active' 
        WHERE status IS NULL
    """)
    
    # Now make it NOT NULL
    op.alter_column('resumes', 'status', nullable=False)
```

### Scenario 3: Renaming a Column

**Complex - Requires data migration**

```python
# Bad way (loses data):
def upgrade():
    op.drop_column('users', 'name')
    op.add_column('users', sa.Column('full_name', sa.String(100)))

# Good way (preserves data):
def upgrade():
    # 1. Add new column
    op.add_column('users', sa.Column('full_name', sa.String(100)))
    
    # 2. Copy data
    op.execute("""
        UPDATE users 
        SET full_name = name
    """)
    
    # 3. Drop old column
    op.drop_column('users', 'name')

def downgrade():
    op.add_column('users', sa.Column('name', sa.String(100)))
    op.execute("UPDATE users SET name = full_name")
    op.drop_column('users', 'full_name')
```

### Scenario 4: Changing Foreign Key Relationships

**Complex - Test thoroughly**

```python
# Original: Resume has template (integer)
class Resume(db.Model):
    template = db.Column(db.Integer)  # Old: just a number

# New: Resume references ResumeTemplate table
class Resume(db.Model):
    template_id = db.Column(db.Integer, db.ForeignKey('resume_templates.id'))
```

**Migration approach:**

```python
def upgrade():
    # 1. Add new column
    op.add_column('resumes', 
        sa.Column('template_id', sa.Integer(), nullable=True))
    
    # 2. Create foreign key
    op.create_foreign_key(
        'fk_resumes_template_id',
        'resumes', 'resume_templates',
        ['template_id'], ['id']
    )
    
    # 3. Migrate data (map old template numbers to new IDs)
    op.execute("""
        UPDATE resumes r
        SET template_id = rt.id
        FROM resume_templates rt
        WHERE r.template = rt.legacy_template_number
    """)
    
    # 4. Drop old column
    op.drop_column('resumes', 'template')

def downgrade():
    op.add_column('resumes', sa.Column('template', sa.Integer()))
    op.execute("UPDATE resumes SET template = template_id")
    op.drop_constraint('fk_resumes_template_id', 'resumes')
    op.drop_column('resumes', 'template_id')
```

---

## Production Deployment

### Pre-Deployment Checklist

```bash
# ✅ 1. Test migrations locally
flask db upgrade
pytest app/tests/ -v

# ✅ 2. Backup production database
# Railway: Use Railway CLI or dashboard to create backup
railway run pg_dump > backup_$(date +%Y%m%d_%H%M%S).sql

# ✅ 3. Review migration files
cat migrations/versions/latest_migration.py

# ✅ 4. Check for breaking changes
# - Will existing data be preserved?
# - Are there default values for new required fields?
# - Can migration be rolled back?

# ✅ 5. Plan rollback strategy
# Know how to revert if something goes wrong
```

### Deployment Workflow

#### Option A: Railway Automatic Deployment

```bash
# 1. Push to main branch
git push origin main

# 2. Railway automatically:
#    - Builds new image
#    - Runs migrations (if configured)
#    - Deploys new version

# 3. Monitor deployment
railway logs

# 4. Verify migration applied
railway run flask db current
```

#### Option B: Manual Migration Control

```bash
# 1. Deploy code WITHOUT running migrations
git push origin main

# 2. Verify deployment successful
railway status

# 3. Manually run migrations
railway run flask db upgrade

# 4. Verify application health
curl https://your-app.railway.app/health

# 5. Check for errors
railway logs --tail
```

### Zero-Downtime Deployment Strategy

For critical migrations with large tables:

#### Phase 1: Add New Fields (Backward Compatible)

```python
# Migration 1: Add new column, keep old one
def upgrade():
    op.add_column('users', sa.Column('new_email', sa.String(120)))
```

Deploy this - old code still works with old column.

#### Phase 2: Dual Write (Application Update)

```python
# Update application to write to both columns
def update_user(user_id, email):
    user.email = email      # Old column
    user.new_email = email  # New column
    db.session.commit()
```

Deploy application update - now writing to both.

#### Phase 3: Backfill Data

```python
# Migration 2: Copy old data to new column
def upgrade():
    op.execute("""
        UPDATE users 
        SET new_email = email 
        WHERE new_email IS NULL
    """)
```

#### Phase 4: Switch to New Column

```python
# Update application to use new column only
def update_user(user_id, email):
    user.new_email = email  # Only new column
    db.session.commit()
```

#### Phase 5: Remove Old Column

```python
# Migration 3: Drop old column
def upgrade():
    op.drop_column('users', 'email')
    # Optionally rename new_email to email
    op.alter_column('users', 'new_email', new_column_name='email')
```

---

## Data Safety & Backup

### Backup Strategy

#### Local Development

```bash
# Quick backup
docker-compose exec -T db pg_dump -U postgres resume_app > backup.sql

# Restore
docker-compose exec -T db psql -U postgres resume_app < backup.sql

# Backup with compression
docker-compose exec -T db pg_dump -U postgres resume_app | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### Production (Railway)

```bash
# Create backup
railway run pg_dump $DATABASE_URL > production_backup_$(date +%Y%m%d_%H%M%S).sql

# List Railway backups (if automated backups enabled)
railway backups list

# Restore backup (CAREFUL!)
railway run psql $DATABASE_URL < backup.sql
```

### Automated Backup Script

Create `scripts/backup_database.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

echo "Creating backup: $BACKUP_FILE"
docker-compose exec -T db pg_dump -U postgres resume_app > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_FILE.gz"
```

### Recovery Plan

```bash
# 1. Stop application
docker-compose down

# 2. Start only database
docker-compose up -d db

# 3. Restore backup
cat backup.sql | docker-compose exec -T db psql -U postgres resume_app

# 4. Verify data
docker-compose exec db psql -U postgres resume_app -c "SELECT COUNT(*) FROM users;"

# 5. Restart application
docker-compose up
```

---

## Common Scenarios

### Scenario 1: I Made a Mistake in a Migration

#### If NOT yet pushed to git:

```bash
# 1. Rollback migration
flask db downgrade

# 2. Delete migration file
rm migrations/versions/bad_migration_file.py

# 3. Fix models
# Edit app/models/temp.py

# 4. Generate new migration
flask db migrate -m "correct migration"

# 5. Apply it
flask db upgrade
```

#### If ALREADY pushed to git:

```bash
# DON'T delete the migration!
# Create a new migration to fix it

flask db migrate -m "fix previous migration issue"
# Edit the new migration to correct the problem
flask db upgrade
```

### Scenario 2: Production and Development Out of Sync

```bash
# 1. Check current version in each environment
# Local:
flask db current

# Production:
railway run flask db current

# 2. If production is behind, apply migrations:
railway run flask db upgrade

# 3. If versions conflict, check migration history:
flask db history
```

### Scenario 3: Need to Reset Development Database

```bash
# Full reset (DESTROYS ALL DATA!)
docker-compose down -v
docker-compose up -d db
flask db upgrade

# Or manually:
docker-compose exec db psql -U postgres -c "DROP DATABASE resume_app;"
docker-compose exec db psql -U postgres -c "CREATE DATABASE resume_app;"
flask db upgrade
```

### Scenario 4: Adding Sample Data

Create `scripts/seed_database.py`:

```python
#!/usr/bin/env python3
"""Seed database with sample data for development"""

from app.server import app
from app.extensions import db
from app.models.temp import User, Resume, ResumeTemplate

def seed_data():
    with app.app_context():
        # Clear existing data (development only!)
        db.session.query(Resume).delete()
        db.session.query(User).delete()
        db.session.query(ResumeTemplate).delete()
        
        # Create sample template
        template = ResumeTemplate(
            name="Professional",
            description="Clean professional template",
            style_config={
                "font": "Arial",
                "color": "#333333"
            },
            sections=["contact", "experience", "education"]
        )
        db.session.add(template)
        db.session.flush()
        
        # Create sample user
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()
        
        # Create sample resume
        resume = Resume(
            user_id=user.id,
            serial_number=1,
            title="Software Engineer Resume",
            template_id=template.id,
            parsed_resume={
                "name": "Test User",
                "email": "test@example.com",
                "experience": []
            }
        )
        db.session.add(resume)
        
        db.session.commit()
        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    seed_data()
```

Usage:
```bash
python scripts/seed_database.py
```

---

## Troubleshooting

### Issue: "Target database is not up to date"

```bash
# Check current version
flask db current

# Check pending migrations
flask db upgrade --sql  # Shows SQL without executing

# Apply migrations
flask db upgrade
```

### Issue: "Can't locate revision identified by 'xxxx'"

```bash
# Migration file is missing or git branch issue
# 1. Check migrations directory
ls migrations/versions/

# 2. Ensure all migrations are pulled
git pull origin main

# 3. Check alembic_version table
docker-compose exec -T db psql -U postgres resume_app -c "SELECT * FROM alembic_version;"

# 4. If version in DB doesn't exist, stamp correct version:
flask db stamp head  # Mark current code as DB state
```

### Issue: Migration Fails Halfway

```bash
# 1. Check error message
flask db upgrade

# 2. Check database state
python3 verify_database_schema.py

# 3. Manual intervention may be needed
docker-compose exec db psql -U postgres resume_app

# 4. Fix manually, then mark migration as complete:
flask db stamp xxxx  # Use migration version ID
```

### Issue: Need to Skip a Migration

```bash
# Don't do this in production!
# For development only:

# Mark migration as applied without running it
flask db stamp +1  # Skip one migration forward
```

---

## Your Project Specific Guidelines

### 1. Primary Model File

```python
# ✅ USE THIS: app/models/temp.py
# This is the ACTIVE model file used by the application

# ❌ DON'T USE THESE (outdated):
# - app/models/user.py
# - app/models/resume.py
# - app/models/job_description.py
# - app/models/db.py
```

### 2. Composite Primary Keys

Your project uses composite keys on some tables:

```python
# resumes table: PRIMARY KEY (user_id, serial_number)
# job_descriptions: PRIMARY KEY (user_id, serial_number)

# When querying:
resume = Resume.query.filter_by(
    user_id=user_id,
    serial_number=serial_num
).first()

# When creating migrations, preserve these composite keys!
```

### 3. JSON Fields

Your models use JSON fields extensively:

```python
parsed_resume = db.Column(db.JSON, nullable=False)
style_config = db.Column(db.JSON)

# Migration best practice:
# Use server_default for JSON fields
op.add_column('table', 
    sa.Column('config', sa.JSON(), server_default='{}')
)
```

### 4. Current Issues to Address

Based on the analysis, you need to:

```bash
# 1. Fix missing primary keys
./fix_database_primary_keys.sh

# 2. Document Google integration tables
flask db revision -m "document google integration tables"
# Edit the migration to match current state

# 3. Clean up unused model files
# Consider removing or documenting:
# - app/models/user.py
# - app/models/resume.py
# - app/models/db.py
```

---

## Quick Reference Commands

```bash
# Development
flask db migrate -m "description"  # Create migration
flask db upgrade                   # Apply migrations
flask db downgrade                 # Rollback one migration
flask db current                   # Show current version
flask db history                   # Show all migrations

# Verification
python3 verify_database_schema.py  # Check schema matches models
pytest app/tests/ -v               # Run tests

# Backup
docker-compose exec -T db pg_dump -U postgres resume_app > backup.sql

# Production (Railway)
railway run flask db current       # Check version
railway run flask db upgrade       # Apply migrations
railway logs --tail                # Monitor errors
```

---

## Additional Resources

- **Flask-Migrate Docs**: https://flask-migrate.readthedocs.io/
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

## Summary: The Golden Rules

1. ✅ **Always use migrations** - Never `db.create_all()` in production
2. ✅ **Test locally first** - Every migration tested before production
3. ✅ **Backup before changes** - Always have a recovery plan
4. ✅ **Review generated migrations** - Don't blindly trust auto-generation
5. ✅ **Make migrations reversible** - Write proper `downgrade()` functions
6. ✅ **Commit migrations to git** - They're part of your code
7. ✅ **Handle existing data** - Add defaults, migrate data when needed
8. ✅ **Document breaking changes** - Communicate with team
9. ✅ **Monitor production** - Watch logs during deployment
10. ✅ **Never delete applied migrations** - Create new ones to fix issues

---

**Last Updated:** October 24, 2025  
**Maintained By:** Resume Modifier Team
