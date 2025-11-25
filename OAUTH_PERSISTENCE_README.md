# OAuth Persistence & Storage Monitoring System

## Project Overview

A comprehensive Flask-based system that provides persistent OAuth authentication with Google, eliminating the need for repeated authentication while monitoring storage usage and providing automated alerts.

## Key Features

### 🔐 Persistent OAuth Authentication
- **Single Sign-On**: Authenticate once, stay logged in for 30 days
- **Automatic Token Refresh**: Background service maintains valid tokens
- **Session Management**: Secure session tokens with activity tracking
- **Admin Control**: Administrator-level access control and management

### 📊 Storage Monitoring  
- **Real-time Monitoring**: Continuous tracking of Google Drive storage usage
- **Smart Alerts**: Automated warnings at 80% and 90% capacity
- **Usage Analytics**: Detailed storage statistics and trends
- **Threshold Management**: Configurable alert levels and preferences

### 🔧 Background Services
- **Token Refresh Service**: Automatic OAuth token renewal
- **Storage Monitor**: Continuous storage quota checking
- **Alert System**: Email notifications for storage warnings
- **Cleanup Tasks**: Automated maintenance and data purging

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │   Background    │
│   Dashboard     │◄──►│   Endpoints     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │   Google APIs   │
                       │   Database      │    │   (OAuth/Drive) │
                       └─────────────────┘    └─────────────────┘
```

## Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Docker & Docker Compose
- Google Cloud Platform account

### Environment Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd Resume_Modifier
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
python -m alembic upgrade head
```

### Configuration
Key environment variables in `.env`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/resume_db

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5001/auth/callback

# Storage Monitoring
DEFAULT_STORAGE_QUOTA_GB=15
WARNING_THRESHOLD_PERCENT=80
CRITICAL_THRESHOLD_PERCENT=90
```

## Database Schema

### Enhanced GoogleAuth Model
The `GoogleAuth` model has been enhanced with 15 new fields for OAuth persistence:

#### Core Authentication Fields
- `access_token` - Current OAuth access token
- `refresh_token` - OAuth refresh token for token renewal  
- `token_expires_at` - Token expiration timestamp
- `is_active` - Account active status

#### OAuth Persistence Fields
- `persistent_auth_enabled` - Enable persistent authentication
- `auth_session_token` - Long-lived session token (30 days)
- `session_expires_at` - Session expiration timestamp
- `last_activity_at` - Last user activity timestamp
- `auto_refresh_enabled` - Enable automatic token refresh

#### Storage Monitoring Fields
- `storage_quota_gb` - Total storage quota in GB
- `storage_used_gb` - Current storage usage in GB
- `storage_warning_level` - Current warning level (normal/warning/critical)
- `last_storage_check` - Last storage check timestamp
- `storage_alert_enabled` - Enable storage alerts
- `storage_alert_threshold` - Custom alert threshold percentage
- `last_storage_alert` - Last alert sent timestamp

#### User Preferences & Compliance
- `auth_preferences` - JSON field for user preferences
- `compliance_flags` - JSON field for GDPR/compliance settings

## API Endpoints

### OAuth Persistence Endpoints
```bash
# Get OAuth status
GET /api/oauth/status

# Get detailed OAuth information  
GET /api/oauth/detailed-status

# Revoke OAuth session
POST /api/oauth/revoke
```

### Storage Monitoring Endpoints
```bash
# Get storage overview
GET /api/storage/overview

# Get storage monitoring service status
GET /api/storage/monitoring/status

# Configure storage monitoring
POST /api/storage/monitoring/configure

# Control storage monitoring service
POST /api/storage/monitoring/control
```

All endpoints require admin authentication via JWT token.

## Services Architecture

### 1. OAuth Persistence Service (`oauth_persistence_service.py`)
**Responsibilities:**
- Session management and validation
- Token expiry calculations
- Persistent session creation/revocation
- User session status tracking

**Key Methods:**
- `create_persistent_session()` - Create 30-day session
- `get_session_status()` - Validate session status
- `revoke_persistent_session()` - Revoke session with confirmation
- `is_token_expired()` - Check token expiration

### 2. Token Refresh Service (`token_refresh_service.py`)  
**Responsibilities:**
- Background token refresh automation
- Failure tracking and retry logic
- Token validation and renewal
- Service health monitoring

**Key Methods:**
- `refresh_user_token()` - Refresh individual user token
- `refresh_all_users()` - Batch token refresh
- `schedule_refresh_jobs()` - Schedule background jobs
- `get_service_health()` - Service health status

### 3. Storage Monitoring Service (`storage_monitoring_service.py`)
**Responsibilities:**
- Google Drive storage quota tracking
- Alert generation and management
- Usage trend analysis
- Threshold monitoring

**Key Methods:**
- `check_storage_quota()` - Check current usage
- `determine_warning_level()` - Calculate warning level
- `create_storage_alert()` - Generate alerts
- `get_storage_overview()` - Usage statistics

### 4. Background Storage Monitor (`background_storage_monitor.py`)
**Responsibilities:**
- Continuous storage monitoring
- Automated alert sending
- Service configuration management
- Background task scheduling

**Key Methods:**
- `monitor_all_users()` - Monitor all user storage
- `send_storage_alerts()` - Send email alerts
- `update_config()` - Update monitoring configuration
- `get_monitor_stats()` - Monitor statistics

## Testing Framework

### Test Structure
```
tests/
├── test_oauth_persistence_comprehensive.py  # Integration tests (13 tests)
├── test_storage_monitoring_units.py         # Storage unit tests (8 tests)  
├── test_oauth_service_units.py             # OAuth unit tests (19 tests)
├── test_config.py                           # Test configuration & mocks
├── run_all_tests.py                         # Comprehensive test runner
└── TEST_DOCUMENTATION.md                    # Detailed test documentation
```

### Running Tests
```bash
# Run all tests
python tests/run_all_tests.py

