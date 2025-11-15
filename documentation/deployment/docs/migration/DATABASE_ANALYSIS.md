# Database Analysis Report
**Date:** October 24, 2025  
**Database:** PostgreSQL (currently configured)  
**Previous Database:** MySQL (commented out in .env)

---

## Executive Summary

This project has undergone database evolution with **multiple table creation methods** and **schema inconsistencies** between model files. The current database likely **does NOT contain the latest table structure** based on the analysis below.

---

## 🔍 How Tables Were Originally Created

### Method 1: Alembic Migrations (Primary Method)
The project uses **Flask-Migrate (Alembic)** as the official database migration tool.

#### Migration History (Chronological Order):
1. **`02dfd41ec2cd_initial_migration.py`** (2025-05-13 20:58:18)
   - **First migration** - Created initial tables:
     - ✅ `users` table (with username, password_hash, email, etc.)
     - ✅ `resumes` table (with id, user_id, serial_number, template, parsed_resume)
     - ✅ `job_descriptions` table (with id, user_id, serial_number, etc.)

2. **`d7c7301cd2d8_initial_migration.py`** (2025-05-13 21:00:40)
   - Modified `job_descriptions` table:
     - ❌ **DROPPED** the `id` column (primary key)
     - Made `user_id` and `serial_number` NOT NULL
     - Changed to composite primary key (user_id, serial_number)

3. **`9f843915c9ad_initial_migration.py`** (2025-05-13 21:02:10)
   - Modified `resumes` table:
     - ❌ **DROPPED** the `id` column (primary key)
     - Made `user_id` and `serial_number` NOT NULL
     - Changed to composite primary key (user_id, serial_number)

4. **`create_user_sites_table.py`** (Manual creation)
   - ✅ Created `user_sites` table
   - Columns: id, user_id, resume_serial, subdomain, html_content, timestamps
   - Unique constraint on subdomain and (user_id, resume_serial)

5. **`f2eae0e50079_add_google_docs_integration_models.py`** (2025-10-16)
   - **Empty migration** (both upgrade() and downgrade() are `pass`)
   - ⚠️ **Critical Issue**: Migration file exists but does NOT create tables!

### Method 2: Manual Table Creation (`init_db.py`)
Located at `app/init_db.py`, this script uses `db.create_all()`:
```python
def init_db():
    with app.app_context():
        db.create_all()
```
This creates tables based on current model definitions, **bypassing migration system**.

---

## 📊 Current Model Files Analysis

### Active Models in Production (`app/models/temp.py`)
This file contains **ALL active models** used by the application:

1. ✅ **User** (`users` table)
   - Fields: id, username, password, email, first_name, last_name, city, bio, country, timestamps
   - Relationships: resumes, job_descriptions, google_auth, generated_documents

2. ✅ **Resume** (`resumes` table)
   - **Composite Primary Key**: (user_id, serial_number)
   - Fields: user_id, serial_number, title, extracted_text, template_id, parsed_resume, timestamps
   - **Key Change**: Uses `template_id` (FK to resume_templates) instead of `template` integer

3. ✅ **JobDescription** (`job_descriptions` table)
   - **Composite Primary Key**: (user_id, serial_number)
   - Fields: user_id, serial_number, title, description, created_at

4. ✅ **UserSite** (`user_sites` table) - ✅ Has migration
   - Fields: id, user_id, resume_serial, subdomain, html_content, timestamps

5. ❌ **ResumeTemplate** (`resume_templates` table) - ⚠️ **NO MIGRATION**
   - Fields: id, name, description, style_config (JSON), sections (JSON), is_active, timestamps
   - **Missing from database!**

6. ❌ **GoogleAuth** (`google_auth_tokens` table) - ⚠️ **NO MIGRATION**
   - Fields: id, user_id, google_user_id, email, name, picture, access_token, refresh_token, token_expires_at, scope, timestamps
   - **Missing from database!**

7. ❌ **GeneratedDocument** (`generated_documents` table) - ⚠️ **NO MIGRATION**
   - Fields: id, user_id, resume_id, template_id, google_doc_id, google_doc_url, document_title, job_description_used, generation_status, timestamps
   - **Missing from database!**

### Outdated/Unused Models (Individual Files)
- `app/models/user.py` - Simple User model (different schema than temp.py)
- `app/models/resume.py` - Simple Resume model with different schema
- `app/models/job_description.py` - Simple JobDescription model
- `app/models/resume_analysis.py` - ResumeAnalysis model (not used in temp.py)
- `app/models/db.py` - Uses SQLAlchemy Base (declarative_base), different from Flask-SQLAlchemy

