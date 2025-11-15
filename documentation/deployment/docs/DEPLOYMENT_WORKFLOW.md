# 🚀 Deployment Workflow Cheat Sheet

Quick reference for deploying database changes from local development to production.

---

## 📝 Development → Production Workflow

### Step-by-Step Process

```
┌─────────────────┐
│ 1. Local Dev    │  Modify models, create migration
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 2. Test Local   │  Apply migration, test thoroughly
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 3. Git Commit   │  Commit migration files
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 4. Backup Prod  │  Create production backup
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 5. Deploy       │  Push to production
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 6. Run Migration│  Apply migration in production
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 7. Verify       │  Test production application
└─────────────────┘
```

---

## 💻 Detailed Commands

### 1️⃣ Local Development

```bash
# Edit your model
vim app/models/temp.py

# Generate migration
flask db migrate -m "add new field to users"

# Review the generated file!
cat migrations/versions/xxxx_add_new_field_to_users.py

# Apply migration locally
flask db upgrade

# Verify schema
python3 verify_database_schema.py

# Test application
pytest app/tests/ -v
docker-compose up

# Test the specific feature
curl -X POST http://localhost:5001/api/endpoint
```

### 2️⃣ Version Control

```bash
# Check what changed
git status

# Add migration and model files
git add migrations/versions/xxxx_*.py
git add app/models/temp.py

# Commit with clear message
git commit -m "feat: add phone number field to User model

- Added phone column to users table
- Migration tested locally with existing data
- Updated User model with phone validation"

# Push to feature branch
git push origin feature/add-phone-field

# Create Pull Request
# → Review by team
# → Merge to main
```

### 3️⃣ Production Backup

```bash
# Railway backup
railway run pg_dump > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup created
ls -lh backup_*.sql

# Compress for storage
gzip backup_*.sql
```

### 4️⃣ Deploy to Production

#### Automatic (Railway)

```bash
# Push to main triggers auto-deploy
git push origin main

# Monitor deployment
railway logs --tail

# Wait for deployment to complete
railway status
```

#### Manual Migration Control

```bash
# 1. Check current migration version
railway run flask db current

# 2. See pending migrations
railway run flask db history

# 3. Apply migrations
railway run flask db upgrade

# 4. Verify version updated
railway run flask db current
```

### 5️⃣ Verification

```bash
# Check application health
curl https://your-app.railway.app/health

# Test API endpoints
curl https://your-app.railway.app/api/endpoint

# Monitor for errors
railway logs --tail --filter error

# Check database state
railway run python3 verify_database_schema.py
```

---

## ⚠️ Handling Existing Data

### Scenario: Adding Nullable Field
✅ **Safe** - No special handling needed

```python
# Model
phone = db.Column(db.String(20))  # Nullable

# Migration (auto-generated is fine)
op.add_column('users', sa.Column('phone', sa.String(20)))

# Existing data: phone will be NULL
```

### Scenario: Adding Required Field
⚠️ **Requires Default Value**

```python
# Step 1: Add as nullable
status = db.Column(db.String(20))

# Migration
def upgrade():
    # Add column as nullable
    op.add_column('users', 
        sa.Column('status', sa.String(20), nullable=True)
    )
    
    # Populate existing records
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    
    # Make it NOT NULL
    op.alter_column('users', 'status', nullable=False)
```

### Scenario: Changing Column Type
⚠️ **May Lose Data**

```python
# From: bio = db.Column(db.String(200))
# To:   bio = db.Column(db.Text)  # No length limit

# Migration
def upgrade():
    # PostgreSQL: Simple alter
    op.alter_column('users', 'bio', 
        type_=sa.Text(),
        existing_type=sa.String(200)
    )
    
    # SQLite: Requires table recreation
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('bio', type_=sa.Text())
```

### Scenario: Dropping Column
🚨 **DATA LOSS**

```python
# Migration
def upgrade():
    # CAREFUL: This deletes data!
    op.drop_column('users', 'old_field')

def downgrade():
    # Can't restore data!
    op.add_column('users', sa.Column('old_field', sa.String(50)))
```

**Better approach for production:**

```python
# Phase 1: Stop writing to column (deploy app update)
# Phase 2: Wait a few days (ensure no issues)
# Phase 3: Drop column (data is confirmed not needed)
```

---

## 🔄 Rollback Procedures

### Rolling Back One Migration

```bash
# Local
flask db downgrade

# Production (CAREFUL!)
railway run flask db downgrade
```

