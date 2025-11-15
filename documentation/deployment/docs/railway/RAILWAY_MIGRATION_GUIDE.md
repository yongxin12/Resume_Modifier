# 🚄 Railway Database Migration Guide

## Problem Overview

When trying to run `railway run flask db upgrade` locally, you may encounter:

```
psycopg2.OperationalError: could not translate host name "postgres.railway.internal" to address: Name or service not known
```

### Root Cause

Railway provides **two database URLs**:

1. **`DATABASE_URL`** (Internal): `postgresql://...@postgres.railway.internal:5432/railway`
   - Only accessible **within Railway's network**
   - Used by deployed applications running on Railway
   - **NOT accessible from your local machine**

2. **`DATABASE_PUBLIC_URL`** (External): `postgresql://...@shinkansen.proxy.rlwy.net:52352/railway`
   - Accessible from **anywhere** (including your local machine)
   - Used for remote connections, local development, and CLI operations
   - **Required for local database migrations**

---

## ✅ Solutions

### **Solution 1: Use Public URL for Local Migration (Recommended)**

Run migrations locally using Railway's public database URL:

```bash
# Get the public URL
railway variables --service Postgres | grep DATABASE_PUBLIC_URL

# Run migration with public URL
DATABASE_URL="postgresql://postgres:PASSWORD@shinkansen.proxy.rlwy.net:PORT/railway" flask db upgrade
```

**Step-by-step:**

```bash
# 1. Switch to Postgres service to get credentials
railway service

# 2. Get the public database URL
railway variables --service Postgres | grep DATABASE_PUBLIC_URL

# 3. Copy the DATABASE_PUBLIC_URL value and run:
DATABASE_URL="<paste-public-url-here>" flask db upgrade
DATABASE_URL="postgresql://postgres:IEAChRNbxjHiLfxsFfoodmTWgxFDxSmV@shinkansen.proxy.rlwy.net:52352/railway" flask db upgrade
```

### **Solution 2: Trigger Migration via Railway Deployment**

Let Railway run migrations automatically during deployment:

#### Option A: Update Procfile

Add a release command to `Procfile`:

```
release: flask db upgrade
web: python -m app.server
```

#### Option B: Update railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "flask db upgrade && python -m app.server"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

#### Option C: Create a One-Time Job

```bash
# Deploy and trigger migration in a single step
railway up --service Resume_Modifier

# Or create a one-time deployment job
railway run --detach flask db upgrade
```

### **Solution 3: Use Railway Shell (Interactive)**

Connect to Railway's environment and run migrations there:

```bash
# Open a shell in Railway's environment
railway shell

# Inside the Railway shell:
flask db upgrade
exit
```

---

## 🔧 Permanent Local Development Setup

To avoid this issue in the future, create a separate `.env.local` file:

### 1. Create `.env.local`

```bash
# .env.local - Use Railway's public database for local development

# Railway Public Database URL (get from: railway variables --service Postgres)
DATABASE_URL=postgresql://postgres:PASSWORD@shinkansen.proxy.rlwy.net:PORT/railway

# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-YOUR-KEY

# Flask Configuration
FLASK_SECRET_KEY=your_flask_secret_key_here
JWT_SECRET=your_super_secure_jwt_secret_key_for_production
FLASK_APP=app.server
FLASK_ENV=development
FLASK_DEBUG=1

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5001/auth/google/callback
```

### 2. Update `.gitignore`

```bash
echo ".env.local" >> .gitignore
```

### 3. Use `.env.local` for Local Development

```bash
# Load .env.local instead of .env
source .env.local

# Or export manually
export $(grep -v '^#' .env.local | xargs)

# Then run migrations
flask db upgrade
```

---

## 📋 Quick Reference Commands

### Get Railway Database URLs

```bash
# List all services
railway service

# View Postgres variables
railway variables --service Postgres

# Get public URL only
railway variables --service Postgres | grep DATABASE_PUBLIC_URL
```

### Run Migrations

```bash
# Local with public URL
DATABASE_URL="<public-url>" flask db upgrade

# Via Railway shell
railway shell
flask db upgrade

# Check migration status
DATABASE_URL="<public-url>" flask db current

# View migration history
DATABASE_URL="<public-url>" flask db history
```

### Database Connection Test

```bash
# Test connection using public URL
psql "postgresql://postgres:PASSWORD@shinkansen.proxy.rlwy.net:PORT/railway"

# Or using Railway CLI
railway connect postgres
```

---

## 🔐 Security Best Practices

### ⚠️ Important Security Notes

1. **Never commit database credentials** to version control
2. **Rotate database passwords** regularly
3. **Use environment variables** for all sensitive data
4. **Restrict public database access** to trusted IP addresses (if possible)

### Update Railway Variables

```bash
# Add new environment variable
railway variables set KEY=value

# Remove variable
railway variables unset KEY

# View all variables
railway variables
```

---

## 🐛 Troubleshooting

### Issue: "Name or service not known"

**Symptom:** `could not translate host name "postgres.railway.internal"`

**Solution:** You're using the internal URL locally. Use `DATABASE_PUBLIC_URL` instead.

### Issue: "Connection timeout"

**Symptom:** Database connection times out

**Solutions:**
1. Check if Railway's public proxy is reachable:
   ```bash
   ping shinkansen.proxy.rlwy.net
   ```
2. Verify firewall/network settings
3. Check Railway service status: https://status.railway.app

### Issue: "Password authentication failed"

**Symptom:** Authentication error when connecting

**Solutions:**
1. Verify password from Railway variables:
   ```bash
   railway variables --service Postgres | grep PGPASSWORD
   ```
2. Ensure no extra spaces or characters in connection string
3. Check if password was recently rotated

### Issue: Migration runs but no changes

**Symptom:** `No changes in schema detected`

**Solution:** This is expected if models match current database state. To force a new migration:
```bash
flask db revision -m "description of changes"
flask db upgrade
```

---

## 📊 Comparison: Internal vs Public URLs

| Feature | Internal URL | Public URL |
|---------|-------------|------------|
| **Hostname** | `postgres.railway.internal` | `shinkansen.proxy.rlwy.net` |
| **Port** | `5432` (PostgreSQL default) | `52352` (Railway proxy port) |
| **Accessible from** | Railway services only | Anywhere with internet |
| **Use case** | Production deployments | Local dev, migrations, CLI |
| **Security** | Internal network only | Public (password protected) |
| **Performance** | Faster (direct connection) | Slower (proxy overhead) |

---

## 🚀 Recommended Workflow

### For Local Development:

1. Use `DATABASE_PUBLIC_URL` in local `.env.local`
2. Run migrations locally before pushing code
3. Test changes with local database connection
4. Push to Railway when ready

### For Production Deployment:

1. Push code to GitHub
2. Railway auto-deploys with `DATABASE_URL` (internal)
3. Migrations run automatically (if configured in Procfile/railway.toml)
4. Verify deployment health check

---

## 📞 Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)

---

**✅ Migration Complete!**

Your database schema is now up to date on Railway's PostgreSQL instance.
