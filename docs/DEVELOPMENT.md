# MyHaven Backend Development Guide

**Version:** 1.1 | **Updated:** May 15, 2026

## Installation

### Prerequisites
- Python 3.10 or higher.
- PostgreSQL.
- Virtual environment tool.

### Setup Process
1. Navigate to the `backend` directory.
2. Initialize and activate a virtual environment.
3. Install requirements: `pip install -r requirements.txt`.
4. Install development tools: `pip install black ruff pytest pytest-django pytest-cov`.

### Database Configuration
1. Configure the `.env` file.
2. Apply migrations: `python manage.py migrate`.
3. Create an administrative user: `python manage.py createsuperuser`.

### Execution
Start the development server: `python manage.py runserver`.
- Server: [http://localhost:8000/](http://localhost:8000/)
- API Documentation: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

## Development Workflow

### Test-Driven Development (TDD)
1. Write a failing test in `tests.py`.
2. Implement the minimum code to pass the test.
3. Refactor the implementation to meet quality standards.

### Testing Commands
- Execute all tests: `python manage.py test`.
- Execute app-specific tests: `python manage.py test <app_name>.tests`.
Current suite consists of 12 tests.

### Pre-commit Verification
Run the verification script before committing changes:
- Windows: `.\run_checks.ps1`
- Unix: `./run_checks.sh`

## Coding Standards
- **Formatting**: Black formatter.
- **Linting**: Ruff linter.
- **Type Hints**: Required for service and repository methods.
- **Docstrings**: Required for classes and public methods.
- **Naming**: `snake_case` for variables and functions; `PascalCase` for classes.

## Implementation Guidelines
- **Models**: Defined in `models.py`.
- **Logic**: Implemented in `services.py`.
- **Queries**: Contained in `repositories.py`.
- **Endpoints**: Managed in `views.py` and `serializers.py`.

## Troubleshooting

| Problem | Action |
|---------|--------|
| Database Connection | Verify `.env` settings and PostgreSQL status. |
| Failed Tests | Ensure migrations are applied and the environment is isolated. |
| Missing Imports | Verify virtual environment activation. |
