# 📘 Database Management Quick Start Guide

**For:** Resume Modifier Developers  
**Purpose:** Get started with database management best practices  
**Last Updated:** October 24, 2025

---

## 🎯 What You Need to Know

### The Golden Rules

1. **ALWAYS use Flask-Migrate** for schema changes
2. **NEVER** use `db.create_all()` in production
3. **ALWAYS** backup before deploying to production
4. **ALWAYS** test migrations locally first
5. **NEVER** modify existing migration files (create new ones to fix)

---

## 🚀 Quick Start

### For New Developers

```bash
# 1. Clone and setup
git clone https://github.com/Andrlulu/Resume_Modifier.git
cd Resume_Modifier
cp .env.example .env
# Edit .env with your settings

# 2. Start database
docker-compose up -d db

# 3. Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Apply migrations (creates all tables)
flask db upgrade

# 5. Verify everything is correct
python3 verify_database_schema.py

# 6. Start application
docker-compose up
```

### Daily Development

```bash
# Pull latest code
git pull origin main

# Apply any new migrations
flask db upgrade

# Start working
docker-compose up
```

---

## 🔧 Making Database Changes

### Simple Example: Adding a Field

```bash
# 1. Edit the model
vim app/models/temp.py

# Add field to User model:
# phone = db.Column(db.String(20))

# 2. Generate migration
flask db migrate -m "add phone to users"

# 3. Review the generated file
cat migrations/versions/*_add_phone_to_users.py

# 4. Test locally
flask db upgrade
python3 verify_database_schema.py

# 5. Commit to git
git add migrations/versions/*_add_phone_to_users.py
git add app/models/temp.py
git commit -m "feat: add phone field to User"
git push
```

### Complex Example: Adding Required Field with Existing Data

```bash
# 1. Add field as NULLABLE first
# In app/models/temp.py:
# status = db.Column(db.String(20))  # Nullable

# 2. Generate migration
flask db migrate -m "add status to users"

# 3. Edit migration to populate existing data
vim migrations/versions/*_add_status_to_users.py

# Add to upgrade():
def upgrade():
    op.add_column('users', sa.Column('status', sa.String(20)))
    # Populate existing records
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    # Make it required
    op.alter_column('users', 'status', nullable=False)

# 4. Test and deploy as above
```

---

## 🚀 Deploying to Production (Railway)

### Pre-Deployment Checklist

```bash
✅ Migration tested locally
✅ Tests passing (pytest app/tests/ -v)
✅ Migration committed to git
✅ Production backup created
✅ Team notified
```

### Deployment Commands

```bash
# 1. Create production backup
railway run pg_dump > backup_$(date +%Y%m%d).sql

# 2. Deploy code
git push origin main
# Railway auto-deploys

# 3. Apply migration
railway run flask db upgrade

# 4. Verify
curl https://your-app.railway.app/health
railway logs --tail
```

---

## 🆘 Common Issues

### Issue: Migration Fails

```bash
# Check what went wrong
flask db current
python3 verify_database_schema.py

# Rollback if needed
flask db downgrade

# Fix and try again
```

### Issue: Out of Sync with Production

```bash
# Check versions
flask db current  # Local
railway run flask db current  # Production

# Sync by applying migrations
railway run flask db upgrade
```

### Issue: Need to Reset Local Database

```bash
# Nuclear option (destroys all data!)
docker-compose down -v
docker-compose up -d db
flask db upgrade
```

---

## 📚 Full Documentation

| Document | When to Read |
|----------|--------------|
| [DATABASE_BEST_PRACTICES.md](docs/DATABASE_BEST_PRACTICES.md) | Comprehensive guide - read before making complex changes |
| [DEPLOYMENT_WORKFLOW.md](docs/DEPLOYMENT_WORKFLOW.md) | Quick reference for deploying changes |
| [DATABASE_REVIEW_SUMMARY.md](DATABASE_REVIEW_SUMMARY.md) | Understanding current database state |
| [DATABASE_ANALYSIS.md](DATABASE_ANALYSIS.md) | Deep technical analysis of database |

---

## 🔍 Useful Commands

```bash
# Development
flask db migrate -m "description"    # Create migration
flask db upgrade                     # Apply migrations
flask db downgrade                   # Rollback one
flask db current                     # Show version
flask db history                     # Show all migrations

# Verification
python3 verify_database_schema.py    # Check schema
pytest app/tests/ -v                 # Run tests

# Backup
docker-compose exec -T db pg_dump -U postgres resume_app > backup.sql

# Production (Railway)
railway run flask db upgrade         # Apply migrations
railway run flask db current         # Check version
railway logs --tail                  # Monitor
```

---

## 🎓 Learning Path

### Beginner
1. Read this Quick Start Guide
2. Try adding a simple nullable field
3. Read DEPLOYMENT_WORKFLOW.md

### Intermediate
1. Add a required field with data migration
2. Create a new table with relationships
3. Read DATABASE_BEST_PRACTICES.md sections 1-4

### Advanced
1. Perform zero-downtime deployment
2. Handle complex data transformations
3. Read all of DATABASE_BEST_PRACTICES.md

---

## ⚡ Scripts Available

| Script | Purpose |
|--------|---------|
| `verify_database_schema.py` | Verify database matches models |
| `fix_database_primary_keys.sh` | Fix current PK issues |
| `scripts/backup_database.sh` | Create automated backup |
| `scripts/seed_database.py` | Add sample data for testing |

---

## 💡 Best Practices Summary

### DO ✅
- Use migrations for all schema changes
- Test migrations locally first
- Review auto-generated migrations
- Write reversible migrations
- Backup before production changes
- Commit migrations to git

### DON'T ❌
- Use `db.create_all()` in production
- Modify existing migrations
- Add NOT NULL without defaults
- Skip testing migrations
- Delete migration files
- Make manual SQL changes

---

## 🎯 Current Project Status

Based on recent analysis (October 24, 2025):

**Database State:**
- ✅ All tables exist
- ✅ All columns match models
- ⚠️ Missing 2 primary keys (resumes, job_descriptions)

**Immediate Action Needed:**
```bash
# Fix missing primary keys
./fix_database_primary_keys.sh
```

**Ongoing Improvements:**
- Document Google integration tables in migrations
- Clean up unused model files
- Establish clear migration workflow

---

## 🤝 Getting Help

1. **Check documentation** in `docs/` folder
2. **Run verification** scripts
3. **Check git history** for similar changes
4. **Ask the team** before risky changes
5. **Test in development** first

---

## 📞 Quick Reference

**Emergency Rollback:**
```bash
railway run flask db downgrade
```

**Check Status:**
```bash
flask db current
python3 verify_database_schema.py
```

**Fresh Start:**
```bash
docker-compose down -v
docker-compose up -d db
flask db upgrade
```

---

**Remember:** When in doubt, backup and test first! 🛡️

---

**Last Updated:** October 24, 2025  
**Maintained By:** Resume Modifier Team  
**Questions?** Check docs/ folder or ask in team chat
