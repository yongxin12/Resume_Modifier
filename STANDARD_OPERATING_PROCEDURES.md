# Resume Editor Project - Standard Operating Procedures (SOPs)
**Version:** 1.0  
**Date:** November 22, 2025  
**Status:** Active

---

## 📋 Overview

This document establishes standard operating procedures for the Resume Editor project to ensure smooth implementation of new features and resolution of defects. The workflow follows Test-Driven Development (TDD) principles and emphasizes proper documentation, testing, and deployment practices.

---

## 🎯 Core SOP Workflow (10-Step Process)

### Step 1: Functionality Analysis & Specification
**Objective:** Break down requirements and document in function specification

**Process:**
1. **Requirement Gathering**
   - Receive functionality request (GitHub issue, user story, or bug report)
   - Analyze scope, complexity, and dependencies
   - Identify affected components (API, UI, database, services)

2. **Documentation Update**
   - Open `function-specification.md`
   - Add new functionality section with:
     - **Purpose**: What problem does this solve?
     - **Scope**: What components are affected?
     - **Requirements**: Functional and non-functional requirements
     - **Dependencies**: External services, database changes, API modifications
     - **Acceptance Criteria**: Clear, testable conditions for completion

**Example Function Specification Entry:**
```markdown
## Feature: OAuth Token Refresh Automation
**Purpose:** Automatically refresh Google OAuth tokens before expiration
**Scope:** OAuth persistence service, background monitoring, token refresh endpoints
**Requirements:**
- Detect tokens expiring within 1 hour
- Automatically refresh using refresh token
- Log refresh activities
- Handle refresh failures gracefully
**Dependencies:** Google OAuth API, PostgreSQL, background scheduler
**Acceptance Criteria:**
- Tokens refresh automatically when 1 hour from expiry
- Failed refreshes trigger user notification
- All refresh activities logged with timestamps
```

**Deliverables:**
- ✅ Updated `function-specification.md`
- ✅ Requirements clearly documented
- ✅ Scope and dependencies identified

---

### Step 2: Task Breakdown & Test Case Design
**Objective:** Apply TDD principles to design comprehensive test cases

**Process:**
1. **Task Decomposition**
   - Break functionality into atomic, testable units
   - Identify edge cases and error scenarios
   - Map test cases to acceptance criteria

2. **Test Case Design**
   - **Unit Tests**: Individual function/method testing
   - **Integration Tests**: Component interaction testing
   - **End-to-End Tests**: Full workflow validation
   - **Edge Case Tests**: Boundary conditions, error handling
   - **Performance Tests**: Load and stress testing where applicable

**Test Case Template:**
```python
class TestOAuthTokenRefresh:
    """Test cases for OAuth token refresh functionality"""
    
    def test_token_refresh_before_expiry(self):
        """Should refresh token when 1 hour from expiry"""
        # Given: Token expiring in 1 hour
        # When: Background monitor runs
        # Then: Token is refreshed successfully
        
    def test_token_refresh_failure_handling(self):
        """Should handle refresh failures gracefully"""
        # Given: Refresh token is invalid
        # When: Refresh attempt is made
        # Then: User is notified, error is logged
```

**Deliverables:**
- ✅ Comprehensive test case list
- ✅ Test scenarios mapped to requirements
- ✅ Edge cases and error conditions identified

---

### Step 3: Test Implementation
**Objective:** Create tests before implementing functionality

**Process:**
1. **Test File Creation**
   ```bash
   # Create test files following naming convention
   touch tests/test_oauth_token_refresh.py
   touch tests/integration/test_oauth_background_service.py
   ```

2. **Test Implementation Standards**
   - Use descriptive test names: `test_should_refresh_token_when_one_hour_from_expiry`
   - Follow AAA pattern: Arrange, Act, Assert
   - Mock external dependencies (Google API, database)
   - Include positive and negative test cases
   - Add performance tests for critical paths

