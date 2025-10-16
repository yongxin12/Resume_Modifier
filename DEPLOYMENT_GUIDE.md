# 🚀 Resume Editor Deployment & Setup Guide

## 📋 Prerequisites

### For Local Development
- 🐳 Docker and Docker Compose installed
- 🔑 OpenAI API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)
- 💻 Python 3.12+ (optional, for non-Docker development)

### For Railway Deployment
- 🚄 Railway account at [railway.app](https://railway.app)
- 🔑 OpenAI API key
- 📱 GitHub account (for repository connection)

---

## ⚡ Railway Deployment (Recommended for Production)

### Step 1: Prepare Your Repository
1. **Fork or Clone**
   ```bash
   git clone https://github.com/Andrlulu/Resume_Modifier.git
   cd Resume_Modifier
   ```

2. **Push to Your GitHub** (if cloned)
   ```bash
   git remote set-url origin https://github.com/YOUR_USERNAME/Resume_Modifier.git
   git push -u origin main
   ```

### Step 2: Deploy to Railway
1. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Resume_Modifier repository

2. **Add PostgreSQL Database**
   - In Railway dashboard, click "New" → "Database" → "PostgreSQL"
   - Railway automatically provisions and connects the database
   - Note: DATABASE_URL is automatically set

3. **Configure Environment Variables**
   Go to your Railway project → Variables tab and add:
   ```bash
   OPENAI_API_KEY=sk-proj-YOUR-ACTUAL-OPENAI-KEY-HERE
   JWT_SECRET=your-super-secure-production-jwt-secret-key
   FLASK_APP=app.server
   FLASK_ENV=production
   FLASK_DEBUG=0
   PORT=5001
   ```

4. **Deploy**
   - Railway automatically builds and deploys your app
   - Check deployment logs in Railway dashboard
   - Get your app URL: `https://your-app-name.railway.app`

### Step 3: Verify Deployment
```bash
# Test health endpoint
curl https://your-app-name.railway.app/health

# Access API documentation
# Visit: https://your-app-name.railway.app/apidocs
```

### Railway Configuration Files
The repository includes:
- `railway.toml` - Railway-specific configuration
- `Procfile` - Process definition for deployment
- `requirements.txt` - Python dependencies

---

## 🐳 Local Development Setup

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/Andrlulu/Resume_Modifier.git
cd Resume_Modifier

# Copy environment template
cp .env.example .env
```

### Step 2: Configure Environment
Edit `.env` file with your credentials:
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# Database Configuration (Docker will handle this)
DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_app

# JWT Security
JWT_SECRET=your-super-secure-jwt-secret-key

# Flask Configuration
FLASK_APP=app.server
FLASK_ENV=development
FLASK_DEBUG=1
```

### Step 3: Start with Docker Compose
```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f web

# Check service status
docker compose ps
```

### Step 4: Verify Local Installation
```bash
# Test health endpoint
curl http://localhost:5001/health

# Expected response:
{
  "status": "healthy",
  "service": "Resume Editor API",
  "timestamp": "2025-10-16T10:30:00.000Z",
  "components": {
    "database": "connected",
    "openai": "configured"
  }
}

# Access interactive API documentation
open http://localhost:5001/apidocs
```

### Step 5: Database Setup (Automatic)
The application automatically handles database initialization:
- Creates tables on first run
- Runs migrations
- Seeds initial data (templates)

### Step 6: Test the Application
```bash
# Run the test suite (100% coverage)
docker compose exec web pytest app/tests/ -v

# Run manual API tests
python test_api.py
```

---

## Architecture

### Service Components

```
┌─────────────────────────────────────────┐
│         Resume Editor API               │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Flask Application (Port 5001)  │  │
│  │   - API Endpoints                │  │
│  │   - JWT Authentication           │  │
│  │   - Swagger Documentation        │  │
│  └──────────────────────────────────┘  │
│              │                          │
│              ▼                          │
│  ┌──────────────────────────────────┐  │
│  │   AI Services (OpenAI)           │  │
│  │   - Resume Parsing               │  │
│  │   - Analysis                     │  │
│  │   - Scoring                      │  │
│  └──────────────────────────────────┘  │
│              │                          │
│              ▼                          │
│  ┌──────────────────────────────────┐  │
│  │   PostgreSQL Database            │  │
│  │   - User data                    │  │
│  │   - Resume storage               │  │
│  │   - Job descriptions             │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Database Schema

**Users Table:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(100),
    country VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Resumes Table:**
```sql
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    serial_number INTEGER,
    title VARCHAR(200),
    parsed_resume JSONB,
    template INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## API Endpoints Overview

### Public Endpoints (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| POST | `/api/register` | User registration |
| POST | `/api/login` | User login |
| POST | `/api/pdfupload` | Upload and parse PDF resume |
| POST | `/api/job_description_upload` | Analyze resume with job description |
| POST | `/api/resume/score` | Score resume with AI analysis |

### Protected Endpoints (Require JWT Token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT | `/api/save_resume` | Save/update resume |
| GET | `/api/get_resume_list` | Get user's resume list |
| GET | `/api/get_resume/<id>` | Get specific resume |
| PUT | `/api/put_profile` | Update user profile |
| GET | `/api/get_profile` | Get user profile |

---

## New Features Implemented

### 1. Health Check Endpoint (`/health`)
- ✅ Verifies database connectivity
- ✅ Checks OpenAI API configuration
- ✅ Returns service status and timestamp
- ✅ Used for monitoring and deployment verification

### 2. Swagger/OpenAPI Documentation
- ✅ Integrated Flasgger for automatic API documentation
- ✅ Interactive API explorer at `/apidocs`
- ✅ Complete endpoint specifications
- ✅ Request/response examples
- ✅ Authentication documentation

### 3. Resume Scoring Endpoint (`/api/resume/score`)
- ✅ AI-powered resume scoring
- ✅ Three main scoring categories:
  - **Keyword Matching (35% weight)**
    - Matched/missing keywords
    - Keyword density analysis
    - Relevance scoring
  - **Language Expression (35% weight)**
    - Grammar quality
    - Professional tone
    - Clarity assessment
    - Action verb usage
  - **ATS Readability (30% weight)**
    - Format compatibility
    - Structure clarity
    - Parsing friendliness
    - Section organization
- ✅ Detailed recommendations
- ✅ Strengths and weaknesses analysis
- ✅ Overall weighted score

---

## Testing

### Manual Testing with cURL

**1. Health Check:**
```bash
curl -X GET http://localhost:5001/health
```

**2. Register User:**
```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

**3. Login:**
```bash
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

**4. Score Resume:**
```bash
curl -X POST http://localhost:5001/api/resume/score \
  -H "Content-Type: application/json" \
  -d '{
    "resume": {
      "personalInfo": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com"
      },
      "workExperience": [],
      "education": [],
      "skills": ["Python", "Flask"]
    },
    "job_description": "Looking for a Python developer with Flask experience"
  }'
```

### Automated Testing

Run the provided test script:
```bash
python test_api.py
```

---

## 🌐 Production Deployment Options

### Option 1: Railway (Recommended)

#### Advantages of Railway
- ✅ **Zero Configuration**: Automatic builds and deploys
- ✅ **Built-in PostgreSQL**: Managed database with automatic backups
- ✅ **SSL/HTTPS**: Automatic SSL certificates
- ✅ **Custom Domains**: Easy domain configuration
- ✅ **Environment Management**: Secure environment variable handling
- ✅ **Monitoring**: Built-in logging and metrics
- ✅ **Scaling**: Automatic scaling based on usage

#### Railway Deployment Process
```bash
# 1. Connect to Railway
railway login

# 2. Create new project from existing code
railway init

# 3. Add PostgreSQL database
railway add postgresql

# 4. Set environment variables
railway variables set OPENAI_API_KEY=sk-proj-your-key-here
railway variables set JWT_SECRET=your-production-secret
railway variables set FLASK_ENV=production

# 5. Deploy
railway up
```

#### Post-Deployment Railway Setup
```bash
# Run database migrations
railway run flask db upgrade

# View deployment logs
railway logs

# Open your deployed app
railway open
```

### Option 2: Docker Production Deployment

#### Using docker-compose.prod.yml
```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Start production services
docker compose -f docker-compose.prod.yml up -d

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

#### Production Environment Variables
```bash
# Production .env file
OPENAI_API_KEY=sk-proj-your-production-key
JWT_SECRET=very-secure-random-production-secret
DATABASE_URL=postgresql://user:password@production-db:5432/resume_app
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5001
```

### Security Considerations

1. **JWT Secret:** Use a strong, random secret key
2. **Database:** Use strong passwords, restrict access
3. **HTTPS:** Always use HTTPS in production
4. **CORS:** Configure appropriate CORS policies
5. **Rate Limiting:** Implement rate limiting for public endpoints
6. **API Keys:** Never commit API keys to version control

---

## 📊 Monitoring and Management

### Railway Monitoring
Railway provides built-in monitoring tools:

#### Application Metrics
- **CPU Usage**: Monitor resource consumption
- **Memory Usage**: Track memory usage patterns
- **Response Times**: API endpoint performance
- **Request Volume**: Traffic analytics
- **Error Rates**: Failed request tracking

#### Database Monitoring
```bash
# Connect to Railway PostgreSQL
railway connect postgres

# View database status
railway run psql $DATABASE_URL -c "SELECT NOW();"

# Check database size
railway run psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('railway'));"
```

#### Real-time Logs
```bash
# View live application logs
railway logs --tail

