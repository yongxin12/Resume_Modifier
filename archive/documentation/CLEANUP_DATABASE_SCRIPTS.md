# 🧹 Database Scripts Cleanup & Migration Guide

## Current Status: CLEANUP REQUIRED ⚠️

This project has accumulated numerous database migration scripts over time. This document identifies what's current vs obsolete and provides the definitive migration guidance.

---

## ✅ **ACTIVE DATABASE TOOLS** (Keep These)

### 1. **`database_manager.py`** - Primary Tool
**Status:** ✅ Current, comprehensive, Railway-compatible
**Purpose:** Unified database management for all environments
**Features:**
- Railway PostgreSQL connection with retry logic  
- Schema validation and updates
- Column addition and table creation
- Performance index management
- Comprehensive error handling

**Usage:**
```bash
# Show database info
python3 database_manager.py info

# Validate schema
python3 database_manager.py validate

# Update missing columns
python3 database_manager.py columns

# Full database update
python3 database_manager.py update
```

### 2. **`scripts/railway_migrate.py`** - Railway Deployment
**Status:** ✅ Current, used by Railway
**Purpose:** Database initialization for Railway deployments
**Features:**
- Called automatically by Railway (configured in railway.toml)
- Uses Flask-SQLAlchemy models
- Creates all tables from current models

**Usage:** Automatic via Railway deployment

### 3. **Flask-Migrate System** - Schema Changes
**Status:** ✅ Active, located in `core/migrations/`
**Purpose:** Formal database schema changes
**Usage:**
```bash
cd core
flask db migrate -m "description"
flask db upgrade
```

---

## ❌ **OBSOLETE SCRIPTS** (Delete These)

### Root Directory Obsolete Files:
- `add_missing_columns.py` ❌ (superseded by database_manager.py)
- `add_oauth_persistence_fields.py` ❌ (integrated into models)
- `analyze_database_scripts.py` ❌ (one-time analysis script)
- `fix_all_timestamps.py` ❌ (specific fix, no longer needed)
- `fix_columns_safe.py` ❌ (superseded by database_manager.py)
- `fix_railway_database.py` ❌ (superseded by database_manager.py)
- `fix_railway_schema.py` ❌ (superseded by database_manager.py)
- `railway_migration.py` ❌ (superseded by scripts/railway_migrate.py)
- `railway_migration_simple.py` ❌ (superseded by scripts/railway_migrate.py)
- `railway_setup.py` ❌ (one-time setup, no longer needed)
- `update_database.py` ❌ (superseded by database_manager.py)

### Test Files (Keep for Testing):
- `test_database_integration.py` ✅ (testing tool)
- `test_railway_*.py` ✅ (testing tools)

### Archive Directory:
- `archive/old_database_scripts/` ✅ (already archived, keep for reference)

---

## 🎯 **DEFINITIVE RAILWAY MIGRATION PROCESS**

### For Development:
```bash
# 1. Validate local database
python3 database_manager.py validate

# 2. Test connection
python3 database_manager.py info

# 3. Apply updates if needed
python3 database_manager.py update
```

### For Railway Deployment:
1. **Automatic Process (Recommended):**
   - Railway automatically runs `scripts/railway_migrate.py` on deployment
   - Configured in `railway.toml`: `startCommand = "bash -c 'python scripts/railway_migrate.py && python railway_start.py'"`
   - No manual intervention needed

2. **Manual Railway Database Management:**
   ```bash
   # Check production database
   railway run python3 database_manager.py info
   
   # Validate production schema
   railway run python3 database_manager.py validate
   
   # Update production database (if needed)
   railway run python3 database_manager.py update
   ```

3. **For Schema Changes (Model Updates):**
   ```bash
   # 1. Update models in core/app/models/
   # 2. Create migration
   cd core
   flask db migrate -m "description of changes"
   
   # 3. Deploy to Railway (migrations run automatically)
   git push origin main
   ```

---

## 📋 **CLEANUP ACTION PLAN**

### Phase 1: Safe Cleanup
1. Move obsolete scripts to archive
2. Update documentation
3. Test current tools

### Phase 2: Validation
1. Test Railway connection
2. Validate database manager functionality
3. Confirm automatic migrations work

### Phase 3: Documentation Update
1. Update DATABASE_SCRIPTS_README.md
2. Remove obsolete references
3. Create definitive migration guide

---

## 🚀 **CURRENT RAILWAY CONNECTION ISSUE**

**Problem:** Railway connection failing with "Name or service not known"
**Cause:** Running `railway run` commands locally without proper Railway CLI context

**Solutions:**
1. **For Local Development:**
   ```bash
   # Use local database for development
   export DATABASE_URL="postgresql://postgres:password@localhost:5432/resume_app"
   python3 database_manager.py info
   ```

2. **For Railway Production Management:**
   ```bash
   # Ensure Railway CLI is installed and logged in
   railway login
   railway link
   
   # Then use Railway commands
   railway run python3 database_manager.py info
   ```

3. **For Deployment (Automatic):**
   - Railway automatically handles database setup
   - No manual commands needed
   - Scripts run automatically via railway.toml

---

## ✅ **RECOMMENDED WORKFLOW**

### Daily Development:
1. Use `database_manager.py` for local database management
2. Test changes locally before deployment
3. Use Flask-Migrate for schema changes

### Deployment:
1. Push code to Railway
2. Railway automatically runs migrations
3. Monitor deployment logs for any issues

### Production Maintenance:
1. Use `railway run python3 database_manager.py info` to check status
2. Only run manual updates if automatic process fails

---

**Next Steps:** Execute cleanup script to remove obsolete files and update documentation.