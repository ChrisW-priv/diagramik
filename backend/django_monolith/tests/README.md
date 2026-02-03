# Backend Testing Guide

This directory contains comprehensive tests for the Django backend API.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── factories.py                   # Factory Boy model factories
├── test_auth/                     # Authentication tests
│   ├── test_registration.py
│   ├── test_login.py
│   ├── test_jwt_tokens.py
│   └── test_google_oauth.py
├── test_diagrams/                 # Diagram CRUD tests
│   ├── test_diagram_crud.py
│   └── test_diagram_versions.py
├── test_rate_limiting/            # Quota and rate limiting tests
│   ├── test_quota_enforcement.py
│   └── test_period_calculations.py
└── test_integration/              # End-to-end integration tests
    └── test_full_user_journey.py
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
# From project root
task be:sync
```

### Run All Tests

```bash
# From django_monolith directory
pytest

# Or from backend root
pytest django_monolith/tests/
```

### Run Specific Test Categories

```bash
# Authentication tests only
pytest tests/test_auth/

# Diagram tests only
pytest tests/test_diagrams/

# Rate limiting tests only
pytest tests/test_rate_limiting/

# Integration tests only
pytest tests/test_integration/
```

### Run Specific Test File

```bash
pytest tests/test_auth/test_login.py
```

### Run Specific Test

```bash
pytest tests/test_auth/test_login.py::TestLogin::test_login_with_valid_credentials_returns_tokens
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View report
open htmlcov/index.html
```

### Run in Parallel (Faster)

```bash
# Use all CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4
```

### Run Only Fast Tests

```bash
# Skip slow tests
pytest -m "not slow"
```

### Run Only Integration Tests

```bash
pytest -m integration
```

## Test Markers

Tests are organized with markers for easy filtering:

- `unit` - Unit tests (isolated components)
- `integration` - Integration tests (multiple components)
- `e2e` - End-to-end tests (complete user journeys)
- `slow` - Slow tests (can be skipped for quick checks)
- `requires_postgres` - Tests that need PostgreSQL (not SQLite)

## Database Strategy

### SQLite for Most Tests

By default, tests use SQLite for speed. This is configured automatically by pytest-django.

### PostgreSQL for Specific Tests

Some tests require PostgreSQL features. Mark them with `@pytest.mark.requires_postgres`:

```python
@pytest.mark.requires_postgres
def test_postgres_specific_feature():
    # Test code
```

To run PostgreSQL tests in CI:

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
pytest -m requires_postgres
```

## Mocking Strategy

### What's Mocked

The following external dependencies are mocked in all tests:

1. **FastAgent / MCP Service** - `mock_agent_call` fixture
1. **Google Cloud Storage** - `mock_gcs_signed_url` fixture
1. **Email Sending** - `mock_send_mail` fixture
1. **Google OAuth API** - `mock_google_oauth` fixture

### Using Fixtures

All mocks are available as pytest fixtures:

```python
def test_create_diagram(authenticated_client, mock_agent_call):
    response = authenticated_client.post('/api/v1/diagrams/', {'text': 'test'})
    assert response.status_code == 201
    mock_agent_call.assert_called_once()
```

## Time-Based Testing

Rate limiting tests use `freezegun` to manipulate time:

```python
from freezegun import freeze_time

@freeze_time("2026-01-01 12:00:00")
def test_daily_quota_resets():
    # Create requests on day 1
    ...

    # Travel to day 2
    with freeze_time("2026-01-02 12:00:00"):
        # Quota should be reset
        ...
```

## Authentication in Tests

### Force Authentication (Recommended)

Most tests use force authentication for speed:

```python
def test_something(authenticated_client):
    # Client is already authenticated
    response = authenticated_client.get('/api/v1/diagrams/')
```

### Real JWT Tokens

For token-specific tests:

```python
def test_token_refresh(api_client, jwt_tokens):
    response = api_client.post('/api/v1/auth/token/refresh/', {
        'refresh': jwt_tokens['refresh']
    })
```

## Factory Boy Usage

Create test data with factories:

```python
from tests.factories import UserFactory, DiagramFactory

def test_user_diagrams():
    user = UserFactory(email="custom@example.com")
    diagram = DiagramFactory(owner=user, title="Custom Title")
```

## Common Fixtures

Available in `conftest.py`:

- `api_client` - Unauthenticated API client
- `user` - Test user with password 'testpass123'
- `authenticated_client` - Pre-authenticated API client
- `jwt_tokens` - JWT tokens dict with 'access' and 'refresh'
- `mock_agent_call` - Mocked agent function
- `mock_gcs_signed_url` - Mocked GCS signed URL generation
- `mock_send_mail` - Mocked email sending
- `mock_google_oauth` - Mocked Google OAuth API

## Writing New Tests

### 1. Follow AAA Pattern

```python
def test_something():
    # Arrange - Set up test data
    user = UserFactory()

    # Act - Perform the action
    response = client.post('/api/endpoint/', data)

    # Assert - Check the results
    assert response.status_code == 201
```

### 2. Use Descriptive Names

```python
# Good
def test_login_with_invalid_password_returns_401():
    ...

# Bad
def test_login():
    ...
```

### 3. One Assertion Per Test (When Possible)

```python
# Good
def test_registration_creates_user():
    response = api_client.post('/register/', data)
    assert User.objects.filter(email=data['email']).exists()

def test_registration_returns_201():
    response = api_client.post('/register/', data)
    assert response.status_code == 201

# Acceptable (related assertions)
def test_registration_success():
    response = api_client.post('/register/', data)
    assert response.status_code == 201
    assert 'access' in response.data
```

### 4. Use Parametrize for Similar Tests

```python
@pytest.mark.parametrize("password,expected_status", [
    ("short", 400),
    ("", 400),
    ("validpass123", 201),
])
def test_password_validation(password, expected_status):
    # Test implementation
```

## CI/CD Integration

### GitHub Actions Example

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    - name: Install dependencies
      run: |
        pip install uv
        cd backend && uv sync
    - name: Run tests
      run: |
        cd backend/django_monolith
        pytest --cov --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests Hang on Agent Calls

Make sure `mock_agent_call` fixture is included:

```python
def test_create_diagram(authenticated_client, mock_agent_call):
    ...
```

### Database Locked Errors

Run tests with `--reuse-db` or serially:

```bash
pytest --reuse-db
# or
pytest -n 0
```

### Import Errors

Make sure Django settings are configured:

```bash
export DJANGO_SETTINGS_MODULE=backend.settings
pytest
```

## Coverage Goals

- Overall: 85%+
- Critical paths (auth, diagram creation, rate limiting): 90%+

Check coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Performance

Target test execution time: < 1 minute for full suite

Tips for fast tests:

- Use SQLite (default)
- Mock external services (done automatically)
- Use `pytest-xdist` for parallel execution
- Use `--reuse-db` to skip database recreation

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [Factory Boy documentation](https://factoryboy.readthedocs.io/)
- [freezegun documentation](https://github.com/spulec/freezegun)
