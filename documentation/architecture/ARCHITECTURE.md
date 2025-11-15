# Resume Editor - Enhanced Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Resume Editor API v1.1                       │
│                   http://localhost:5001                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│   NEW: /health    │  NEW: /apidocs   │    │  API Endpoints│
│   Monitoring  │    │  Documentation   │    │  (Existing)   │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ - Database   │    │ - Swagger UI     │    │ - Auth      │
│ - OpenAI     │    │ - Interactive    │    │ - Resume    │
│ - Status     │    │ - All Endpoints  │    │ - Profile   │
└──────────────┘    └──────────────────┘    └─────────────┘
```

## New Resume Scoring Endpoint

```
POST /api/resume/score
         │
         ▼
┌─────────────────────────────────────────┐
│         AI-Powered Scoring              │
│         (OpenAI GPT-4o-mini)            │
└─────────────────────────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│  Score Analysis  │            │  Recommendations │
└──────────────────┘            └──────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Keyword    │ │  Language   │ │    ATS      │ │   Overall   │
│  Matching   │ │ Expression  │ │ Readability │ │    Score    │
│   (35%)     │ │   (35%)     │ │   (30%)     │ │   (0-100)   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
      │               │               │
      ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ - Matched   │ │ - Grammar   │ │ - Format    │
│   keywords  │ │ - Tone      │ │ - Structure │
│ - Missing   │ │ - Clarity   │ │ - Parsing   │
│   keywords  │ │ - Action    │ │ - Sections  │
│ - Density   │ │   verbs     │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Scoring Calculation

```
Overall Score = (Keyword × 0.35) + (Language × 0.35) + (ATS × 0.30)

Example:
┌──────────────────────────────────────────────┐
│ Keyword Matching:      88 × 0.35 = 30.8     │
│ Language Expression:   85 × 0.35 = 29.75    │
│ ATS Readability:       83 × 0.30 = 24.9     │
│ ─────────────────────────────────────────    │
│ Overall Score:                   = 85.45    │
└──────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│    Client    │
└──────────────┘
       │
       │ POST /api/resume/score
       │ { resume: {...}, job_description: "..." }
       │
       ▼
┌──────────────────────┐
│   Flask Server       │
│   (server.py)        │
└──────────────────────┘
       │
       │ Validate input
       │
       ▼
┌──────────────────────┐
│   ResumeAI Service   │
│   (resume_ai.py)     │
└──────────────────────┘
       │
       │ score_resume()
       │
       ▼
┌──────────────────────┐
│   OpenAI API         │
│   (GPT-4o-mini)      │
└──────────────────────┘
       │
       │ AI Analysis
       │
       ▼
┌──────────────────────┐
│   Scoring Result     │
│   {                  │
│     overall_score,   │
│     scores: {...},   │
│     recommendations, │
│     strengths,       │
│     weaknesses       │
│   }                  │
└──────────────────────┘
       │
       │ JSON Response
       │
       ▼
┌──────────────┐
│    Client    │
└──────────────┘
```

## Health Check Flow

```
┌──────────────┐
│   Client     │
└──────────────┘
       │
       │ GET /health
       │
       ▼
┌──────────────────────┐
│   Flask Server       │
└──────────────────────┘
       │
       ├───────────────────────┬───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Database   │    │   OpenAI     │    │   Service    │
│   Check      │    │   Config     │    │   Status     │
└──────────────┘    └──────────────┘    └──────────────┘
       │                       │                       │
       │ SELECT 1              │ Check API key         │
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  "connected" │    │ "configured" │    │   "healthy"  │
└──────────────┘    └──────────────┘    └──────────────┘
       │                       │                       │
       └───────────────────────┴───────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  JSON Response   │
                    │  Status: 200/503 │
                    └──────────────────┘
```

## API Endpoint Summary

```
Public Endpoints (No Auth)
├── GET  /                          # Index
├── GET  /health                    # NEW: Health check
├── POST /api/register              # User registration
├── POST /api/login                 # User login
├── POST /api/pdfupload             # Upload PDF resume
├── POST /api/job_description_upload # Analyze with job
└── POST /api/resume/score          # NEW: Score resume

Protected Endpoints (JWT Required)
├── PUT  /api/save_resume           # Save resume
├── GET  /api/get_resume_list       # List resumes
├── GET  /api/get_resume/<id>       # Get resume
├── PUT  /api/put_profile           # Update profile
└── GET  /api/get_profile           # Get profile

Documentation
└── GET  /apidocs                   # NEW: Swagger UI
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│           Application Layer             │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │   Flask    │      │   Flasgger   │  │
│  │   3.1.0    │      │   (NEW)      │  │
│  └────────────┘      └──────────────┘  │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│           Database Layer                │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │PostgreSQL  │      │ SQLAlchemy   │  │
│  │    15      │      │   2.0.40     │  │
│  └────────────┘      └──────────────┘  │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            AI Layer                     │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │  OpenAI    │      │ GPT-4o-mini  │  │
│  │   API      │      │   (NEW)      │  │
│  └────────────┘      └──────────────┘  │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         Infrastructure                  │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │   Docker   │      │    Nginx     │  │
│  │  Compose   │      │  (Optional)  │  │
│  └────────────┘      └──────────────┘  │
└─────────────────────────────────────────┘
```

## Feature Comparison

```
┌──────────────────────┬────────────┬────────────┐
│      Feature         │   Before   │   After    │
├──────────────────────┼────────────┼────────────┤
│ Health Check         │     ❌     │     ✅     │
│ API Documentation    │     ❌     │     ✅     │
│ Resume Scoring       │     ❌     │     ✅     │
│ Keyword Analysis     │     ❌     │     ✅     │
│ Language Analysis    │     ❌     │     ✅     │
│ ATS Analysis         │     ❌     │     ✅     │
│ Swagger UI           │     ❌     │     ✅     │
│ PDF Upload           │     ✅     │     ✅     │
│ Job Analysis         │     ✅     │     ✅     │
│ User Auth            │     ✅     │     ✅     │
│ Resume Management    │     ✅     │     ✅     │
└──────────────────────┴────────────┴────────────┘
```

## Deployment Checklist

```
Prerequisites
├── ✅ Docker & Docker Compose installed
├── ✅ .env file with API keys
├── ✅ Port 5001 available
└── ✅ Port 5432 available

Setup Steps
├── 1. ✅ Copy .env.example to .env
├── 2. ✅ Add OPENAI_API_KEY
├── 3. ✅ Add JWT_SECRET
├── 4. ⚠️  docker-compose up -d --build
├── 5. ⚠️  docker-compose exec web flask db upgrade
├── 6. ⚠️  Test: curl http://localhost:5001/health
└── 7. ⚠️  Open: http://localhost:5001/apidocs

Verification
├── ⚠️  Health endpoint responds with 200
├── ⚠️  Swagger UI loads successfully
├── ⚠️  Database connection confirmed
├── ⚠️  OpenAI API configured
└── ⚠️  Test scoring endpoint works

✅ = Completed
⚠️  = Requires deployment
```
