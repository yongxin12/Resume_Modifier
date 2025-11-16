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

### Backend (Flask)

```
app/
 ├─ models/             # SQLAlchemy ORM models (e.g., User, Resume)
 ├─ services/           # Business logic (e.g., resume_ai.py for AI processing)
 ├─ utils/              # Shared helpers (e.g., validators, PDF parsers)
 ├─ response_template/  # Defines response schemas/structures
 ├─ tests/              # Pytest unit and integration tests
 ├─ server.py           # Main Flask application, API endpoint definitions
 ├─ extensions.py       # Flask extension initializations (db, migrate)
 └─ web.py              # Routes for web pages (if any)
migrations/              # Alembic database migration scripts
```

**Rules**

*   **Models**: Define all database tables as classes in the `app/models/` directory. Models must inherit from `db.Model`.
*   **Business Logic**: Isolate complex logic and external service interactions (like AI calls) within the `app/services/` directory. API routes in `server.py` should call these services.
*   **API Endpoints**: Define all API routes in `app/server.py`. Keep routes clean and focused on handling requests and responses.
*   **Utilities**: Place reusable helper functions, such as PDF parsers (`parse_pdf.py`) and validators, in the `app/utils/` directory.
*   **Configuration**: Manage environment-specific settings using `.env` files. Do not commit secrets to the repository.
*   **Dependencies**: Add all new Python packages to the `requirements.txt` file.

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
*   Write tests for:
    *   **Models**: Ensure model properties and relationships work as expected.
    *   **Services**: Test business logic, especially AI-related functions.
    *   **API Endpoints**: Verify request/response behavior, status codes, and authentication.
*   Place test files in the `app/tests/` directory, following the `test_*.py` naming convention.
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