3. **Test Categories**
   - **Unit Tests** (`tests/unit/`): Test individual functions/methods
   - **Integration Tests** (`tests/integration/`): Test component interactions
   - **API Tests** (`tests/api/`): Test API endpoint functionality
   - **End-to-End Tests** (`tests/e2e/`): Test complete workflows

**Example Test Implementation:**
```python
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

class TestOAuthTokenRefresh:
    @patch('core.app.services.google_auth.GoogleAuthService.refresh_token')
    def test_should_refresh_token_when_one_hour_from_expiry(self, mock_refresh):
        # Arrange
        mock_refresh.return_value = {'access_token': 'new_token'}
        token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        # Act
        result = oauth_service.check_and_refresh_token(token_expiry)
        
        # Assert
        assert result.success is True
        mock_refresh.assert_called_once()
```

**Deliverables:**
- ✅ Comprehensive test suite created
- ✅ All test cases implemented
- ✅ Tests are failing (Red phase of TDD)

---

### Step 4: Feature Implementation (TDD Approach)
**Objective:** Implement functionality to make tests pass

**Process:**
1. **Implementation Strategy**
   - Start with simplest test case
   - Write minimal code to make test pass (Green phase)
   - Refactor for quality and performance (Refactor phase)
   - Repeat Red-Green-Refactor cycle

2. **Code Standards**
   - Follow existing code patterns and architecture
   - Add comprehensive docstrings and comments
   - Implement proper error handling
   - Add logging for debugging and monitoring
   - Follow security best practices

3. **Component Integration**
   - Update models if database changes needed
   - Add new service methods
   - Create or update API endpoints
   - Update response schemas
   - Add proper authentication/authorization

**Example Implementation:**
```python
class OAuthTokenRefreshService:
    """Service for managing OAuth token refresh automation"""
    
    def __init__(self):
        self.google_auth_service = GoogleAuthService()
        self.logger = logging.getLogger(__name__)
    
    def check_and_refresh_token(self, token_expiry: datetime) -> RefreshResult:
        """
        Check if token needs refresh and refresh if necessary
        
        Args:
            token_expiry: Token expiration datetime
            
        Returns:
            RefreshResult with success status and new token data
        """
        try:
            # Check if refresh needed (1 hour threshold)
            if self._needs_refresh(token_expiry):
                return self._refresh_token()
            return RefreshResult(success=True, refreshed=False)
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            return RefreshResult(success=False, error=str(e))
```

**Deliverables:**
- ✅ Feature implemented following TDD
- ✅ All tests passing
- ✅ Code follows project standards

---

### Step 5: Task Tracking & Progress Management
**Objective:** Maintain visibility into development progress

**Process:**
1. **Task Tracking Document Updates**
   - Open `TASK_TRACKING.md`
   - Update task status: `Not Started` → `In Progress` → `Completed`
   - Record completion timestamps
   - Note any blockers or issues encountered

2. **Progress Reporting Format**
```markdown
## OAuth Token Refresh Implementation - 2025-11-22

### Tasks Completed ✅
- [x] Function specification documented
- [x] Test cases designed (15 tests)
- [x] Unit tests implemented (10 tests)
- [x] Integration tests implemented (5 tests)
- [x] OAuth refresh service implemented
- [x] Background monitoring service updated

### Current Task 🔄
- [ ] API endpoint integration

### Blockers/Issues 🚨
- None

### Next Steps ⏭️
- Complete API endpoint testing
- Update Swagger documentation
- Docker container testing
```

**Deliverables:**
- ✅ Task tracking document updated
- ✅ Progress clearly documented
- ✅ Blockers identified and addressed

---

### Step 6: Docker Development Environment
**Objective:** Use containerized environment for consistent development

**Process:**
1. **Container Management**
   ```bash
   # Always use Docker for development server
   docker-compose down && docker-compose build && docker-compose up -d
   
   # Verify services are running
   docker-compose ps
   
   # Check logs for issues
   docker-compose logs web
   docker-compose logs db
   ```

