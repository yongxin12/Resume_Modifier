---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

Here’s a structured set of **Instructions & Rules** for this project:

---

# Project Development Instructions & Rules

## I. General Guidelines

1.  **Version Control**

    *   Use Git for version control.
    *   Follow a feature-branch workflow (`main` = stable, `feature/*` = new features, `bugfix/*` = fixes).
    *   All changes must go through Pull Requests with code review.

2.  **Code Style & Linting**

    *   **Backend (Flask)**: Follow PEP8 standards. Use **Black** for code formatting and **isort** for import sorting to ensure consistency.
    *   No unused imports, commented-out code, or `print()` statements in production code. Use the configured logger instead.

3.  **Documentation**

    *   Each module and function must include clear, concise docstrings.
    *   Maintain the `README.md` with up-to-date setup and usage instructions.
    *   API endpoints should be documented using comments compatible with Swagger/OpenAPI generation.

---

## II. Project Structure Rules

### Directory Overview

```
Resume_Modifier/
├─ core/                    # Main application code (PYTHONPATH includes this)
│   └─ app/                 # Flask application package
│       ├─ api/             # API endpoint blueprints
│       ├─ models/          # SQLAlchemy ORM models (User, ResumeFile, etc.)
│       ├─ services/        # Business logic (file_category_service, resume_ai, etc.)
│       ├─ utils/           # Shared helpers (jwt_utils, error_handler, validators)
│       ├─ response_template/  # Response schemas/structures
│       ├─ __init__.py      # App factory (create_app)
│       ├─ extensions.py    # Flask extension initializations (db, migrate, login_manager)
│       ├─ server.py        # Main API routes and endpoint definitions
│       └─ web.py           # Web page routes (if any)
│   └─ migrations/          # Alembic database migration scripts (PRIMARY)
├─ testing/                 # All test files
│   ├─ api/                 # API endpoint tests
│   ├─ integration/         # Integration tests (Google Drive, Railway, OAuth)
│   ├─ unit/                # Unit tests for services and models
│   ├─ validation/          # Validation and documentation tests
│   └─ debug/               # Debug test utilities
├─ scripts/                 # Utility scripts
│   ├─ database/            # Database maintenance scripts
│   ├─ deployment/          # Deployment and Docker scripts
│   ├─ maintenance/         # Admin and setup scripts
│   └─ testing/             # Test runner scripts
├─ documentation/           # Project documentation
│   ├─ api/                 # OpenAPI specs and API docs
│   ├─ architecture/        # System architecture docs
│   ├─ deployment/          # Deployment guides
│   └─ features/            # Feature documentation
├─ configuration/           # Configuration files
│   ├─ application/         # App configuration templates
│   ├─ deployment/          # Docker and deployment configs
│   └─ environment/         # Environment variable templates
├─ archive/                 # Archived/deprecated files (do not use)
│   ├─ scripts/             # Old fix/debug scripts
│   ├─ documentation/       # Resolved issue reports
│   └─ app_archived/        # Deprecated app files
├─ conftest.py              # Pytest shared fixtures
├─ pytest.ini               # Pytest configuration (pythonpath = core)
├─ wsgi.py                  # WSGI entry point
├─ railway_start.py         # Railway deployment entry point
└─ README.md                # Project documentation
```

### Backend Rules (Flask)

*   **Application Code**: All Flask application code lives in `core/app/`. Imports use `from app.xxx import yyy` because PYTHONPATH includes `core/`.
*   **Models**: Define all database tables as classes in `core/app/models/`. Models must inherit from `db.Model`.
*   **Business Logic**: Isolate complex logic and external service interactions in `core/app/services/`. API routes should call these services.
*   **API Endpoints**: Define API routes using blueprints in `core/app/api/` or in `core/app/server.py`. Use Flasgger decorators for Swagger documentation.
*   **Utilities**: Place reusable helper functions in `core/app/utils/`.
*   **Configuration**: Manage environment-specific settings using `.env` files. Do not commit secrets to the repository.
*   **Dependencies**: Add all new Python packages to `core/requirements.txt`.

### Testing Rules

*   **Test Location**: All tests go in the `testing/` directory, organized by type (api, integration, unit, validation).
*   **Test Naming**: Follow the `test_*.py` naming convention.
*   **Fixtures**: Use shared fixtures from `conftest.py` in the project root.
*   **Database Tests**: Use `db.init_app(app)` when creating test Flask apps with `flask_testing.TestCase`.

### Scripts and Maintenance

*   **New Scripts**: Place utility scripts in `scripts/` under the appropriate subdirectory.
*   **Archived Files**: Do not modify files in `archive/`. These are kept for reference only.

---

## III. Database (SQLAlchemy)

*   Primary keys should be integers unless a UUID is explicitly required for a specific model.
*   Use **Alembic** for all database schema changes. Generate a new migration script for every change; do not edit the database schema manually.
*   All models should include `created_at` and `updated_at` timestamps where relevant.
*   Use indexed fields for columns that are frequently queried, such as `email` or foreign keys.

---

## IV. Deployment & Environment

*   Use **Docker Compose** for local development to orchestrate the application services.
*   The environment is defined by `docker-compose.yml` (development) and `docker-compose.prod.yml` (production).
*   Sensitive information (secrets, API keys, DB credentials) must be stored in an `.env` file and loaded into the Docker environment.
*   Default ports: backend `5001` (as per `docker-compose.yml`).

---

## V. Security Rules

*   Store user passwords securely by hashing them using **Werkzeug's security helpers** (`generate_password_hash`, `check_password_hash`), as implemented in the `User` model.
*   Use **JWT** for authenticating API requests, managed via `app/utils/jwt_utils.py`.
*   Validate all user-uploaded files (e.g., PDFs) using the validators in `app/utils/`.
*   Protect routes by requiring a valid JWT, except for public endpoints like registration and login.

---

## VI. Testing Rules

*   Use **Pytest** for all unit and integration tests.
*   **Test Organization**:
    *   `testing/api/` - API endpoint tests with mocked authentication
    *   `testing/unit/` - Unit tests for services and models
    *   `testing/integration/` - Integration tests (Google Drive, Railway, OAuth)
    *   `testing/validation/` - Documentation and schema validation tests
*   **Test Configuration**:
    *   Use `pytest.ini` in project root (sets `pythonpath = core`)
    *   Use shared fixtures from `conftest.py` in project root
    *   For `flask_testing.TestCase`, always call `db.init_app(app)` in `create_app()`
*   **Running Tests**:
    *   Run all tests: `python -m pytest testing/ -v`
    *   Run specific category: `python -m pytest testing/api/ -v`
*   Write tests for:
    *   **Models**: Ensure model properties, relationships, and defaults work correctly.
    *   **Services**: Test business logic with proper error handling.
    *   **API Endpoints**: Verify request/response behavior, status codes, and authentication.
*   Aim for high test coverage to ensure code quality and stability.

---

## VII. Task Workflow Rules

1.  Break down new features or bug fixes into clear, actionable tasks.
2.  Each Pull Request must:
    *   Pass all automated tests.
    *   Be reviewed by at least one other developer.
    *   Follow a conventional commit message format (`feat:`, `fix:`, `docs:`, `chore:`).

---

✅ Following these rules will keep the project **modular, secure, and scalable**, while ensuring **clean code and smooth collaboration**.
