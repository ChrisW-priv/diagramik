"""Shared pytest fixtures for all tests."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .factories import UserFactory


@pytest.fixture
def api_client():
    """Provide an API client for making requests."""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user with default password 'testpass123'."""
    return UserFactory()


@pytest.fixture
def authenticated_client(api_client, user):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def jwt_tokens(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


@pytest.fixture
def auth_headers(jwt_tokens):
    """Generate authorization headers with JWT token."""
    return {"HTTP_AUTHORIZATION": f"Bearer {jwt_tokens['access']}"}


@pytest.fixture
def mock_agent_call(mocker):
    """Mock the agent call to avoid external dependencies."""
    mock_result = mocker.MagicMock()
    mock_result.diagram_title = "Test Diagram"
    mock_result.media_uri = "gs://test-bucket/test-image.png"
    mock_result.history_json = '{"history": []}'

    return mocker.patch(
        "diagrams_assistant.views.agent",
        return_value=mock_result,
    )


@pytest.fixture
def mock_gcs_signed_url(mocker):
    """Mock GCS signed URL generation."""
    return mocker.patch(
        "diagrams_assistant.views.create_publicly_accessible_url",
        return_value="https://storage.googleapis.com/test-bucket/signed-url",
    )


@pytest.fixture
def mock_send_mail(mocker):
    """Mock email sending."""
    return mocker.patch("django.core.mail.send_mail", return_value=1)


@pytest.fixture
def mock_google_oauth(mocker):
    """Mock Google OAuth API responses."""
    # Mock the requests to Google OAuth
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "fake-google-token",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    mock_userinfo_response = mocker.MagicMock()
    mock_userinfo_response.status_code = 200
    mock_userinfo_response.json.return_value = {
        "id": "123456789",
        "email": "testuser@gmail.com",
        "verified_email": True,
        "given_name": "Test",
        "family_name": "User",
    }

    mock_requests = mocker.patch("requests.post", return_value=mock_response)
    mock_get = mocker.patch("requests.get", return_value=mock_userinfo_response)

    return {"post": mock_requests, "get": mock_get}


@pytest.fixture(autouse=True)
def set_test_settings(settings):
    """Configure Django settings for tests."""
    # Use DEBUG mode features in tests (no email verification)
    settings.ACCOUNT_EMAIL_VERIFICATION = "optional"
    settings.DEBUG = True

    # Mock service account key path
    settings.SIGNED_URL_SA_KEY_FILENAME = "/tmp/test-sa-key.json"

    # Set test frontend URL
    settings.FRONTEND_URL = "http://localhost:3000"

    return settings


@pytest.fixture
def site_settings():
    """Create or get site settings singleton."""
    from site_settings.models import SiteSettings

    return SiteSettings.load()


@pytest.fixture
def create_test_sa_key(tmp_path, mocker):
    """Create a temporary service account key file for GCS mocking."""
    sa_key_content = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        "client_email": "test@test.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    import json

    key_file = tmp_path / "test-sa-key.json"
    key_file.write_text(json.dumps(sa_key_content))

    # Mock the service account credentials
    mocker.patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mocker.MagicMock(),
    )

    return str(key_file)