---

## 🚨 Critical Issues Identified

### Issue #1: Missing Migrations for New Tables
**Problem:** Three tables are defined in models but have NO migrations:
- ❌ `resume_templates`
- ❌ `google_auth_tokens`
- ❌ `generated_documents`

**Impact:** If database was created using migrations only, these tables **DO NOT EXIST**.

**Evidence from logs:**
```
docs/google-api-400.md line 105:
"the `generated_documents` table doesn't exist"
```

### Issue #2: Empty Migration File
**File:** `f2eae0e50079_add_google_docs_integration_models.py`
- Created on 2025-10-16 for "Add Google Docs integration models"
- **Both `upgrade()` and `downgrade()` are empty!**
- Should have created: GoogleAuth, GeneratedDocument, ResumeTemplate tables

### Issue #3: Model Definition Conflicts
**Problem:** Multiple versions of same models exist:
- `app/models/temp.py` - **ACTIVE** (used by server.py)
- `app/models/user.py`, `resume.py`, etc. - **INACTIVE** (different schemas)
- `app/models/db.py` - Uses different ORM style (declarative_base vs db.Model)

### Issue #4: Schema Mismatches
**Resume table differences:**
- **Migration (02dfd41ec2cd)**: Has `template` field (Integer)
- **Current Model (temp.py)**: Has `template_id` field (FK to resume_templates)
- **Database likely has**: Old schema with `template` integer

### Issue #5: Primary Key Changes
**Major breaking changes in migrations:**
- Migration `d7c7301cd2d8`: Dropped `id` from `job_descriptions`
- Migration `9f843915c9ad`: Dropped `id` from `resumes`
- Changed to composite PKs: (user_id, serial_number)

---

## 🔎 Database vs Model Comparison

### What Migrations Created (Database should have):
```
✅ users (id PK, username, password, email, first_name, last_name, city, bio, country, timestamps)
✅ resumes (user_id+serial_number PK, title, extracted_text, template, parsed_resume, timestamps)
✅ job_descriptions (user_id+serial_number PK, title, description, created_at)
✅ user_sites (id PK, user_id, resume_serial, subdomain, html_content, timestamps)
❌ resume_templates - NOT CREATED
❌ google_auth_tokens - NOT CREATED
❌ generated_documents - NOT CREATED
```

### What Models Define (Application expects):
```
✅ users (matches)
⚠️ resumes (expects template_id FK, not template integer)
✅ job_descriptions (matches)
✅ user_sites (matches)
❌ resume_templates (missing from DB)
❌ google_auth_tokens (missing from DB)
❌ generated_documents (missing from DB)
```

### Verdict:
**❌ NO - Database does NOT match latest model definitions**

---

## 🛠️ Recommended Actions

### Immediate Actions:

1. **Check Current Database State**
   ```bash
   # Connect to database
   docker-compose up -d db
   docker-compose exec db psql -U postgres resume_app
   
   # List all tables
   \dt
   
   # Check specific table structures
   \d users
   \d resumes
   \d job_descriptions
   \d user_sites
   ```

2. **Verify Missing Tables**
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('resume_templates', 'google_auth_tokens', 'generated_documents');
   ```

3. **Create Proper Migration for Missing Tables**
   ```bash
   # Generate migration from current models
   docker-compose exec web flask db migrate -m "add missing google integration tables"
   
   # Review the generated migration file
   # Apply migration
   docker-compose exec web flask db upgrade
   ```

### Alternative: Clean Database Recreation

If no production data exists:
```bash
# Stop containers
docker-compose down -v

# Remove migration files (keep only the versions directory structure)
# Edit f2eae0e50079 migration to include proper table creation

