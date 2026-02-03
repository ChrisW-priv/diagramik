"""Unit tests for email verification endpoint."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status


User = get_user_model()

pytestmark = pytest.mark.django_db


class TestVerifyEmailView:
    """Tests for VerifyEmailView."""

    @pytest.fixture
    def verify_url(self):
        return "/api/v1/auth/verify-email/"

    def test_verify_email_with_valid_token_via_post(
        self, api_client, unverified_user, verify_url
    ):
        """Test email verification with valid token via POST request."""
        # Arrange
        token = default_token_generator.make_token(unverified_user)
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert "Email verified successfully" in response.data["detail"]

        # Verify user is now active
        unverified_user.refresh_from_db()
        assert unverified_user.is_active is True

        # Verify token marked as verified
        unverified_user.verification_token.refresh_from_db()
        assert unverified_user.verification_token.verified_at is not None

    def test_verify_email_with_valid_token_via_get(
        self, api_client, unverified_user, verify_url
    ):
        """Test email verification with valid token via GET request (clicking email link)."""
        # Arrange
        token = default_token_generator.make_token(unverified_user)
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))

        # Act
        response = api_client.get(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

        unverified_user.refresh_from_db()
        assert unverified_user.is_active is True

    def test_verify_email_already_verified_user(
        self, api_client, verified_user, verify_url
    ):
        """Test verification of already verified user returns success message."""
        # Arrange
        token = default_token_generator.make_token(verified_user)
        uid = urlsafe_base64_encode(force_bytes(verified_user.pk))

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "already verified" in response.data["detail"].lower()

    def test_verify_email_missing_uid(self, api_client, verify_url):
        """Test verification without uid returns 400."""
        # Act
        response = api_client.post(verify_url, {"token": "sometoken"})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "uid" in response.data

    def test_verify_email_missing_token(self, api_client, verify_url):
        """Test verification without token returns 400."""
        # Act
        response = api_client.post(verify_url, {"uid": "someuid"})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.data

    def test_verify_email_invalid_uid(self, api_client, verify_url):
        """Test verification with invalid uid returns 400."""
        # Act
        response = api_client.post(
            verify_url, {"uid": "invalid-uid", "token": "sometoken"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification link" in response.data["detail"]

    def test_verify_email_malformed_uid(self, api_client, unverified_user, verify_url):
        """Test verification with malformed uid (invalid base64) returns 400."""
        # Arrange
        token = default_token_generator.make_token(unverified_user)
        malformed_uid = "not-valid-base64!!!"

        # Act
        response = api_client.post(verify_url, {"uid": malformed_uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification link" in response.data["detail"]

    def test_verify_email_nonexistent_user(self, api_client, verify_url):
        """Test verification with uid for non-existent user returns 400."""
        # Arrange
        fake_uid = urlsafe_base64_encode(force_bytes(999999))

        # Act
        response = api_client.post(verify_url, {"uid": fake_uid, "token": "sometoken"})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification link" in response.data["detail"]

    def test_verify_email_invalid_token(self, api_client, unverified_user, verify_url):
        """Test verification with invalid token returns 400."""
        # Arrange
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))
        invalid_token = "invalid-token-12345"

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": invalid_token})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.data["detail"]

    def test_verify_email_expired_token(
        self, api_client, unverified_user, verify_url, mocker
    ):
        """Test verification with expired token returns 400."""
        # Arrange
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))
        token = default_token_generator.make_token(unverified_user)

        # Mock check_token to return False (expired)
        mocker.patch(
            "user_auth.views.email_password_auth.verify_email.default_token_generator.check_token",
            return_value=False,
        )

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.data["detail"].lower()

    def test_verify_email_invalidated_token(
        self, api_client, unverified_user, verify_url
    ):
        """Test verification with invalidated token (after resend) returns 400."""
        # Arrange
        token = default_token_generator.make_token(unverified_user)
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))

        # Invalidate the token (simulate resend was requested)
        unverified_user.verification_token.invalidate()

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalidated" in response.data["detail"].lower()

    def test_verify_email_returns_jwt_tokens(
        self, api_client, unverified_user, verify_url
    ):
        """Test that verification returns valid JWT tokens for immediate login."""
        # Arrange
        token = default_token_generator.make_token(unverified_user)
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert isinstance(response.data["access"], str)
        assert isinstance(response.data["refresh"], str)
        assert len(response.data["access"]) > 20  # JWT tokens are long strings

    def test_verify_email_returns_user_data(
        self, api_client, unverified_user, verify_url
    ):
        """Test that verification returns user data."""
        # Arrange
        token = default_token_generator.make_token(unverified_user)
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data
        assert response.data["user"]["email"] == unverified_user.email
        assert response.data["user"]["pk"] == unverified_user.pk

    def test_full_registration_to_verification_flow(self, api_client, settings, mocker):
        """Test complete flow: register → receive token → verify → login."""
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )

        registration_data = {
            "email": "newuser@example.com",
            "password1": "securepass123",
            "password2": "securepass123",
            "first_name": "New",
        }

        # Act 1: Register
        register_response = api_client.post(
            "/api/v1/auth/registration/", registration_data
        )

        # Assert 1: Registration successful
        assert register_response.status_code == status.HTTP_201_CREATED
        assert "Verification email sent" in register_response.data["detail"]
        mock_send_mail.assert_called_once()

        # Get user and generate verification token
        user = User.objects.get(email=registration_data["email"])
        assert user.is_active is False
        assert hasattr(user, "verification_token")

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act 2: Verify email
        verify_response = api_client.post(
            "/api/v1/auth/verify-email/", {"uid": uid, "token": token}
        )

        # Assert 2: Verification successful
        assert verify_response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True

        # Act 3: Login with credentials
        login_response = api_client.post(
            "/api/v1/auth/login/",
            {
                "email": registration_data["email"],
                "password": registration_data["password1"],
            },
        )

        # Assert 3: Login successful
        assert login_response.status_code == status.HTTP_200_OK
        assert "access" in login_response.data

    def test_verify_email_user_without_verification_token(self, api_client, verify_url):
        """Test verification for user without EmailVerificationToken record (edge case)."""
        # Arrange - Create user without verification token
        from tests.factories import UserFactory

        user = UserFactory(is_active=False)
        # Note: No EmailVerificationToken created

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = api_client.post(verify_url, {"uid": uid, "token": token})

        # Assert - Should still verify successfully
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True