2. **Development Workflow**
   - Keep containers running in background
   - Use Docker for all testing and validation
   - Database changes reflected in containerized PostgreSQL
   - No need to restart containers for code changes (volume mounting)

3. **Container Health Monitoring**
   ```bash
   # Health check endpoints
   curl http://localhost:5001/health
   
   # Database connectivity test
   curl http://localhost:5001/api/storage/overview
   ```

**Benefits:**
- ✅ Consistent development environment
- ✅ Eliminates "works on my machine" issues
- ✅ Easy environment replication
- ✅ Database state preservation

---

### Step 7: Iterative Development & Testing Loop
**Objective:** Continuous validation until all tests pass

**Process:**
1. **Testing Loop**
   ```bash
   # Run all tests in Docker environment
   docker-compose exec web python -m pytest tests/ -v
   
   # Run specific test suite
   docker-compose exec web python -m pytest tests/test_oauth_token_refresh.py -v
   
   # Run with coverage
   docker-compose exec web python -m pytest tests/ --cov=core.app --cov-report=html
   ```

2. **Iteration Criteria**
   - ✅ All unit tests pass
   - ✅ All integration tests pass
   - ✅ All API tests pass
   - ✅ Code coverage > 90% for new code
   - ✅ No security vulnerabilities
   - ✅ Performance benchmarks met

3. **Issue Resolution**
   - Debug failing tests immediately
   - Fix code or adjust tests as needed
   - Maintain test-first approach
   - Document any test exceptions or known issues

**Deliverables:**
- ✅ All tests passing consistently
- ✅ Code quality standards met
- ✅ Feature working in Docker environment

---

### Step 8: Integration Validation & Documentation
**Objective:** Ensure all tests pass and documentation is current

**Process:**
1. **Comprehensive Test Suite Execution**
   ```bash
   # Run full test suite
   docker-compose exec web python -m pytest tests/ -v --tb=short
   
   # Run OAuth-specific tests
   docker-compose exec web python -m pytest tests/ -k "oauth" -v
   
   # Run API endpoint tests
   python validate_docker_oauth.py
   ```

2. **API Documentation Updates**
   - Update Swagger documentation for new endpoints
   - Add comprehensive parameter descriptions
   - Include example requests and responses
   - Document error codes and scenarios

3. **Documentation Checklist**
   - ✅ Swagger docs updated (`/apidocs/`)
   - ✅ Function specification updated
   - ✅ API changes documented
   - ✅ Code comments comprehensive
   - ✅ README.md updated if needed

**Example Swagger Documentation:**
```python
@api.route('/api/oauth/token/refresh', methods=['POST'])
@swag_from({
    'tags': ['OAuth Management'],
    'summary': 'Manually refresh OAuth token',
    'description': 'Manually trigger OAuth token refresh for current user',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Token refreshed successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'token_refreshed': {'type': 'boolean'},
                    'expires_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        },
        401: {'description': 'Authentication required'},
        500: {'description': 'Token refresh failed'}
    }
})
@token_required
def refresh_oauth_token():
    # Implementation
```

**Deliverables:**
- ✅ All tests passing (100% success rate)
- ✅ Swagger documentation updated
- ✅ Feature fully documented

---

### Step 9: Cleanup & Organization
**Objective:** Remove temporary files and organize codebase

**Process:**
1. **File Cleanup**
   ```bash
   # Remove temporary scripts
   rm -f debug_*.py
   rm -f test_*.py (if not permanent tests)
   rm -f validate_*.py (if temporary)
   rm -f analyze_*.py (if temporary)
   
   # Remove temporary documentation
   rm -f *_TEMP.md
   rm -f *_DRAFT.md
   rm -f RESOLUTION_*.md (if obsolete)
   ```

2. **Code Organization**
   - Move permanent scripts to appropriate directories
   - Update `.gitignore` for new file types
   - Organize test files in proper directories
   - Clean up unused imports and comments

3. **Documentation Consolidation**
   - Archive completed task documentation
   - Update main project documentation
   - Remove redundant or outdated docs
   - Ensure documentation links are valid