# Filter logs by level
railway logs --tail | grep ERROR

# Export logs for analysis
railway logs --tail > app_logs.txt
```

### Health Check Monitoring

#### Built-in Health Endpoint
The application includes a comprehensive health check at `/health`:
```json
{
  "status": "healthy",
  "service": "Resume Editor API", 
  "timestamp": "2025-10-16T10:30:00.000Z",
  "components": {
    "database": "connected",
    "openai": "configured"
  }
}
```

#### Automated Health Monitoring
```bash
# Local monitoring setup
*/5 * * * * curl -f https://your-app.railway.app/health || alert_team

# Railway-based monitoring (using Railway's built-in features)
# Configure alerts in Railway dashboard under "Observability"
```

### Local Development Monitoring
```bash
# View application logs
docker compose logs -f web

# View database logs  
docker compose logs -f db

# Monitor resource usage
docker stats

# Filter critical errors
docker compose logs web | grep -E "(ERROR|CRITICAL)"
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

**2. OpenAI API Errors**
```bash
# Verify API key is set
docker-compose exec web printenv OPENAI_API_KEY

# Test OpenAI connectivity
docker-compose exec web python -c "import openai; print('OK')"
```

**3. Port Already in Use**
```bash
# Check what's using port 5001
lsof -i :5001

# Kill the process or change port in docker-compose.yml
```

