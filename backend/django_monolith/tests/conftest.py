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
    """Mock the agent call to avoid external dependencies.

    Works with both old agent (diagrams_assistant.agent) and new agent (agent module).
    Returns an async coroutine since agent is called with asyncio.run().
    """

    mock_result = mocker.MagicMock()
    mock_result.diagram_title = "Test Diagram"
    mock_result.media_uri = "gs://test-bucket/test-image.png"
    mock_result.history_json = '{"history": []}'

    # Create a tracker for agent calls
    call_tracker = mocker.MagicMock()

    # Create async wrapper for the mock result that tracks calls
    async def async_agent(*args, **kwargs):
        call_tracker(*args, **kwargs)
        return mock_result

    # Create a mock for the FastAgent context manager
    mock_fast_agent_instance = mocker.MagicMock()
    mock_fast_agent_instance.diagram_generator.send = mocker.AsyncMock()

    # Create proper mock structure for message_history
    # The agent expects: message_history[-2].tool_results to be a dict
    # where each value has .content[0].text as a JSON string
    mock_content = mocker.MagicMock()
    mock_content.text = (
        '{"title": "Test Diagram", "uri": "gs://test-bucket/test-image.png"}'
    )

    mock_tool_result = mocker.MagicMock()
    mock_tool_result.content = [mock_content]

    # Use PropertyMock to ensure tool_results is treated as an attribute
    mock_message = mocker.MagicMock()
    type(mock_message).tool_results = mocker.PropertyMock(
        return_value={"test_tool": mock_tool_result}
    )

    mock_fast_agent_instance.diagram_generator.message_history = [
        mock_message,  # index 0, which is -2 (second to last - has tool results)
        mocker.MagicMock(),  # index 1, which is -1 (last message)
    ]
    mock_fast_agent_instance.diagram_generator.load_message_history = mocker.MagicMock()

    # Create async context manager mock
    class MockAsyncContext:
        async def __aenter__(self):
            return mock_fast_agent_instance

        async def __aexit__(self, *args):
            return None

    # Mock FastAgent.run() to return our mock context
    mocker.patch(
        "diagrams_assistant.agent.agent.fast.run", return_value=MockAsyncContext()
    )

    # Mock to_json and from_json to avoid serialization issues
    mocker.patch(
        "diagrams_assistant.agent.agent.to_json", return_value='{"history": []}'
    )
    mocker.patch("diagrams_assistant.agent.agent.from_json", return_value=[])

    # Patch the agent at both the module level and the package level
    # The views import from diagrams_assistant.agent (package __init__.py)
    # which re-exports from diagrams_assistant.agent.agent (module)
    mocker.patch("diagrams_assistant.agent.agent.agent", side_effect=async_agent)
    mocker.patch("diagrams_assistant.agent.agent", new=async_agent)

    # Also mock the new agent module
    try:
        mocker.patch(
            "agent.core.agent_orchestrator.agent",
            side_effect=async_agent,
        )
    except (ImportError, ModuleNotFoundError):
        pass

    return call_tracker


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
def set_test_settings(settings, monkeypatch):
    """Configure Django settings for tests."""
    # Use DEBUG mode features in tests (no email verification)
    settings.ACCOUNT_EMAIL_VERIFICATION = "optional"
    settings.DEBUG = True

    # Mock service account key path
    settings.SIGNED_URL_SA_KEY_FILENAME = "/tmp/test-sa-key.json"

    # Set test frontend URL
    settings.FRONTEND_URL = "http://localhost:3000"

    # Set MCP service URL for FastAgent
    monkeypatch.setenv("MCP_SERVICE_URL", "http://localhost:8080")

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


@pytest.fixture
def unverified_user():
    """Create an unverified user (is_active=False)."""
    from user_auth.models import EmailVerificationToken

    user = UserFactory(is_active=False)
    EmailVerificationToken.objects.create(user=user, resend_count=0)
    return user


@pytest.fixture
def verified_user():
    """Create a verified user with verification token marked as verified."""
    from user_auth.models import EmailVerificationToken

    user = UserFactory(is_active=True)
    token = EmailVerificationToken.objects.create(user=user, resend_count=0)
    token.mark_verified()
    return user


@pytest.fixture
def user_with_max_resends():
    """Create unverified user who has exhausted resend attempts."""
    from user_auth.models import EmailVerificationToken

    user = UserFactory(is_active=False)
    EmailVerificationToken.objects.create(user=user, resend_count=5)
    return user


@pytest.fixture
def mock_new_agent_clarification_needed(mocker, site_settings):
    """Mock new agent raising ClarificationNeeded exception.

    Only works when use_new_agent feature flag is enabled.
    """

    # Enable new agent
    site_settings.use_new_agent = True
    site_settings.save()

    # Create a mock exception that mimics ClarificationNeeded
    class MockClarificationNeeded(Exception):
        def __init__(self, question):
            self.clarification_question = question
            super().__init__(question)

    # Make the exception have the right name
    MockClarificationNeeded.__name__ = "ClarificationNeeded"

    # Create async wrapper that raises the exception
    async def async_agent_raises(*args, **kwargs):
        raise MockClarificationNeeded("What type of diagram do you want?")

    # Mock the new agent module
    mock_module = mocker.MagicMock()
    mock_module.ClarificationNeeded = MockClarificationNeeded
    mock_module.CodeGenerationError = Exception

    # Patch the agent module in sys.modules first
    mocker.patch.dict("sys.modules", {"agent": mock_module})

    # Then patch the actual agent function
    mock_agent = mocker.patch(
        "agent.core.agent_orchestrator.agent",
        side_effect=async_agent_raises,
    )
    mock_module.agent = async_agent_raises

    return mock_agent


@pytest.fixture
def mock_new_agent_code_generation_error(mocker, site_settings):
    """Mock new agent raising CodeGenerationError exception.

    Only works when use_new_agent feature flag is enabled.
    """

    # Enable new agent
    site_settings.use_new_agent = True
    site_settings.save()

    # Create a mock exception that mimics CodeGenerationError
    class MockCodeGenerationError(Exception):
        def __init__(self, message, validation_errors=None):
            self.validation_errors = validation_errors or []
            super().__init__(message)

    # Make the exception have the right name
    MockCodeGenerationError.__name__ = "CodeGenerationError"

    # Create async wrapper that raises the exception
    async def async_agent_raises(*args, **kwargs):
        raise MockCodeGenerationError(
            "Failed to generate valid code", validation_errors=["Syntax error"]
        )

    # Mock the new agent module
    mock_module = mocker.MagicMock()
    mock_module.ClarificationNeeded = Exception
    mock_module.CodeGenerationError = MockCodeGenerationError

    # Patch the agent module in sys.modules first
    mocker.patch.dict("sys.modules", {"agent": mock_module})

    # Then patch the actual agent function
    mock_agent = mocker.patch(
        "agent.core.agent_orchestrator.agent",
        side_effect=async_agent_raises,
    )
    mock_module.agent = async_agent_raises

    return mock_agent
