# 🗄️ Database Management Guide

**Status:** ✅ Updated November 25, 2024 - Clean, minimal, focused

---

## 🎯 **Current Active Tools**

### **Primary Tool: `database_manager.py`** ⭐
**Purpose:** Unified database management for all environments (development + Railway production)

**Features:**
- ✅ Railway PostgreSQL connection with retry logic
- ✅ Schema validation and automatic updates  
- ✅ Column addition and table creation
- ✅ Performance index management
- ✅ Comprehensive error handling and reporting

**Usage:**
```bash
# Show database info and table status
python3 database_manager.py info

# Validate current schema
python3 database_manager.py validate

# Update missing columns only
python3 database_manager.py columns

# Full database update (tables + columns + indexes)
python3 database_manager.py update

# Preview what would be done (safe)
python3 database_manager.py update --dry-run

# Test database connection
python3 database_manager.py test
```

### **Railway Deployment: `scripts/railway_migrate.py`** 🚀
**Purpose:** Automatic database initialization for Railway deployments

**Features:**
- ✅ Called automatically by Railway on deployment
- ✅ Uses Flask-SQLAlchemy models for table creation
- ✅ Configured in `railway.toml` startup command

**Usage:** Automatic - no manual intervention needed

---

## 🎛️ **Railway Database Management**

### **For Development (Local):**
```bash
# Use local database for development work
export DATABASE_URL="postgresql://postgres:password@localhost:5432/resume_app"
python3 database_manager.py info
```

### **For Railway Production:**
```bash
# Ensure Railway CLI is logged in
railway login
railway link

# Check production database status
railway run --service Postgres python3 database_manager.py info

# Validate production schema
railway run --service Postgres python3 database_manager.py validate

# Update production database (only if needed)
railway run --service Postgres python3 database_manager.py update

# Alternative: Use the helper script
python3 db_helper.py info         # Railway mode (default)
python3 db_helper.py validate     # Railway mode
```

### **For Deployment (Automatic):**
1. Push code to Railway
2. Railway automatically runs `scripts/railway_migrate.py`  
3. Database tables created/updated automatically
4. No manual intervention required

---

## 📋 **Schema Changes Workflow**

### **For Model Updates:**
```bash
# 1. Update models in core/app/models/
# 2. Create formal migration
cd core
flask db migrate -m "description of changes"

# 3. Test migration locally
flask db upgrade

# 4. Deploy to Railway (auto-applies migrations)
git push origin main
```

### **For Quick Column Updates:**
```bash
# Add new columns to database_manager.py
# Then apply updates
python3 database_manager.py columns
```

---

## 📚 **Documentation Structure**

### **Active Documentation:**
- **This file** - Current database management guide
- `CLEANUP_DATABASE_SCRIPTS.md` - Cleanup and migration audit
- `scripts/README.md` - Scripts directory documentation

### **Archived Documentation:**
- `archive/old_database_scripts/` - Previous database fix scripts (reference only)
- `archive/cleanup_2024_11_25/` - Obsolete scripts moved during cleanup

---

## ⚠️ **Important Notes**

### **Railway Connection Issues:**
If `railway run` commands fail with connection errors:
1. Ensure Railway CLI is installed: `npm i -g @railway/cli`
2. Login to Railway: `railway login`
3. Link project: `railway link`
4. For local development, use local database instead

### **Schema Validation:**
Always run `python3 database_manager.py validate` before and after changes to ensure schema integrity.

### **Backup Strategy:**
Railway handles automatic backups. For critical changes, consider manual backup before running updates.

---

## 🚀 **Quick Start Commands**

```bash
# Check everything is working
python3 database_manager.py info

# Validate current setup
python3 database_manager.py validate

# Update if needed
python3 database_manager.py update

# Deploy to Railway
git push origin main
```

---

**Last Updated:** November 25, 2024  
**Next Review:** As needed for schema changes