**4. Migration Issues**
```bash
# Reset migrations (CAUTION: Destroys data)
docker-compose exec web flask db downgrade base
docker-compose exec web flask db upgrade
```

---

## Maintenance

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres resume_app > backup.sql

# Restore backup
docker-compose exec -T db psql -U postgres resume_app < backup.sql
```

### Updating Dependencies

```bash
# Update requirements.txt
# Then rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Performance Optimization

### Recommendations

1. **Database Indexing:** Ensure indexes on frequently queried fields
2. **Caching:** Implement Redis for API response caching
3. **Connection Pooling:** Configure SQLAlchemy connection pooling
4. **API Rate Limiting:** Prevent abuse and ensure fair usage
5. **CDN:** Use CDN for static assets if applicable

---

## Support & Documentation

- **API Documentation:** http://localhost:5001/apidocs
- **Full API Reference:** See `API_DOCUMENTATION.md`
- **Project Rules:** See `.github/instructions/copilot-instructions.instructions.md`

---

## Version History

### v1.1.0 (Current)
- ✅ Added `/health` endpoint for system monitoring
- ✅ Integrated Swagger/OpenAPI documentation
- ✅ Implemented `/api/resume/score` endpoint
- ✅ Added detailed AI-powered scoring metrics
- ✅ Enhanced API documentation

### v1.0.0 (Previous)
- Basic resume parsing
- Job description analysis
- User authentication
- Resume management

---

## Future Roadmap

1. **Enhanced Scoring:**
   - Industry-specific scoring models
   - Multi-language resume support
   - Custom scoring weights

2. **Additional Features:**
   - Resume template generation
   - Cover letter generation
   - LinkedIn profile import
   - Resume comparison tools

3. **Infrastructure:**
   - Redis caching layer
   - Elasticsearch for resume search
   - Kubernetes deployment configs
   - CI/CD pipeline

---

## Contributing

Please follow the project guidelines in `.github/instructions/copilot-instructions.instructions.md` when contributing to this project.
