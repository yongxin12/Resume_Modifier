# 🚄 Railway Deployment Guide for Resume Modifier

This guide provides step-by-step instructions for deploying the Resume Modifier application to Railway.

## 🚀 Quick Deploy Button

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?referrer=github)

---

## 📋 Prerequisites

- ✅ Railway account at [railway.app](https://railway.app)
- ✅ GitHub account with access to this repository
- ✅ OpenAI API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)

---

## 🛤️ Step-by-Step Deployment

### Step 1: Prepare Repository

1. **Fork the Repository**
   ```bash
   # Go to https://github.com/Andrlulu/Resume_Modifier
   # Click "Fork" button
   # Clone your fork locally
   git clone https://github.com/YOUR_USERNAME/Resume_Modifier.git
   cd Resume_Modifier
   ```

2. **Optional: Customize Configuration**
   - Review `railway.toml` for any needed changes
   - Ensure `Procfile` is present and correct
   - Verify `requirements.txt` is up to date

### Step 2: Create Railway Project

1. **Sign up/Login to Railway**
   - Visit [railway.app](https://railway.app)
   - Sign up or login with GitHub

2. **Create New Project**
   ```
   Dashboard → "New Project" → "Deploy from GitHub repo"
   ```

3. **Connect Repository**
   - Select your forked `Resume_Modifier` repository
   - Railway will automatically detect it as a Python project

### Step 3: Add Database

1. **Add PostgreSQL Service**
   ```
   Project Dashboard → "New" → "Database" → "Add PostgreSQL"
   ```

2. **Verify Database Connection**
   - Railway automatically creates `DATABASE_URL` environment variable
   - This connects your app to the PostgreSQL instance

### Step 4: Configure Environment Variables

In your Railway project dashboard, go to **Variables** tab and add:

```bash
# Required Variables
OPENAI_API_KEY=sk-proj-YOUR-ACTUAL-OPENAI-KEY-HERE
JWT_SECRET=your-super-secure-production-jwt-secret-key

# Flask Configuration
FLASK_APP=app.server
FLASK_ENV=production
FLASK_DEBUG=0

# Port Configuration (Railway automatically sets PORT)
PORT=5001
```

#### Important Notes:
- **OPENAI_API_KEY**: Get from [OpenAI Platform](https://platform.openai.com/account/api-keys)
- **JWT_SECRET**: Generate a secure random string (use `openssl rand -base64 32`)
- **DATABASE_URL**: Automatically set by Railway PostgreSQL service

### Step 5: Deploy

1. **Trigger Deployment**
   - Railway automatically builds and deploys on code push
   - Watch the build logs in Railway dashboard
   - Deployment typically takes 2-3 minutes

2. **Monitor Build Process**
   ```
   Railway Dashboard → Your Project → "Deployments" tab
   ```

### Step 6: Post-Deployment Setup

1. **Run Database Migrations**
   
   **⚠️ Important: Railway provides two database URLs:**
   - `DATABASE_URL` (internal): Only works **within Railway's network**
   - `DATABASE_PUBLIC_URL` (external): Works from **your local machine**
   
   **Option A: Run Locally (Recommended)**
   ```bash
   # Get the public database URL
   railway service  # Select "Postgres"
   railway variables --service Postgres | grep DATABASE_PUBLIC_URL
   
   # Run migration with the public URL
   DATABASE_URL="postgresql://user:pass@shinkansen.proxy.rlwy.net:PORT/railway" flask db upgrade
   ```
   
   **Option B: Automatic Migration on Deploy**
   
   Update your `Procfile`:
   ```
   release: flask db upgrade
   web: python -m app.server
   ```
   
   Or update `railway.toml`:
   ```toml
   [deploy]
   startCommand = "flask db upgrade && python -m app.server"
   ```
   
   **Option C: Use Railway Shell**
   ```bash
   railway shell
   flask db upgrade
   exit
   ```
   
   > 📖 For detailed troubleshooting, see [RAILWAY_MIGRATION_GUIDE.md](./RAILWAY_MIGRATION_GUIDE.md)

2. **Verify Deployment**
   ```bash
   # Get your Railway app URL from dashboard
   curl https://your-app-name.railway.app/health
   
   # Should return:
   {
     "status": "healthy",
     "service": "Resume Editor API",
     "timestamp": "...",
     "components": {
       "database": "connected",
       "openai": "configured"
     }
   }
   ```

3. **Access API Documentation**
   ```
   https://your-app-name.railway.app/apidocs
   ```

---

## 🔧 Railway Configuration Files

### `railway.toml`
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python -m app.server"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[environments.production]
[environments.production.variables]
FLASK_ENV = "production"
FLASK_DEBUG = "0"
PORT = "5001"
```

### `Procfile`
```
web: python -m app.server
```

---

## 🌐 Custom Domain Setup

1. **Add Custom Domain**
   ```
   Railway Dashboard → Your Project → Settings → Domains
   ```

2. **Configure DNS**
   - Add CNAME record pointing to Railway's domain
   - Railway provides SSL certificates automatically

---

## 📊 Monitoring and Management

### Railway Dashboard Features

1. **Metrics Monitoring**
   - CPU and memory usage
   - Request/response metrics
   - Error rates and logs

2. **Log Management**
   ```bash
   # View logs via Railway CLI
   railway logs --tail
   
   # Filter by service
   railway logs --tail --service web
   ```

3. **Environment Management**
   - Manage variables securely
   - Different environments (staging, production)

### Database Management

1. **Connect to Database**
   ```bash
   # Using Railway CLI
   railway connect postgres
   
   # Using psql directly
   railway run psql $DATABASE_URL
   ```

2. **Database Backups**
   - Railway automatically handles backups
   - Manual backup: `railway run pg_dump $DATABASE_URL > backup.sql`

---

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs in Railway dashboard
   # Common issues:
   # - Missing dependencies in requirements.txt
   # - Python version compatibility
   # - Environment variable issues
   ```

2. **Database Connection Issues**
   ```bash
   # ⚠️ Error: "could not translate host name postgres.railway.internal"
   # This means you're using the INTERNAL database URL from your local machine
   
   # Solution: Use DATABASE_PUBLIC_URL instead
   railway variables --service Postgres | grep DATABASE_PUBLIC_URL
   DATABASE_URL="<public-url-here>" flask db upgrade
   
   # Test database connection
   railway connect postgres
   ```

3. **OpenAI API Issues**
   ```bash
   # Verify API key is set correctly
   railway variables get OPENAI_API_KEY
   
   # Test OpenAI connection
   railway run python -c "import openai; print('OpenAI OK')"
   ```

### Debug Commands

```bash
# View current deployment status
railway status

# Check environment variables
railway variables

# View recent logs
railway logs --tail --lines 100

# Connect to database
railway connect postgres

# Run database migrations
railway run flask db upgrade

# Test health endpoint
curl https://your-app-name.railway.app/health
```

---

## 🔄 Continuous Deployment

### Automatic Deployments

Railway automatically deploys when you push to your connected GitHub branch:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Railway automatically:
# 1. Detects the push
# 2. Builds the new version
# 3. Runs tests (if configured)
# 4. Deploys if successful
```

### Deployment Hooks

Configure webhooks in Railway dashboard:
- Pre-deploy hooks
- Post-deploy notifications
- Integration with Slack, Discord, etc.

---

## 📈 Scaling and Performance

### Railway Scaling

1. **Automatic Scaling**
   - Railway scales based on CPU and memory usage
   - Configure scaling policies in dashboard

2. **Manual Scaling**
   ```
   Railway Dashboard → Your Service → Settings → Resources
   ```

3. **Performance Optimization**
   - Monitor resource usage
   - Optimize database queries
   - Implement caching strategies

---

## 🔐 Security Best Practices

### Environment Variables
- Never commit secrets to code
- Use Railway's secure variable storage
- Rotate JWT secrets regularly
- Monitor API key usage

### Database Security
- Railway handles database security
- Use strong passwords
- Monitor database access logs
- Regular backups and recovery testing

---

## 📞 Support and Resources

### Railway Resources
- [Railway Documentation](https://docs.railway.app/)
- [Railway Community Discord](https://discord.gg/railway)
- [Railway Status Page](https://status.railway.app/)

### Project Resources
- [GitHub Repository](https://github.com/Andrlulu/Resume_Modifier)
- [API Documentation](./API_DOCUMENTATION.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)

### Getting Help
1. Check Railway dashboard for error logs
2. Review this guide for common solutions
3. Check GitHub issues for known problems
4. Create new issue with detailed error information

---

## 🎯 Next Steps

After successful deployment:

1. **Test All Features**
   - User registration/login
   - PDF upload and parsing
   - Resume scoring
   - Export functionality

2. **Set Up Monitoring**
   - Configure alerting for errors
   - Monitor performance metrics
   - Set up uptime monitoring

3. **Plan for Growth**
   - Monitor usage patterns
   - Plan for scaling needs
   - Consider additional features

---

**🎉 Congratulations! Your Resume Modifier is now live on Railway!**

Your application should be accessible at: `https://your-app-name.railway.app`

Happy coding! 🚀