**Cleanup Checklist:**
- ✅ Temporary files removed
- ✅ Code properly organized
- ✅ Documentation consolidated
- ✅ Git repository clean

---

### Step 10: Railway Database Integration
**Objective:** Deploy database changes to production environment

**Process:**
1. **Pre-deployment Verification**
   ```bash
   # Verify Railway connection
   railway status
   railway whoami
   
   # Check current database state
   echo "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" | railway connect postgres
   ```

2. **Database Migration**
   ```bash
   # Run Railway migration script
   ./scripts/maintenance/railway_migrate.sh
   
   # Verify migration success
   python verify_railway_db.py
   
   # Check specific table changes
   echo "DESCRIBE new_table;" | railway connect postgres
   ```

3. **Production Validation**
   ```bash
   # Test production endpoints
   curl -X GET "https://your-railway-app.railway.app/health"
   curl -X GET "https://your-railway-app.railway.app/api/auth/google/status" \
        -H "Authorization: Bearer $TEST_TOKEN"
   ```

4. **Rollback Plan**
   - Document migration steps for rollback
   - Keep backup of previous database state
   - Test rollback procedure in staging environment

**Deliverables:**
- ✅ Database changes deployed to Railway
- ✅ Production endpoints working
- ✅ Migration documented and verified

---

## 🛠️ Tools & Technologies

### Development Environment
- **Docker & Docker Compose**: Containerized development environment
- **Python 3.11+**: Primary development language
- **Flask**: Web framework
- **PostgreSQL**: Database system
- **Railway**: Cloud deployment platform

### Testing Framework
- **pytest**: Primary testing framework
- **pytest-cov**: Code coverage analysis
- **unittest.mock**: Mocking framework
- **requests**: API testing

### Documentation
- **Swagger/OpenAPI**: API documentation
- **Markdown**: General documentation
- **Flasgger**: Flask-Swagger integration

### Quality Assurance
- **TDD Approach**: Test-driven development
- **Code Coverage**: Minimum 90% for new code
- **Docker Testing**: All tests run in containerized environment

---

## 📚 Reference Documents

### Project Documentation
- `function-specification.md`: Detailed feature specifications
- `TASK_TRACKING.md`: Development progress tracking
- `API_DOCUMENTATION.md`: API endpoint documentation
- `README.md`: Project setup and usage

### Technical References
- `IMPLEMENTATION_REPORT.md`: Technical implementation details
- `DOCKER_OAUTH_DEPLOYMENT_SUCCESS.md`: Docker deployment guide
- `OAUTH_PERSISTENCE_README.md`: OAuth system documentation

### Scripts & Tools
- `scripts/railway_migrate.py`: Database migration script
- `scripts/maintenance/railway_migrate.sh`: Railway deployment script
- `validate_docker_oauth.py`: OAuth endpoint validation
- `analyze_api_docs.py`: API documentation analysis

---

## 🧪 Test Conflict Prevention & Resolution

### Overview
Test conflicts occur when fixing one test causes another to fail, creating a cascade of issues. This section provides systematic approaches to prevent and resolve test conflicts.

### Common Test Conflict Patterns

#### 1. **Model Constructor Parameter Mismatches**
**Problem:** Different tests use different parameter names for the same model constructor
- Example: `User(password_hash='...')` vs `User(password='...')`
- Impact: Fixing one test breaks another that uses incorrect parameters

**Prevention:**
```python
# Always verify model constructor signature first
def create_test_user():
    """Standardized user creation for all tests"""
    return User(
        username='testuser', 
        email='test@example.com',
        password='hashed_password'  # Use actual parameter name
    )
```

**Resolution Strategy:**
1. Check actual model constructor in `models/temp.py`
2. Search for ALL constructor calls: `grep -r "User(" testing/`
3. Update ALL instances consistently
4. Create shared fixture to prevent future mismatches

