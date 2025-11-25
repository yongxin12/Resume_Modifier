# Database Management Scripts

## Active Scripts

### 🚀 Primary Tool: `database_manager.py`
**Purpose:** Unified database management for all environments
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

# Dry run (show what would be done)
python3 database_manager.py update --dry-run
```

### 🏗️ Deployment Script: `scripts/railway_migrate.py`
**Purpose:** Database initialization for Railway deployments
**Usage:** Automatically called by Railway (configured in railway.toml)

## Archived Scripts
- `archive/old_database_scripts/` - Contains previous database fix scripts
- These are kept for reference but should not be used

## Migration Management
- Use Flask-Migrate for formal schema changes: `flask db migrate`
- Use database_manager.py for quick fixes and updates
- Always test changes in development first

## Railway Deployment
1. Changes to database_manager.py are automatically deployed
2. Railway calls scripts/railway_migrate.py on startup
3. Use `railway run python3 database_manager.py info` to check production database
