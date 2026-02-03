"""Tests for user registration."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestRegistration:
    """Tests for the registration endpoint."""

    @pytest.fixture
    def registration_url(self):
        return "/api/v1/auth/registration/"

    @pytest.fixture
    def valid_registration_data(self):
        return {
            "email": "newuser@example.com",
            "password1": "securepassword",
            "password2": "securepassword",
            "first_name": "New",
        }

    def test_registration_with_valid_data_creates_user(
        self, api_client, registration_url, valid_registration_data
    ):
        """Test that registration with valid data creates a user."""
        # Arrange - data already in fixture

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email=valid_registration_data["email"]).exists()

        user = User.objects.get(email=valid_registration_data["email"])
        assert user.first_name == valid_registration_data["first_name"]
        assert user.check_password(valid_registration_data["password1"])
        assert user.is_active

    def test_registration_returns_jwt_tokens_in_dev_mode(
        self, api_client, registration_url, valid_registration_data, settings
    ):
        """Test that registration returns JWT tokens when email verification is not required."""
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == valid_registration_data["email"]

    def test_registration_sends_verification_email_in_production(
        self, api_client, registration_url, valid_registration_data, settings, mocker
    ):
        """Test that registration sends verification email in production mode."""
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        # Mock send_mail to return success
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert "detail" in response.data
        assert "Verification email sent" in response.data["detail"]
        mock_send_mail.assert_called_once()

    def test_registration_creates_inactive_user_when_verification_mandatory(
        self, api_client, registration_url, valid_registration_data, settings, mocker
    ):
        """Test that user is created with is_active=False when verification is mandatory."""
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email=valid_registration_data["email"])
        assert user.is_active is False

    def test_registration_creates_verification_token_record(
        self, api_client, registration_url, valid_registration_data, settings, mocker
    ):
        """Test that registration creates EmailVerificationToken record."""
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email=valid_registration_data["email"])
        assert hasattr(user, "verification_token")
        assert user.verification_token.resend_count == 0
        assert user.verification_token.verified_at is None

    def test_registration_deletes_user_if_email_send_fails(
        self, api_client, registration_url, valid_registration_data, settings, mocker
    ):
        """Test that user is deleted if verification email send fails."""
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        # Mock send_mail to return failure
        mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=0
        )

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "could not be sent" in response.data["detail"].lower()
        # User should not exist in database
        assert not User.objects.filter(email=valid_registration_data["email"]).exists()

    def test_registration_with_duplicate_email_returns_400(
        self, api_client, registration_url, valid_registration_data, user
    ):
        """Test that registration with existing email returns 400."""
        # Arrange
        valid_registration_data["email"] = user.email

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "already exists" in response.data["email"][0].lower()

    def test_registration_with_unverified_duplicate_email_shows_helpful_message(
        self, api_client, registration_url, valid_registration_data, unverified_user
    ):
        """Test that registration with unverified duplicate email shows helpful message."""
        # Arrange
        valid_registration_data["email"] = unverified_user.email

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "unverified account" in response.data["email"][0].lower()
        assert "verification link" in response.data["email"][0].lower()

    def test_registration_with_short_password_returns_400(
        self, api_client, registration_url, valid_registration_data
    ):
        """Test that registration with short password returns 400."""
        # Arrange
        valid_registration_data["password1"] = "short"
        valid_registration_data["password2"] = "short"

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password1" in response.data
        assert "at least 8 characters" in response.data["password1"][0].lower()

    def test_registration_with_mismatched_passwords_returns_400(
        self, api_client, registration_url, valid_registration_data
    ):
        """Test that registration with mismatched passwords returns 400."""
        # Arrange
        valid_registration_data["password2"] = "differentpass123"

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password2" in response.data
        assert "do not match" in response.data["password2"][0].lower()

    def test_registration_without_email_returns_400(
        self, api_client, registration_url, valid_registration_data
    ):
        """Test that registration without email returns 400."""
        # Arrange
        del valid_registration_data["email"]

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_registration_without_password_returns_400(
        self, api_client, registration_url, valid_registration_data
    ):
        """Test that registration without password returns 400."""
        # Arrange
        del valid_registration_data["password1"]

        # Act
        response = api_client.post(registration_url, valid_registration_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password1" in response.data