#### 2. **Database Session Management Conflicts**
**Problem:** Tests accessing model attributes outside session context
- Example: `DetachedInstanceError` when accessing model.id in fixtures
- Impact: Session fixes for one test can affect others

**Prevention:**
```python
@pytest.fixture
def sample_model(app):
    with app.app_context():
        model = Model(...)
        db.session.add(model)
        db.session.commit()
        # Re-attach to session for later access
        return db.session.merge(model)

def test_method(app, sample_model):
    with app.app_context():
        # Always re-attach when accessing attributes
        model = db.session.merge(sample_model)
        assert model.id is not None
```

**Resolution Strategy:**
1. Identify all session-dependent code
2. Add session management consistently across all tests
3. Use `db.session.merge()` pattern uniformly

#### 3. **Import Path Inconsistencies**
**Problem:** Different test files use different import patterns
- Example: `from app.models import User` vs `from core.app.models import User`
- Impact: Path fixes for one location break others

**Prevention:**
```python
# Use consistent PYTHONPATH approach
# Set in pytest configuration or test runner
PYTHONPATH=/path/to/core:$PYTHONPATH python -m pytest
```

**Resolution Strategy:**
1. Standardize import paths project-wide
2. Use environment-based path resolution
3. Document import patterns in project guidelines

#### 4. **Datetime Import/Usage Conflicts**
**Problem:** Mixed datetime import and usage patterns
- Example: `import datetime` + `datetime.utcnow()` vs `from datetime import datetime`
- Impact: Datetime fixes break other modules

**Prevention:**
```python
# Consistent datetime imports across project
from datetime import datetime

# Consistent usage pattern
created_at = datetime.utcnow()
```

**Resolution Strategy:**
1. Audit all datetime imports: `grep -r "import.*datetime" .`
2. Standardize to one pattern project-wide
3. Use automated tools (sed/awk) for bulk updates

### Test Conflict Resolution Workflow

#### Step 1: Conflict Detection
```bash
# Run full test suite to identify conflicts
PYTHONPATH=/path/to/core:$PYTHONPATH python -m pytest testing/ --tb=short

# Focus on failed tests
pytest --lf  # Last failed tests only
```

#### Step 2: Pattern Analysis
1. **Categorize failures** by error type:
   - Constructor parameter errors
   - Session management errors  
   - Import path errors
   - Datetime/attribute errors

2. **Map dependencies** between tests:
   - Shared fixtures
   - Common model usage
   - Overlapping imports

#### Step 3: Systematic Resolution
```python
# Example: Fix all User constructor calls
# 1. Find all occurrences
grep -r "User(" testing/ core/

# 2. Verify correct signature
# Check core/app/models/temp.py User.__init__

# 3. Update all at once (avoid partial fixes)
sed -i 's/password_hash=/password=/g' testing/**/*.py

# 4. Test all affected areas
pytest testing/ -k "User" -v
```

#### Step 4: Validation & Prevention
```bash
# Run complete test suite to ensure no new conflicts
PYTHONPATH=/path/to/core:$PYTHONPATH python -m pytest testing/ --tb=short

# Document patterns for future reference
echo "User constructor: User(username, email, password)" >> CODING_STANDARDS.md
```

### Test Conflict Prevention Best Practices

#### 1. **Shared Test Utilities**
```python
# testing/utils/model_factories.py
class ModelFactory:
    @staticmethod
    def create_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com', 
            'password': 'hashed_password'
        }
        defaults.update(kwargs)
        return User(**defaults)
```

#### 2. **Consistent Test Configuration**
```python
# conftest.py - shared across all tests
@pytest.fixture
def app():
    """Consistent app configuration for all tests"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
```

#### 3. **Model Interface Contracts**
```python
# tests/contracts/test_model_contracts.py
def test_user_constructor_interface():
    """Verify User constructor signature doesn't change"""
    import inspect
    sig = inspect.signature(User.__init__)
    expected_params = ['self', 'username', 'email', 'password']
    actual_params = list(sig.parameters.keys())
    assert actual_params == expected_params
```

