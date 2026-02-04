"""Tests for Google OAuth authentication."""

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from user_auth.models import SocialAccount

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestGoogleOAuth:
    """Tests for Google OAuth authentication flow."""

    @pytest.fixture
    def auth_url_endpoint(self):
        return "/api/v1/auth/social/google/url/"

    @pytest.fixture
    def callback_endpoint(self):
        return "/api/v1/auth/social/google/"

    def test_google_auth_url_returns_authorization_url(
        self, api_client, auth_url_endpoint
    ):
        """Test that requesting Google auth URL returns authorization URL."""
        # Act
        response = api_client.get(auth_url_endpoint)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "auth_url" in response.data
        assert "https://accounts.google.com/o/oauth2" in response.data["auth_url"]

    def test_google_callback_with_valid_code_creates_user(
        self, api_client, callback_endpoint, mock_google_oauth
    ):
        """Test that OAuth callback with valid code creates a new user."""
        # Arrange
        callback_data = {"code": "valid-google-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

        # Verify OAuth API calls were made
        mock_google_oauth["post"].assert_called_once()
        mock_google_oauth["get"].assert_called_once()

        # Verify user was created
        user = User.objects.get(email="testuser@gmail.com")
        assert user.first_name == "Test"
        assert user.last_name == "User"

        # Verify social account was created
        social_account = SocialAccount.objects.get(user=user, provider="google")
        assert social_account.uid == "123456789"

    def test_google_callback_with_existing_email_links_account(
        self, api_client, callback_endpoint, mock_google_oauth
    ):
        """Test that OAuth callback with existing email links social account."""
        # Arrange
        # Create user with same email as Google account
        existing_user = User.objects.create_user(
            username="testuser@gmail.com",
            email="testuser@gmail.com",
            password="somepassword",
        )

        callback_data = {"code": "valid-google-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

        # Verify OAuth API calls were made
        mock_google_oauth["post"].assert_called_once()
        mock_google_oauth["get"].assert_called_once()

        # Verify social account was linked to existing user
        social_account = SocialAccount.objects.get(
            user=existing_user, provider="google"
        )
        assert social_account.uid == "123456789"

        # Verify no duplicate user was created
        assert User.objects.filter(email="testuser@gmail.com").count() == 1

    def test_google_callback_with_existing_social_account_logs_in(
        self, api_client, callback_endpoint, mock_google_oauth
    ):
        """Test that OAuth callback with existing social account logs user in."""
        # Arrange
        # Create user with Google social account
        user = User.objects.create_user(
            username="testuser@gmail.com",
            email="testuser@gmail.com",
        )
        SocialAccount.objects.create(
            user=user,
            provider="google",
            uid="123456789",
            extra_data={"email": "testuser@gmail.com"},
        )

        callback_data = {"code": "valid-google-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

        # Verify OAuth API calls were made
        mock_google_oauth["post"].assert_called_once()
        mock_google_oauth["get"].assert_called_once()

        # Verify no duplicate accounts were created
        assert SocialAccount.objects.filter(user=user, provider="google").count() == 1

    def test_google_callback_with_invalid_code_returns_400(
        self, api_client, callback_endpoint, mocker
    ):
        """Test that OAuth callback with invalid code returns 400."""
        # Arrange
        # Mock Google API to return error
        mock_response = mocker.MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        callback_data = {"code": "invalid-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_post.assert_called_once()

    def test_google_callback_without_code_returns_400(
        self, api_client, callback_endpoint
    ):
        """Test that OAuth callback without code returns 400."""
        # Act
        response = api_client.post(callback_endpoint, {})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_google_callback_without_email_returns_400(
        self, api_client, callback_endpoint, mocker
    ):
        """Test that OAuth callback without email in userinfo returns 400."""
        # Arrange
        # Mock Google API to return userinfo without email
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "fake-token"}

        mock_userinfo = mocker.MagicMock()
        mock_userinfo.status_code = 200
        mock_userinfo.json.return_value = {
            "id": "123456789",
            # No email field
            "given_name": "Test",
            "family_name": "User",
        }

        mock_post = mocker.patch("requests.post", return_value=mock_response)
        mock_get = mocker.patch("requests.get", return_value=mock_userinfo)

        callback_data = {"code": "valid-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        mock_post.assert_called_once()
        mock_get.assert_called_once()


class TestGoogleOAuthPermissions:
    """Test that OAuth endpoints have correct permissions."""

    def test_google_auth_url_allows_anonymous_access(self, api_client):
        """Test that Google auth URL endpoint allows anonymous access."""
        # Act
        response = api_client.get("/api/v1/auth/social/google/url/")

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_google_callback_allows_anonymous_access(self, api_client):
        """Test that Google callback endpoint allows anonymous access."""
        # Act
        response = api_client.post("/api/v1/auth/social/google/", {})

        # Assert
        # Should not return 401/403 (even if 400 for missing code)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN


class TestGoogleOAuthEmailVerification:
    """Test suite to ensure Google SSO users have verified email status."""

    @pytest.fixture
    def callback_endpoint(self):
        return "/api/v1/auth/social/google/"

    def test_new_google_user_has_verified_email_token(
        self, api_client, callback_endpoint, mock_google_oauth
    ):
        """Test that new Google SSO users get a verified EmailVerificationToken."""
        # Arrange
        callback_data = {"code": "valid-google-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

        # Verify user was created
        user = User.objects.get(email="testuser@gmail.com")
        assert user.is_active is True

        # CRITICAL: Verify EmailVerificationToken exists and is marked verified
        assert hasattr(user, "verification_token"), (
            "Google SSO user must have EmailVerificationToken"
        )
        assert user.verification_token.verified_at is not None, (
            "Google SSO user's EmailVerificationToken must be verified immediately"
        )

    def test_existing_unverified_user_verified_on_google_login(
        self, api_client, callback_endpoint, mock_google_oauth, unverified_user
    ):
        """Test that existing unverified users get verified when logging in via Google."""
        # Arrange
        # Update the unverified user to have the same email as Google returns
        unverified_user.email = "testuser@gmail.com"
        unverified_user.username = "testuser@gmail.com"
        unverified_user.save()

        # Verify user is unverified
        assert unverified_user.is_active is False
        assert unverified_user.verification_token.verified_at is None

        callback_data = {"code": "valid-google-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # After Google login, user should be verified
        unverified_user.refresh_from_db()
        assert unverified_user.is_active is True, (
            "Existing unverified user should be activated after Google SSO login"
        )
        assert unverified_user.verification_token.verified_at is not None, (
            "Existing user's email should be verified after Google SSO login"
        )

    def test_existing_verified_user_not_affected(
        self, api_client, callback_endpoint, mock_google_oauth, verified_user
    ):
        """Test that existing verified users aren't negatively affected."""
        # Arrange
        # Update the verified user to have the same email as Google returns
        verified_user.email = "testuser@gmail.com"
        verified_user.username = "testuser@gmail.com"
        verified_user.save()

        original_verified_at = verified_user.verification_token.verified_at
        assert original_verified_at is not None

        callback_data = {"code": "valid-google-code"}

        # Act
        response = api_client.post(callback_endpoint, callback_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify nothing changed for already-verified user
        verified_user.refresh_from_db()
        assert verified_user.is_active is True
        # Verification timestamp should not be modified
        assert verified_user.verification_token.verified_at == original_verified_at

    def test_google_user_can_access_protected_endpoints(
        self,
        api_client,
        callback_endpoint,
        mock_google_oauth,
        mock_agent_call,
        mock_gcs_signed_url,
    ):
        """Integration test: Google SSO user should access protected resources."""
        # Arrange - Create user via Google OAuth
        callback_data = {"code": "valid-google-code"}
        response = api_client.post(callback_endpoint, callback_data)

        assert response.status_code == status.HTTP_200_OK
        access_token = response.data["access"]

        # Act - Try to access protected diagram endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.post("/api/v1/diagrams/", {"text": "test diagram"})

        # Assert - Should succeed, not return 401/403
        assert response.status_code in [200, 201], (
            f"Google SSO user should access protected endpoints, got {response.status_code}"
        )
