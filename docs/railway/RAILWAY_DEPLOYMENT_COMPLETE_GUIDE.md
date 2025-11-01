# 🚄 Complete Railway Deployment Guide for Resume Modifier Backend

**A comprehensive, production-ready deployment guide following best practices**

---

## 📑 Table of Contents

1. [Prerequisites & Planning](#-prerequisites--planning)
2. [Pre-Deployment Checklist](#-pre-deployment-checklist)
3. [Initial Railway Setup](#-initial-railway-setup)
4. [Database Configuration](#-database-configuration)
5. [Environment Variables Setup](#-environment-variables-setup)
6. [Database Migration Strategy](#-database-migration-strategy)
7. [Deployment & Testing](#-deployment--testing)
8. [Post-Deployment Configuration](#-post-deployment-configuration)
9. [Monitoring & Maintenance](#-monitoring--maintenance)
10. [Troubleshooting Guide](#-troubleshooting-guide)
11. [CI/CD & Automation](#-cicd--automation)
12. [Security Best Practices](#-security-best-practices)

---

## 📋 Prerequisites & Planning

### Required Accounts & Access
- ✅ [Railway Account](https://railway.app) (free tier available)
- ✅ [GitHub Account](https://github.com) with repository access
- ✅ [OpenAI API Key](https://platform.openai.com/account/api-keys)
- ✅ [Google Cloud Console](https://console.cloud.google.com) (for OAuth)

### Local Development Environment
```bash
# Verify you have the following installed:
python --version    # Should be 3.11 or 3.12
git --version       # Latest stable
railway --version   # Railway CLI (optional but recommended)
```

### Install Railway CLI (Recommended)
```bash
# macOS/Linux
npm i -g @railway/cli

# Or using Homebrew (macOS)
brew install railway

# Or using pip
pip install railway

# Verify installation
railway --version

# Login to Railway
railway login
```

---

## ✅ Pre-Deployment Checklist

### 1. Code Repository Preparation

```bash
# Ensure your repository is clean
git status

# Make sure all changes are committed
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Verify Required Files Exist

```bash
# Check for these critical files:
ls -la Procfile                # ✅ Must exist
ls -la railway.toml            # ✅ Must exist
ls -la requirements.txt        # ✅ Must exist
ls -la railway_start.py        # ✅ Must exist
ls -la app/__init__.py         # ✅ Must exist
ls -la migrations/             # ✅ Must exist
```

**✅ File Verification:**
```bash
# Procfile should contain:
cat Procfile
# Expected: web: python railway_start.py

# railway.toml should have:
cat railway.toml
# Should include builder, startCommand, healthcheckPath

# railway_start.py should be executable entry point
cat railway_start.py | head -20
```

### 3. Verify Database Models

```bash
# Ensure all models are properly defined
ls -la app/models/temp.py

# Verify migration files exist
ls -la migrations/versions/
# Should see: e5218d5636ae_initial_migration_with_all_tables.py
```

### 4. Local Testing Before Deployment

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Test the application locally
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/resume_app"
export OPENAI_API_KEY="your-test-key"
export JWT_SECRET="test-secret"
export FLASK_SECRET_KEY="test-flask-secret"

# Run the app
python railway_start.py

# In another terminal, test health endpoint
curl http://localhost:5001/health
# Expected: {"status": "healthy", ...}

# Test API documentation
curl http://localhost:5001/apidocs
# Should return HTML page
```

### 5. Run Tests

```bash
# Run full test suite
pytest app/tests/ -v

# Check for any failures
pytest app/tests/ --tb=short

# Verify all 67 tests pass
pytest app/tests/ -v | grep "passed"
```

---

## 🚀 Initial Railway Setup

### Step 1: Create Railway Project

#### Option A: Via Railway Dashboard (Recommended for First-Time)

1. **Go to [Railway Dashboard](https://railway.app/dashboard)**

2. **Create New Project**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**

3. **Connect GitHub Repository**
   - Authorize Railway to access your GitHub
   - Select `Resume_Modifier` repository
   - Choose branch: `main` (or your deployment branch)

4. **Railway Auto-Detection**
   - Railway will automatically detect Python project
   - It will read `railway.toml` for configuration
   - Build process will be configured automatically

#### Option B: Via Railway CLI

```bash
# Navigate to project directory
cd /path/to/Resume_Modifier

# Initialize Railway project
railway init

# Select "Create new project"
# Name it: "resume-modifier-backend"

# Link the project
railway link

# Verify link
railway status
# Should show: Project: resume-modifier-backend
```

### Step 2: Verify Project Configuration

```bash
# Check Railway project status
railway status

# Expected output:
# Project: resume-modifier-backend
# Environment: production
# Service: Resume_Modifier
```

---

## 🗄️ Database Configuration

### Step 1: Add PostgreSQL Service

#### Via Railway Dashboard:

1. **In your Railway project:**
   - Click **"+ New"**
   - Select **"Database"**
   - Choose **"PostgreSQL"**

2. **Database will be provisioned:**
   - Takes ~30 seconds
   - Automatically creates database credentials
   - Automatically sets environment variables

#### Via Railway CLI:

```bash
# Add PostgreSQL database
railway add postgres

# Verify database was added
railway service
# You should see both "Resume_Modifier" and "Postgres" services
```

### Step 2: Verify Database Environment Variables

Railway automatically creates these variables when you add PostgreSQL:

```bash
# Check variables for Postgres service
railway service  # Select "Postgres"
railway variables

# You should see:
# DATABASE_URL              - Internal URL (postgres.railway.internal)
# DATABASE_PUBLIC_URL       - External URL (proxy.rlwy.net)
# PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
```

**Important URLs:**
- **`DATABASE_URL`** (Internal): Used by Railway services internally
  - Format: `postgresql://user:pass@postgres.railway.internal:5432/railway`
  - ✅ Use this for deployed app
  
- **`DATABASE_PUBLIC_URL`** (External): Used for external connections
  - Format: `postgresql://user:pass@region.proxy.rlwy.net:PORT/railway`
  - ✅ Use this for local migrations

### Step 3: Link Database to Application Service

Railway should automatically link the database. Verify:

```bash
# Switch to your app service
railway service  # Select "Resume_Modifier"

# Check if DATABASE_URL exists
railway variables | grep DATABASE_URL

# If not present, manually add it:
railway variables set DATABASE_URL=$DATABASE_URL
```

---

## 🔐 Environment Variables Setup

### Step 1: Required Environment Variables

Create all environment variables for your application service:

```bash
# Switch to application service
railway service  # Select "Resume_Modifier"

# Set required variables
railway variables set OPENAI_API_KEY="sk-proj-YOUR-ACTUAL-KEY-HERE"
railway variables set JWT_SECRET="$(openssl rand -base64 32)"
railway variables set FLASK_SECRET_KEY="$(openssl rand -base64 32)"

# Set Flask configuration
railway variables set FLASK_APP="app.server"
railway variables set FLASK_ENV="production"
railway variables set FLASK_DEBUG="0"

# Port (Railway sets this automatically, but we can override)
railway variables set PORT="5001"
```

### Step 2: Google OAuth Configuration (If Using)

```bash
# Set Google OAuth variables
railway variables set GOOGLE_CLIENT_ID="your-google-client-id"
railway variables set GOOGLE_CLIENT_SECRET="your-google-client-secret"

# Update redirect URI for production
# Format: https://your-app-name.railway.app/auth/google/callback
railway variables set GOOGLE_REDIRECT_URI="https://your-app.railway.app/auth/google/callback"
```

**⚠️ Important:** Update Google Cloud Console OAuth settings:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to: APIs & Services → Credentials
3. Select your OAuth 2.0 Client ID
4. Add to "Authorized redirect URIs":
   - `https://your-app.railway.app/auth/google/callback`
   - `https://your-custom-domain.com/auth/google/callback` (if using custom domain)

### Step 3: Verify All Variables

```bash
# List all variables
railway variables

# Expected variables:
# ✅ DATABASE_URL
# ✅ OPENAI_API_KEY
# ✅ JWT_SECRET
# ✅ FLASK_SECRET_KEY
# ✅ FLASK_APP
# ✅ FLASK_ENV
# ✅ FLASK_DEBUG
# ✅ PORT
# ✅ GOOGLE_CLIENT_ID (optional)
# ✅ GOOGLE_CLIENT_SECRET (optional)
# ✅ GOOGLE_REDIRECT_URI (optional)
```

### Step 4: Environment Variables Best Practices

```bash
# Generate secure secrets
openssl rand -base64 32  # For JWT_SECRET
openssl rand -base64 32  # For FLASK_SECRET_KEY

# Verify no spaces or special characters
railway variables get JWT_SECRET

# Update variables if needed
railway variables set JWT_SECRET="new-value"

# Delete incorrect variables
railway variables unset WRONG_VARIABLE_NAME
```

---

## 🔄 Database Migration Strategy

### Understanding Railway Database URLs

**Critical Concept:**
- **Internal URL** (`postgres.railway.internal`): Only works inside Railway
- **Public URL** (`*.proxy.rlwy.net`): Works from anywhere

### Strategy 1: Automatic Migration on Deploy (Recommended)

#### Update `railway.toml`:

```toml
[build]
builder = "nixpacks"

[deploy]
# Run migrations before starting the app
startCommand = "flask db upgrade && python railway_start.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

**Advantages:**
- ✅ Migrations run automatically on every deploy
- ✅ Uses internal DATABASE_URL (faster)
- ✅ No manual intervention needed
- ✅ Ensures database is always up to date

**⚠️ Important:** Commit and push this change:
```bash
git add railway.toml
git commit -m "Add automatic database migration on deploy"
git push origin main
```

### Strategy 2: Manual Migration Using Script (Alternative)

Use the automated migration script we created:

```bash
# From your local machine, run migrations on Railway database
./scripts/railway_migrate.py upgrade

# Or using the bash version
./scripts/railway_migrate.sh upgrade

# Verify migration
./scripts/railway_migrate.py current
```

**When to use:**
- ✅ One-time migrations
- ✅ Testing migrations before deploy
- ✅ Troubleshooting migration issues

### Strategy 3: Pre-Deploy Migration Check

Create a migration verification script:

```bash
# Create scripts/check_migrations.sh
cat > scripts/check_migrations.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Checking database migrations..."

# Get public database URL
PUBLIC_URL=$(railway variables --service Postgres | grep DATABASE_PUBLIC_URL | ...)

# Check current version
export DATABASE_URL="$PUBLIC_URL"
CURRENT=$(flask db current 2>&1 | grep -o '[a-f0-9]\{12\}' | head -1)
HEAD=$(flask db heads 2>&1 | grep -o '[a-f0-9]\{12\}' | head -1)

if [ "$CURRENT" = "$HEAD" ]; then
    echo "✅ Database is up to date: $CURRENT"
    exit 0
else
    echo "⚠️  Database needs migration"
    echo "   Current: $CURRENT"
    echo "   Head: $HEAD"
    exit 1
fi
EOF

chmod +x scripts/check_migrations.sh
```

### Step-by-Step Initial Migration

**For first deployment:**

1. **Verify migration files exist:**
   ```bash
   ls -la migrations/versions/
   # Should see: e5218d5636ae_initial_migration_with_all_tables.py
   ```

2. **Run initial migration:**
   ```bash
   # Using automated script (recommended)
   ./scripts/railway_migrate.py upgrade
   
   # Or manually with public URL
   railway variables --service Postgres | grep DATABASE_PUBLIC_URL
   DATABASE_URL="postgresql://..." flask db upgrade
   ```

3. **Verify migration:**
   ```bash
   ./scripts/railway_migrate.py current
   # Expected: e5218d5636ae (head)
   
   ./scripts/railway_migrate.py history
   # Should show: <base> -> e5218d5636ae, initial migration with all tables
   ```

4. **Verify tables were created:**
   ```bash
   # Connect to database
   railway connect postgres
   
   # List tables
   \dt
   
   # Expected tables:
   # - users
   # - resumes
   # - job_descriptions
   # - user_sites
   # - resume_templates
   # - google_auths
   # - generated_documents
   # - alembic_version
   
   # Exit psql
   \q
   ```

---

## 🚀 Deployment & Testing

### Step 1: Trigger Initial Deployment

#### Via Git Push (Automatic):

```bash
# Make sure all changes are committed
git status

# Push to trigger deployment
git push origin main

# Railway will automatically:
# 1. Detect the push
# 2. Build the application
# 3. Run migrations (if configured in railway.toml)
# 4. Start the service
```

#### Via Railway CLI:

```bash
# Deploy current directory
railway up

# Monitor deployment
railway logs --tail
```

### Step 2: Monitor Deployment Progress

#### Via Railway Dashboard:

1. Go to your Railway project
2. Click on **"Resume_Modifier"** service
3. Click on **"Deployments"** tab
4. Watch the build logs in real-time

Look for these stages:
```
✅ Building (2-3 minutes)
   - Installing dependencies
   - Copying files
   - Setting up environment
   
✅ Deploying (30 seconds)
   - Running migrations (if configured)
   - Starting application
   
✅ Active
   - Health check passed
   - Service is live
```

#### Via Railway CLI:

```bash
# Watch logs
railway logs --tail

# Filter for errors
railway logs --tail | grep -i error

# Check specific deployment
railway logs --deployment <deployment-id>
```

### Step 3: Get Your Application URL

```bash
# Get the public URL
railway domain

# Or from dashboard:
# Go to Settings → Domains
# You'll see: https://your-app-name.railway.app
```

### Step 4: Test Deployment

#### Test 1: Health Check

```bash
# Get your app URL
APP_URL=$(railway domain)

# Test health endpoint
curl https://your-app-name.railway.app/health

# Expected response:
{
  "status": "healthy",
  "service": "Resume Editor API",
  "timestamp": "2025-10-26T...",
  "components": {
    "database": "connected",
    "openai": "configured"
  }
}
```

#### Test 2: API Documentation

```bash
# Access Swagger UI
open https://your-app-name.railway.app/apidocs

# Or test with curl
curl https://your-app-name.railway.app/apidocs | grep "Resume Editor API"
```

#### Test 3: User Registration

```bash
# Test user registration endpoint
curl -X POST https://your-app-name.railway.app/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Expected: 201 Created with user data
```

#### Test 4: Database Connection

```bash
# Test login (which requires database)
curl -X POST https://your-app-name.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Expected: 200 OK with JWT token
```

#### Test 5: AI Features (OpenAI Integration)

```bash
# Get JWT token first (from login response)
TOKEN="your-jwt-token-here"

# Test resume parsing
curl -X POST https://your-app-name.railway.app/api/pdfupload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample-resume.pdf"

# Expected: Parsed resume data
```

### Step 5: Verify Database Migrations

```bash
# Connect to Railway database
railway connect postgres

# Check alembic version
SELECT * FROM alembic_version;
# Expected: version_num = e5218d5636ae

# Check tables exist
\dt

# Check user table structure
\d users

# Exit
\q
```

---

## ⚙️ Post-Deployment Configuration

### Step 1: Configure Custom Domain (Optional)

#### Add Custom Domain in Railway:

```bash
# Via CLI
railway domain add yourdomain.com

# Or via Dashboard:
# Settings → Domains → Custom Domain → Add Domain
```

#### Configure DNS:

Add CNAME record in your DNS provider:
```
Type: CNAME
Name: @ (or subdomain like 'api')
Value: your-app-name.railway.app
TTL: 3600
```

#### Update Environment Variables:

```bash
# Update Google OAuth redirect URI
railway variables set GOOGLE_REDIRECT_URI="https://yourdomain.com/auth/google/callback"
```

### Step 2: Enable HTTPS (Automatic)

Railway provides automatic SSL certificates:
- ✅ Free SSL/TLS certificates via Let's Encrypt
- ✅ Automatic renewal
- ✅ HTTPS enforced by default

Verify HTTPS:
```bash
curl -I https://your-app-name.railway.app/health
# Look for: HTTP/2 200
```

### Step 3: Configure Health Checks

Railway uses the `healthcheckPath` from `railway.toml`:

```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
```

Monitor health check status:
```bash
# Via CLI
railway status

# Via Dashboard
# Service → Deployments → Active Deployment → Health
```

### Step 4: Set Up Logging

Configure log retention and monitoring:

```bash
# View recent logs
railway logs --tail --lines 100

# Filter logs
railway logs --tail | grep ERROR

# Export logs
railway logs --lines 1000 > deployment_logs.txt
```

### Step 5: Configure Restart Policy

Already configured in `railway.toml`:

```toml
[deploy]
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

This means Railway will:
- Automatically restart if app crashes
- Try up to 3 times before marking as failed
- Wait progressively longer between retries

---

## 📊 Monitoring & Maintenance

### Monitoring Metrics

#### Via Railway Dashboard:

1. **Service Overview:**
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

2. **Deployment History:**
   - Success/failure rates
   - Build times
   - Deployment frequency

3. **Database Metrics:**
   - Connection count
   - Database size
   - Query performance

#### Via Railway CLI:

```bash
# Get service metrics
railway status

# Monitor resource usage
railway logs --tail | grep -E "CPU|Memory|Request"
```

### Database Backups

#### Automatic Backups:

Railway automatically backs up PostgreSQL databases:
- ✅ Daily automated backups
- ✅ 7-day retention on free tier
- ✅ Point-in-time recovery available

#### Manual Backup:

```bash
# Get database public URL
railway variables --service Postgres | grep DATABASE_PUBLIC_URL

# Create backup
pg_dump "postgresql://user:pass@host:port/railway" > backup_$(date +%Y%m%d).sql

# Or via Railway CLI
railway connect postgres -- pg_dump railway > backup.sql
```

#### Restore from Backup:

```bash
# Restore to Railway database
psql "$(railway variables --service Postgres | grep DATABASE_PUBLIC_URL | ...)" < backup.sql
```

### Application Updates

#### Deployment Workflow:

```bash
# 1. Make changes locally
git add .
git commit -m "Feature: Add new endpoint"

# 2. Test locally
python railway_start.py
# Test thoroughly

# 3. Run tests
pytest app/tests/ -v

# 4. Create migration if needed
flask db migrate -m "Add new column"
flask db upgrade  # Test locally

# 5. Push to deploy
git push origin main

# 6. Monitor deployment
railway logs --tail

# 7. Verify deployment
curl https://your-app-name.railway.app/health
```

### Rollback Strategy

#### Rollback to Previous Deployment:

```bash
# Via Dashboard:
# Service → Deployments → Select previous deployment → "Redeploy"

# Via CLI (requires deployment ID)
railway redeploy <deployment-id>
```

#### Rollback Database Migration:

```bash
# Check current version
./scripts/railway_migrate.py current

# View history
./scripts/railway_migrate.py history

# Rollback one version
./scripts/railway_migrate.py downgrade

# Verify
./scripts/railway_migrate.py current
```

### Performance Optimization

#### Monitor Slow Endpoints:

```bash
# Add timing logs to your application
# Check logs for slow requests
railway logs --tail | grep "duration"
```

#### Database Query Optimization:

```bash
# Connect to database
railway connect postgres

# Check slow queries (if pg_stat_statements enabled)
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

#### Scale Resources (Paid Plans):

```bash
# Via Dashboard:
# Service → Settings → Resources
# Adjust CPU/Memory allocation
```

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Deployment Fails to Build

**Symptoms:**
```
ERROR: Could not install packages
Build failed
```

**Solutions:**
```bash
# 1. Check requirements.txt format
cat requirements.txt | grep -E "^[^#]"

# 2. Verify Python version compatibility
# Edit railway.toml or add runtime.txt
echo "python-3.12" > runtime.txt

# 3. Check build logs for specific package errors
railway logs --deployment <id> | grep ERROR

# 4. Try local build
pip install -r requirements.txt

# 5. Update problematic packages
pip install --upgrade package-name
pip freeze > requirements.txt
```

#### Issue 2: Database Connection Failed

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not translate host name
Connection refused
```

**Solutions:**
```bash
# 1. Verify DATABASE_URL is set
railway variables | grep DATABASE_URL

# 2. Check if Postgres service is running
railway service  # Select Postgres
railway logs --tail

# 3. Test connection
railway connect postgres
# If this works, the database is fine

# 4. Verify internal URL is used in production
railway variables get DATABASE_URL
# Should contain: postgres.railway.internal

# 5. Check if migration ran
./scripts/railway_migrate.py current
```

#### Issue 3: Health Check Failing

**Symptoms:**
```
Health check timeout
Service marked as unhealthy
```

**Solutions:**
```bash
# 1. Test health endpoint
curl https://your-app-name.railway.app/health

# 2. Check if app is starting correctly
railway logs --tail | grep "Starting"

# 3. Verify health check path in railway.toml
cat railway.toml | grep healthcheck

# 4. Increase timeout if needed
# Edit railway.toml:
healthcheckTimeout = 600  # 10 minutes

# 5. Check application logs for errors
railway logs --tail | grep -i error
```

#### Issue 4: Migration Errors

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision
Migration failed
```

**Solutions:**
```bash
# 1. Check migration files exist
ls -la migrations/versions/

# 2. Verify current database version
./scripts/railway_migrate.py current

# 3. Check migration history
./scripts/railway_migrate.py history

# 4. Stamp database if needed (CAREFUL!)
# This marks database as current without running migrations
./scripts/railway_migrate.py stamp

# 5. If corrupt, reset migrations (LAST RESORT)
# Backup data first!
# Drop all tables and re-run initial migration
```

#### Issue 5: Environment Variable Not Loading

**Symptoms:**
```
KeyError: 'OPENAI_API_KEY'
Configuration missing
```

**Solutions:**
```bash
# 1. List all variables
railway variables

# 2. Verify variable is set for correct service
railway service  # Select "Resume_Modifier"
railway variables get OPENAI_API_KEY

# 3. Check for typos in variable names
# Variables are case-sensitive!

# 4. Redeploy after setting variables
railway up

# 5. Test variable in Railway shell
railway shell
echo $OPENAI_API_KEY
```

#### Issue 6: OpenAI API Errors

**Symptoms:**
```
openai.error.AuthenticationError
Invalid API key
```

**Solutions:**
```bash
# 1. Verify API key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 2. Check for extra spaces or newlines
railway variables get OPENAI_API_KEY | od -c

# 3. Regenerate API key from OpenAI dashboard
# Update in Railway:
railway variables set OPENAI_API_KEY="sk-proj-NEW-KEY"

# 4. Check API usage/quota
# Visit: https://platform.openai.com/account/usage

# 5. Verify API key format
# Should start with: sk-proj-
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Temporarily enable debug mode
railway variables set FLASK_DEBUG="1"
railway variables set FLASK_ENV="development"

# Watch detailed logs
railway logs --tail

# Remember to disable after debugging
railway variables set FLASK_DEBUG="0"
railway variables set FLASK_ENV="production"
```

---

## 🔄 CI/CD & Automation

### GitHub Actions Integration

Create `.github/workflows/railway-deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        JWT_SECRET: test-secret
        FLASK_SECRET_KEY: test-secret
      run: |
        pytest app/tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install Railway CLI
      run: npm i -g @railway/cli
    
    - name: Deploy to Railway
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      run: |
        railway up --detach
        echo "Deployed to Railway!"
```

### Setup GitHub Secrets:

```bash
# Get Railway token
railway login
railway token

# Add to GitHub:
# Settings → Secrets and variables → Actions
# New repository secret:
# Name: RAILWAY_TOKEN
# Value: <your-railway-token>

# Add OpenAI key for tests
# Name: OPENAI_API_KEY
# Value: <your-openai-key>
```

### Pre-Commit Hooks

Create `.githooks/pre-commit`:

```bash
#!/bin/bash

echo "🔍 Running pre-commit checks..."

# Run tests
pytest app/tests/ -v
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted."
    exit 1
fi

# Check code formatting
black --check app/
if [ $? -ne 0 ]; then
    echo "❌ Code formatting issues. Run: black app/"
    exit 1
fi

# Check for migrations
if git diff --cached --name-only | grep -q "app/models/"; then
    echo "⚠️  Models changed. Did you create a migration?"
    echo "Run: flask db migrate -m 'description'"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed!"
```

Setup:
```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

---

## 🔒 Security Best Practices

### Environment Variables Security

```bash
# ✅ DO: Use secure, random secrets
openssl rand -base64 32

# ❌ DON'T: Use predictable values
# JWT_SECRET="secret123"

# ✅ DO: Rotate secrets regularly
railway variables set JWT_SECRET="$(openssl rand -base64 32)"

# ✅ DO: Use different secrets per environment
# Production: Strong secret
# Staging: Different strong secret
# Development: Simple secret (local only)

# ❌ DON'T: Commit secrets to Git
grep -r "sk-proj-" .  # Check for exposed keys
git secrets --scan  # Use git-secrets tool
```

### Database Security

```bash
# ✅ DO: Use strong database passwords
railway variables --service Postgres | grep PGPASSWORD

# ✅ DO: Limit database access
# Railway automatically restricts to internal network

# ✅ DO: Regular backups
# Setup automated backup script

# ✅ DO: Monitor database access
railway logs --tail | grep "database"

# ❌ DON'T: Use public URL in production
# Only use DATABASE_PUBLIC_URL for local migrations
```

### API Security

```python
# ✅ DO: Rate limiting (add to app)
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ✅ DO: Input validation
from marshmallow import Schema, fields, validate

# ✅ DO: HTTPS only
@app.before_request
def before_request():
    if not request.is_secure and app.env == "production":
        return redirect(request.url.replace("http://", "https://"))
```

### Monitoring Security

```bash
# Setup security monitoring
# 1. Monitor failed login attempts
railway logs --tail | grep "login.*failed"

# 2. Monitor API errors
railway logs --tail | grep -E "401|403|500"

# 3. Setup alerts (via Railway Dashboard)
# Settings → Notifications → Add Alert
# Condition: Error rate > threshold
```

### Security Checklist

- [ ] All secrets use random, cryptographically secure values
- [ ] No secrets committed to Git repository
- [ ] HTTPS enforced for all endpoints
- [ ] Database uses strong password
- [ ] Database access restricted to internal network
- [ ] JWT tokens expire (add expiration logic)
- [ ] Input validation on all endpoints
- [ ] Rate limiting enabled
- [ ] Security headers configured (CORS, CSP)
- [ ] Regular dependency updates
- [ ] Error messages don't leak sensitive info
- [ ] Logging doesn't include passwords/tokens
- [ ] API keys rotated regularly
- [ ] Backup strategy in place

---

## 📝 Quick Reference Commands

### Railway CLI Cheat Sheet

```bash
# Project Management
railway init                    # Initialize new project
railway link                    # Link to existing project
railway unlink                  # Unlink from project
railway status                  # Show project status

# Service Management
railway service                 # Select service
railway add postgres            # Add PostgreSQL database
railway add redis               # Add Redis

# Deployment
railway up                      # Deploy current directory
railway up --detach             # Deploy in background
railway logs --tail             # Watch deployment logs
railway logs --deployment <id>  # View specific deployment

# Environment Variables
railway variables               # List all variables
railway variables set KEY=value # Set variable
railway variables get KEY       # Get variable value
railway variables unset KEY     # Delete variable

# Database
railway connect postgres        # Connect to PostgreSQL
railway run psql $DATABASE_URL  # Run psql

# Domains
railway domain                  # Show current domain
railway domain add example.com  # Add custom domain

# Shell Access
railway shell                   # Open shell in Railway environment
railway run <command>           # Run command in Railway environment

# Utilities
railway whoami                  # Show current user
railway logout                  # Logout
railway --help                  # Show help
```

### Database Migration Commands

```bash
# Local migrations
flask db migrate -m "description"  # Create migration
flask db upgrade                   # Apply migrations
flask db downgrade                 # Rollback migration
flask db current                   # Show current version
flask db history                   # Show migration history
flask db stamp head                # Mark as current

# Railway migrations (using scripts)
./scripts/railway_migrate.py upgrade    # Apply migrations
./scripts/railway_migrate.py current    # Show current version
./scripts/railway_migrate.py history    # Show history
./scripts/railway_migrate.py downgrade  # Rollback
```

### Testing Commands

```bash
# Run tests
pytest app/tests/ -v                    # All tests with verbose
pytest app/tests/ -v -k test_name       # Specific test
pytest app/tests/ --cov=app             # With coverage
pytest app/tests/ --tb=short            # Short traceback

# API testing
curl https://app.railway.app/health     # Health check
curl https://app.railway.app/apidocs    # API docs
```

---

## 🎯 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally (`pytest app/tests/ -v`)
- [ ] Database migrations created and tested
- [ ] Environment variables documented
- [ ] `Procfile` configured correctly
- [ ] `railway.toml` configured correctly
- [ ] `requirements.txt` up to date
- [ ] Repository pushed to GitHub
- [ ] Google OAuth configured (if using)
- [ ] OpenAI API key obtained

### During Deployment

- [ ] Railway project created
- [ ] PostgreSQL database added
- [ ] All environment variables set
- [ ] Database migrations run successfully
- [ ] Deployment completed without errors
- [ ] Health check passing

### Post-Deployment

- [ ] Application accessible via URL
- [ ] API documentation available (`/apidocs`)
- [ ] Database connection working
- [ ] User registration works
- [ ] User login works
- [ ] OpenAI integration works
- [ ] Google OAuth works (if configured)
- [ ] Custom domain configured (if needed)
- [ ] Monitoring/logging configured
- [ ] Backup strategy in place

---

## 📚 Additional Resources

### Official Documentation
- [Railway Documentation](https://docs.railway.app/)
- [Railway CLI Guide](https://docs.railway.app/develop/cli)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

### Project Documentation
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- [RAILWAY_MIGRATION_GUIDE.md](./RAILWAY_MIGRATION_GUIDE.md)
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- [Database Best Practices](./docs/DATABASE_BEST_PRACTICES.md)

### Support
- [Railway Community Discord](https://discord.gg/railway)
- [Railway Status Page](https://status.railway.app/)
- [GitHub Issues](https://github.com/Andrlulu/Resume_Modifier/issues)

---

## 🎉 Conclusion

You now have a **complete, production-ready deployment** of the Resume Modifier backend on Railway!

### What You've Accomplished:

✅ **Deployed a Flask application** with PostgreSQL database  
✅ **Configured environment variables** securely  
✅ **Set up database migrations** with multiple strategies  
✅ **Enabled health monitoring** and automatic restarts  
✅ **Implemented best practices** for security and performance  
✅ **Created automation tools** for easier management  
✅ **Established monitoring** and maintenance procedures  

### Next Steps:

1. **Monitor your application** using Railway dashboard
2. **Set up CI/CD** using GitHub Actions
3. **Configure custom domain** for production use
4. **Implement rate limiting** for API endpoints
5. **Set up error tracking** (e.g., Sentry)
6. **Regular backups** and maintenance

---

**🚀 Your Resume Modifier backend is live and ready to help users optimize their resumes!**

For questions or issues, refer to the [Troubleshooting Guide](#-troubleshooting-guide) or create an issue on GitHub.

**Happy Deploying! 🎉**