#### 4. **Automated Conflict Detection**
```bash
# Pre-commit hook to catch common conflicts
#!/bin/bash
# check_test_conflicts.sh

# Check for mixed datetime imports
if grep -r "import datetime" . && grep -r "from datetime import" .; then
    echo "❌ Mixed datetime import patterns detected"
    exit 1
fi

# Check for inconsistent model constructors  
if grep -r "password_hash=" testing/ && grep -r "password=" testing/; then
    echo "❌ Mixed User constructor patterns detected"
    exit 1
fi

echo "✅ No test conflicts detected"
```

### Test Conflict Monitoring

#### Continuous Integration Checks
```yaml
# .github/workflows/test-conflicts.yml
name: Test Conflict Detection
on: [push, pull_request]
jobs:
  detect-conflicts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check for test conflicts
        run: |
          ./scripts/check_test_conflicts.sh
          PYTHONPATH=core:$PYTHONPATH python -m pytest testing/ --tb=short
```

#### Metrics & Reporting
- **Test Pass Rate**: Monitor overall test success percentage
- **Conflict Patterns**: Track recurring conflict types
- **Resolution Time**: Measure time to resolve conflicts
- **Prevention Effectiveness**: Count conflicts prevented by guidelines

### Documentation Requirements

#### Test Conflict Log
```markdown
## Test Conflict Resolution Log

### 2025-11-25: User Constructor Parameter Mismatch
**Problem:** Tests using `password_hash` parameter but model expects `password`
**Root Cause:** Model interface changed but tests not updated
**Resolution:** Updated all User() calls to use correct parameters
**Prevention:** Added model contract tests and shared factories
**Files Affected:** 15 test files, 34 constructor calls
**Time to Resolve:** 2 hours
```

#### Model Change Impact Assessment
Before changing any model interface:
1. **Search for all usages**: `grep -r "ModelName(" .`
2. **Assess test impact**: Count affected test files
3. **Plan coordinated update**: Update all usages simultaneously
4. **Add deprecation period**: If breaking change, provide transition period

This comprehensive approach ensures that test fixes don't create cascading failures and maintains a stable test suite throughout development.

---

## 🚨 Emergency Procedures

### Rollback Process
1. **Identify Issue**: Document the problem and affected components
2. **Stop Deployment**: Halt any ongoing deployment processes
3. **Database Rollback**: Use Railway database backup if needed
4. **Code Rollback**: Revert to last known good commit
5. **Verification**: Run full test suite to confirm rollback success
6. **Communication**: Update stakeholders and document lessons learned

### Critical Issue Response
1. **Assessment**: Evaluate impact and urgency
2. **Immediate Action**: Apply temporary fixes if available
3. **Root Cause Analysis**: Identify underlying cause
4. **Permanent Fix**: Implement proper solution following SOP
5. **Prevention**: Update SOPs to prevent recurrence

---

## 📊 Success Metrics

### Development Quality
- **Test Coverage**: > 90% for new code
- **Test Success Rate**: 100% pass rate required
- **Documentation Coverage**: All public APIs documented
- **Code Review**: All changes peer-reviewed

### Deployment Success
- **Railway Integration**: 100% deployment success
- **API Uptime**: > 99.9% availability
- **Response Time**: < 200ms for health checks
- **Error Rate**: < 0.1% for production endpoints

---

## 🔄 SOP Maintenance

### Review Schedule
- **Monthly**: Review SOP effectiveness and metrics
- **Quarterly**: Update based on lessons learned
- **Annual**: Comprehensive SOP revision

### Update Process
1. Identify improvement opportunities
2. Draft SOP changes
3. Test changes in development environment
4. Get team approval
5. Update documentation
6. Train team on changes

---

**Document Control:**
- **Version**: 1.0
- **Last Updated**: November 22, 2025
- **Next Review**: December 22, 2025
- **Owner**: Resume Editor Development Team
- **Approved By**: Project Lead