### Rolling Back to Specific Version

```bash
# See migration history
flask db history

# Rollback to specific version
flask db downgrade <revision_id>

# Example:
flask db downgrade 9f843915c9ad
```

### Emergency Rollback (Application + Database)

```bash
# 1. Revert code deployment
git revert HEAD
git push origin main

# 2. Rollback database
railway run flask db downgrade

# 3. Restore from backup (if needed)
railway run psql $DATABASE_URL < backup.sql

# 4. Verify application
curl https://your-app.railway.app/health
```

---

## 🧪 Testing Migrations Before Production

### Test Migration with Production Data Copy

```bash
# 1. Download production backup
railway run pg_dump > prod_backup.sql

# 2. Load into local database
docker-compose down -v
docker-compose up -d db
cat prod_backup.sql | docker-compose exec -T db psql -U postgres resume_app

# 3. Apply your migration to production data
flask db upgrade

# 4. Test application with production-like data
docker-compose up
pytest app/tests/ -v

# 5. Verify no data corruption
python3 verify_database_schema.py
```

---

## 📊 Common Migration Patterns

### Pattern 1: Adding Indexed Column

```python
def upgrade():
    # Add column
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), 
                                      server_default='false'))
    
    # Add index for faster queries
    op.create_index('idx_users_email_verified', 'users', ['email_verified'])

def downgrade():
    op.drop_index('idx_users_email_verified')
    op.drop_column('users', 'email_verified')
```

### Pattern 2: Adding Unique Constraint

```python
def upgrade():
    # Add column
    op.add_column('users', sa.Column('username', sa.String(50)))
    
    # Check for duplicates first!
    duplicates = op.get_bind().execute("""
        SELECT username, COUNT(*) 
        FROM users 
        WHERE username IS NOT NULL 
        GROUP BY username 
        HAVING COUNT(*) > 1
    """).fetchall()
    
    if duplicates:
        raise Exception(f"Cannot add unique constraint, duplicates found: {duplicates}")
    
    # Add unique constraint
    op.create_unique_constraint('uq_users_username', 'users', ['username'])
```

### Pattern 3: Adding Foreign Key

```python
def upgrade():
    # Add column
    op.add_column('resumes', 
        sa.Column('template_id', sa.Integer(), nullable=True)
    )
    
    # Add foreign key
    op.create_foreign_key(
        'fk_resumes_template_id',  # Constraint name
        'resumes',                  # Source table
        'resume_templates',         # Target table
        ['template_id'],            # Source columns
        ['id']                      # Target columns
    )
```

### Pattern 4: Creating Table with Relationships

```python
def upgrade():
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preferences', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        
        # Foreign key
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], 
                                name='fk_user_preferences_user_id'),
        
        # Unique constraint
        sa.UniqueConstraint('user_id', name='uq_user_preferences_user_id')
    )
```

---

## 🎯 Quick Checklist

Before deploying migration to production:

- [ ] Migration tested locally with fresh database
- [ ] Migration tested locally with existing data
- [ ] Migration tested with production data copy (if available)
- [ ] `downgrade()` function implemented and tested
- [ ] Default values provided for new required fields
- [ ] No data loss from column changes
- [ ] Indexes added for new columns that will be queried
- [ ] Application code compatible with schema changes
- [ ] Tests passing (pytest app/tests/ -v)
- [ ] Migration committed to git
- [ ] Pull request reviewed and approved
- [ ] Production backup created
- [ ] Deployment plan documented
- [ ] Rollback plan ready
- [ ] Team notified of deployment

---

## 🆘 Emergency Contacts

```bash
# Check what went wrong
railway logs --tail --filter error

# Database connection test
railway run python -c "from app.extensions import db; print('DB OK')"

# Check migration status
railway run flask db current

# Quick rollback
railway run flask db downgrade

# Restore from backup (last resort)
railway run psql $DATABASE_URL < backup.sql
```

---

## 📚 Additional Resources

- Full guide: `docs/DATABASE_BEST_PRACTICES.md`
- Schema verification: `python3 verify_database_schema.py`
- Fix primary keys: `./fix_database_primary_keys.sh`
- Database analysis: `DATABASE_ANALYSIS.md`

---

**Remember:** 
- 🟢 Green = Safe to proceed
- 🟡 Yellow = Proceed with caution
- 🔴 Red = High risk, needs careful planning

**Golden Rule:** If you're not sure, ASK! Better to delay than to lose production data.