# Recreate database from scratch
docker-compose up -d db
docker-compose exec web flask db upgrade
```

### Long-term Fixes:

1. **Consolidate Model Files**
   - Delete unused model files (user.py, resume.py, job_description.py, db.py)
   - Keep only `temp.py` or rename it to a more descriptive name

2. **Fix Empty Migration**
   - Update `f2eae0e50079_add_google_docs_integration_models.py` with proper table creation code

3. **Add Migration Tests**
   - Create tests to verify migration integrity
   - Ensure all model tables exist after migrations

4. **Document Database Schema**
   - Create ER diagram
   - Document all tables, relationships, and constraints

---

## 📋 Database Schema Summary (Expected Final State)

### Tables with Migrations ✅
- `users` - User accounts
- `resumes` - User resumes (composite PK)
- `job_descriptions` - Job postings (composite PK)
- `user_sites` - Generated resume websites

### Tables Missing Migrations ❌
- `resume_templates` - Resume templates configuration
- `google_auth_tokens` - OAuth tokens
- `generated_documents` - Google Docs export tracking

### Foreign Key Relationships
```
users (1) → (∞) resumes
users (1) → (∞) job_descriptions
users (1) → (1) google_auth_tokens
users (1) → (∞) generated_documents
resume_templates (1) → (∞) resumes
resume_templates (1) → (∞) generated_documents
(users.id, resumes.serial_number) → generated_documents (composite FK)
```

---

## 🎯 Conclusion & Actual Database State

### ✅ ACTUAL DATABASE VERIFICATION (October 24, 2025)

**Database Query Results:**
```sql
-- Tables present in database:
✅ users
✅ resumes
✅ job_descriptions  
✅ user_sites
✅ resume_templates
✅ google_auth_tokens
✅ generated_documents
✅ alembic_version (migration tracking)
```

**Current Migration Version:** `f2eae0e50079` (latest)

### 🔍 Key Findings:

#### 1. **Tables Created Successfully** ✅
Despite the migration file `f2eae0e50079` having empty `upgrade()` function, **ALL tables exist** in the database!

**This indicates:**
- Tables were created using `db.create_all()` method (from `app/init_db.py`)
- OR tables were manually created via SQL
- The migration tracking was updated without actual migration code

#### 2. **Resumes Table Structure** ⚠️
```sql
Column: template_id (integer, not null)
Primary Key: NOT DEFINED (only NOT NULL constraints exist)
Foreign Keys: user_id → users(id)
```

**Issue:** Model expects composite PK `(user_id, serial_number)` but database has **NO PRIMARY KEY**!

#### 3. **Schema Matches Models** ✅
- `resume_templates` table matches `ResumeTemplate` model
- `google_auth_tokens` table matches `GoogleAuth` model  
- `generated_documents` table matches `GeneratedDocument` model
- All columns and relationships are correct

### 🚨 Critical Discovery: Mixed Creation Methods

**Original Creation Method:** 
1. **Initial tables:** Alembic migrations (02dfd41ec2cd → 9f843915c9ad)
2. **Google integration tables:** Manual creation via `db.create_all()` or SQL

**Evidence:**
- Migration `f2eae0e50079` is marked as applied but contains no table creation code
- Tables exist with correct schema matching models
- This is a **dangerous pattern** - bypasses migration system

### ⚠️ Database Integrity Issues

#### Primary Key Missing on `resumes` Table
```sql
-- Expected (from model):
PRIMARY KEY (user_id, serial_number)

-- Actual (from database):
NO PRIMARY KEY DEFINED
```

**Risk:** Data integrity issues, duplicate records possible

#### Similar Issue May Exist on `job_descriptions`
Need to verify if composite PK was successfully applied.

### 📋 Recommended Immediate Actions

1. **Add Missing Primary Keys**
   ```sql
   ALTER TABLE resumes 
   ADD PRIMARY KEY (user_id, serial_number);
   
   ALTER TABLE job_descriptions 
   ADD PRIMARY KEY (user_id, serial_number);
   ```

2. **Create Proper Migration for Google Tables**
   - Edit `f2eae0e50079` to include actual table creation code
   - OR create new migration that documents the current state
   - This ensures migrations match actual database schema

3. **Verify All Constraints**
   ```bash
   docker-compose exec -T db psql -U postgres resume_app -c "
   SELECT table_name, constraint_name, constraint_type 
   FROM information_schema.table_constraints 
   WHERE table_schema = 'public' 
   ORDER BY table_name;"
   ```

4. **Document Creation Method**
   - Add comments explaining how Google integration tables were created
   - Establish rule: ALL schema changes must go through migrations

### 🎯 Final Answer

**Q: How were tables originally created?**  
**A:** Mixed approach:
- Core tables (users, resumes, job_descriptions, user_sites): **Alembic migrations**
- Google integration tables (resume_templates, google_auth_tokens, generated_documents): **Manual creation** via `db.create_all()` or direct SQL

**Q: Does current database contain latest table structure?**  
**A:** **Mostly YES** - all tables and columns exist, BUT:
- ❌ Missing primary keys on `resumes` table
- ❌ Migration history doesn't match actual schema (empty migration file)
- ⚠️ Need to verify `job_descriptions` primary key
- ⚠️ Migration system was bypassed for recent tables

**Risk Level:** 🟡 MEDIUM - Database works but lacks proper migration tracking and some constraints
