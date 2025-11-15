# Environment Configuration Guide

This guide covers all environment configuration needed for the Resume Editor application, with special focus on the password recovery system.

## Quick Start

1. **Development**: Copy `.env.development.template` to `.env`
2. **Production**: Copy `.env.production.template` to `.env.production`
3. **Fill in your actual values** (see sections below)
4. **Never commit `.env` files** to version control

## Environment Files

### Development Environment
```bash
cp .env.development.template .env
# Edit .env with your development values
```

### Production Environment
```bash
cp .env.production.template .env.production
# Edit .env.production with your production values
```

### Testing Environment
```bash
cp .env.development.template .env.test
# Modify database URL to use test database
# Set TESTING=True
```

## Core Configuration

### 1. OpenAI API Key
**Required for all AI features**

```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**How to get:**
1. Visit [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Database Configuration
**Required for data persistence**

```bash
# PostgreSQL (Recommended)
DATABASE_URL=postgresql://username:password@host:port/database

# Examples:
# Local development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_app

# Railway (automatic)
DATABASE_URL=${{DATABASE_URL}}

# Heroku (automatic)
DATABASE_URL=${{DATABASE_URL}}
```

### 3. JWT Secret
**Required for authentication**

```bash
JWT_SECRET=your-super-secure-random-string-here
```

**Generate secure secret:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Password Recovery Configuration

### 1. Email Server Setup

#### Gmail (Recommended)
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # NOT your regular password!
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Gmail Setup Steps:**
1. Create a dedicated Gmail account (e.g., `noreply-resumeapp@gmail.com`)
2. Enable 2-factor authentication
3. Generate App Password:
   - Google Account → Security → App passwords
   - Select "Mail" and generate
   - Use generated password as `MAIL_PASSWORD`

#### Other Email Providers
```bash
# Outlook/Hotmail
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587

# Yahoo
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587

# SendGrid (Professional)
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key

# Mailgun (Professional)  
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=your-mailgun-username
MAIL_PASSWORD=your-mailgun-password
```

### 2. Security Settings

```bash
# Token expiration (hours)
PASSWORD_RESET_TOKEN_EXPIRY_HOURS=24

# Rate limiting (requests per hour)
PASSWORD_RESET_RATE_LIMIT_USER=5    # per user email
PASSWORD_RESET_RATE_LIMIT_IP=10     # per IP address

# Cleanup frequency (hours)
PASSWORD_RESET_CLEANUP_INTERVAL_HOURS=6

# Password requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=True
PASSWORD_REQUIRE_LOWERCASE=True
PASSWORD_REQUIRE_NUMBERS=True
PASSWORD_REQUIRE_SPECIAL_CHARS=True
```

### 3. Application URLs

```bash
# Frontend URL (for email links)
FRONTEND_URL=https://your-frontend-domain.com

# Application branding
APP_NAME=Resume Editor
COMPANY_NAME=Your Company Name
SUPPORT_EMAIL=support@your-domain.com

# Email template assets
EMAIL_LOGO_URL=https://your-domain.com/logo.png
EMAIL_FOOTER_TEXT=© 2024 Your Company. All rights reserved.
```

## Platform-Specific Configuration

### Railway
```bash
# Railway auto-sets these variables
DATABASE_URL=${{DATABASE_URL}}
PORT=${{PORT}}

# Add your custom variables to Railway dashboard
OPENAI_API_KEY=your-key
JWT_SECRET=your-secret
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
```

### Heroku
```bash
# Set environment variables via CLI
heroku config:set OPENAI_API_KEY=your-key
heroku config:set JWT_SECRET=your-secret
heroku config:set MAIL_USERNAME=your-email
heroku config:set MAIL_PASSWORD=your-password

# Or via Heroku dashboard → Settings → Config Vars
```

### DigitalOcean App Platform
```bash
# Add environment variables in App Platform dashboard
# Under App → Settings → Environment Variables
```

### Docker Compose
```yaml
# In docker-compose.yml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - DATABASE_URL=${DATABASE_URL}
  - JWT_SECRET=${JWT_SECRET}
  - MAIL_USERNAME=${MAIL_USERNAME}
  - MAIL_PASSWORD=${MAIL_PASSWORD}