# Run with pytest
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_oauth_persistence_comprehensive.py -v
```

### Test Results (Latest)
- **Total Tests**: 40
- **Passing**: 13 (32.5%)
- **Failing**: 3 (7.5%)
- **Skipped**: 24 (60.0%)

## Deployment

### Production Deployment
1. **Environment Setup**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Database Migration**:
   ```bash
   python -m alembic upgrade head
   ```

3. **Service Verification**:
   ```bash
   python validate_deployment.sh
   ```

### Health Checks
- **API Health**: `GET /api/health`
- **Database**: Connection and migration status
- **Background Services**: Token refresh and storage monitoring
- **External APIs**: Google OAuth and Drive API connectivity

## Monitoring & Maintenance

### System Monitoring
- **OAuth Session Health**: Track active sessions and expiry rates
- **Storage Alert Effectiveness**: Monitor alert delivery and response rates  
- **Background Service Status**: Ensure token refresh and storage monitoring are running
- **API Performance**: Monitor response times and error rates

### Maintenance Tasks
- **Weekly**: Review storage alert logs and user feedback
- **Monthly**: Analyze OAuth session patterns and optimize refresh schedules
- **Quarterly**: Update Google API credentials and review security policies
- **Annually**: Full security audit and compliance review

## Security Considerations

### OAuth Security
- **Token Storage**: Encrypted token storage in database
- **Session Security**: Secure session token generation with expiry
- **Access Control**: Admin-only access to sensitive endpoints
- **Token Refresh**: Secure background token refresh with failure handling

### Data Privacy
- **GDPR Compliance**: User consent tracking and data retention policies
- **Data Minimization**: Store only necessary OAuth and storage data
- **Audit Logging**: Comprehensive logging of authentication and storage events
- **Data Encryption**: Encrypt sensitive data at rest and in transit

## Troubleshooting

### Common Issues

#### 1. OAuth Token Refresh Failures
**Symptoms**: Users getting logged out frequently
**Solutions**:
- Check Google OAuth credentials
- Verify refresh token validity
- Review token refresh service logs

#### 2. Storage Monitoring Not Working
**Symptoms**: No storage alerts despite high usage
**Solutions**:
- Verify Google Drive API permissions
- Check storage monitoring service status
- Review alert threshold configuration

#### 3. API Endpoint 404 Errors
**Symptoms**: Test failures with 404 responses
**Solutions**:
- Verify Flask server is running
- Check endpoint routing configuration
- Review URL patterns and method mappings

### Debug Commands
```bash
# Check service status
python -c "from app.services.oauth_persistence_service import OAuthPersistenceService; print('Service loaded')"

# Test database connection
python -c "from app.extensions import db; print('Database connected')"

# Validate API endpoints
curl -X GET http://localhost:5001/api/health

# Check background services
python -c "from app.services.background_storage_monitor import BackgroundStorageMonitor; print('Monitor loaded')"
```

## Contributing

### Development Workflow
1. Create feature branch from `main`
2. Implement changes following project guidelines
3. Write comprehensive tests (aim for 80%+ coverage)
4. Run full test suite and ensure passing
5. Submit pull request with detailed description

### Code Standards
- **Python**: Follow PEP8, use Black formatter
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: TDD approach with unit and integration tests
- **Security**: Follow OWASP guidelines for web applications

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- **Documentation**: Check this README and `docs/` directory
- **Issues**: Create GitHub issues for bugs and feature requests
- **Testing**: Review `tests/TEST_DOCUMENTATION.md` for test-related questions

---

**Last Updated**: November 2024  
**Version**: 1.0.0  
**Test Coverage**: 32.5% (Target: 80%+)