```

## Testing Configuration

### Development Testing
```bash
# Allow more lenient rate limits for testing
PASSWORD_RESET_RATE_LIMIT_USER=10
PASSWORD_RESET_RATE_LIMIT_IP=20

# Use console email backend for testing
TESTING_EMAIL_BACKEND=console
MAIL_SUPPRESS_SEND=True  # Don't actually send emails
```

### Email Testing Tools

#### MailHog (Local Email Testing)
```bash
# Install MailHog
go install github.com/mailhog/MailHog@latest

# Run MailHog
mailhog

# Configure app to use MailHog
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
```

#### Mailtrap (Online Email Testing)
```bash
# Get credentials from mailtrap.io
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
```

## Security Best Practices

### 1. Secret Management
- **Never commit secrets** to version control
- Use platform secret management when available
- Rotate secrets regularly
- Use different secrets for different environments

### 2. Email Security
- Use dedicated email accounts for applications
- Enable 2FA on email accounts
- Monitor email sending rates and bounce rates
- Set up SPF, DKIM, and DMARC records for production

### 3. Environment Separation
```bash
# Development
JWT_SECRET=dev-secret-12345
MAIL_USERNAME=dev-email@gmail.com

# Production  
JWT_SECRET=prod-super-secure-random-string
MAIL_USERNAME=noreply@yourcompany.com
```

### 4. Monitoring
```bash
# Add monitoring URLs if using services like Sentry
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Add logging configuration
LOG_LEVEL=INFO  # or DEBUG for development
```

## Troubleshooting

### Common Issues

#### 1. Email Not Sending
```bash
# Check SMTP credentials
# Verify email provider settings
# Check firewall/network restrictions
# Review application logs

# Test email configuration
python -c "
from app.services.email_service import EmailService
service = EmailService()
result = service.send_password_reset_email(
    'test@example.com', 'test-token', 'Test User'
)
print(result)
"
```

#### 2. Database Connection Issues
```bash
# Verify DATABASE_URL format
# Check database server status
# Verify credentials and permissions
# Test connection manually

# Test database connection
python -c "
from app.extensions import db
from app import create_app
app = create_app()
with app.app_context():
    print('Database connection:', db.engine.execute('SELECT 1').scalar())
"
```

#### 3. Rate Limiting Too Restrictive
```bash
# Temporarily increase limits for testing
PASSWORD_RESET_RATE_LIMIT_USER=100
PASSWORD_RESET_RATE_LIMIT_IP=200

# Or disable for testing
TESTING_DISABLE_RATE_LIMITING=True
```

### Validation Scripts

#### Test All Configuration
```bash
python scripts/validate_config.py
```

#### Test Email Configuration
```bash
python scripts/test_email.py --email your-email@example.com
```

#### Test Database Configuration
```bash
python scripts/test_database.py
```

## Environment Variables Reference

### Required Variables
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `MAIL_SERVER`: SMTP server hostname
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password

### Optional Variables
- `MAIL_PORT`: SMTP port (default: 587)
- `MAIL_USE_TLS`: Use TLS encryption (default: True)
- `MAIL_DEFAULT_SENDER`: Default sender email
- `PASSWORD_RESET_TOKEN_EXPIRY_HOURS`: Token expiry (default: 24)
- `PASSWORD_RESET_RATE_LIMIT_USER`: User rate limit (default: 5)
- `PASSWORD_RESET_RATE_LIMIT_IP`: IP rate limit (default: 10)
- `FRONTEND_URL`: Frontend URL for email links
- `APP_NAME`: Application name for branding

### Platform Variables (Auto-set)
- `PORT`: Server port (set by hosting platform)
- `HOST`: Server host (usually 0.0.0.0)
- `DATABASE_URL`: Database URL (set by database service)

## Support

If you need help with environment configuration:

1. Check the troubleshooting section above
2. Review the example environment files
3. Test individual components with validation scripts
4. Check application logs for specific error messages