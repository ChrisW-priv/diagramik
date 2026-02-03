"""Tests for user login."""

import pytest
from rest_framework import status
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestLogin:
    """Tests for the login endpoint."""

    @pytest.fixture
    def login_url(self):
        return "/api/v1/auth/login/"

    @property
    def user_password(self):
        return "testpass123"

    @pytest.fixture
    def user_with_password(self):
        """Create a user with a known password."""
        return UserFactory(password=self.user_password)

    def test_login_with_valid_credentials_returns_tokens(
        self, api_client, login_url, user_with_password
    ):
        """Test that login with valid credentials returns JWT tokens."""
        # Arrange
        credentials = {
            "email": user_with_password.email,
            "password": self.user_password,
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        user_data = response.data["user"]
        assert user_data["email"] == user_with_password.email
        assert user_data["first_name"] == user_with_password.first_name

    def test_login_with_invalid_email_returns_401(self, api_client, login_url):
        """Test that login with non-existent email returns 401."""
        # Arrange
        credentials = {
            "email": "nonexistent@example.com",
            "password": self.user_password,
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        assert response.data["detail"] == "Invalid email or password."

    def test_login_with_invalid_password_returns_401(
        self, api_client, login_url, user_with_password
    ):
        """Test that login with wrong password returns 401."""
        # Arrange
        credentials = {
            "email": user_with_password.email,
            "password": "wrongpassword",
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        assert response.data["detail"] == "Invalid email or password."

    def test_login_with_unverified_user_returns_403(
        self, api_client, login_url, unverified_user
    ):
        """Test that login with unverified user returns 403 with EMAIL_NOT_VERIFIED."""
        # Arrange
        unverified_user.set_password(self.user_password)
        unverified_user.save()

        credentials = {
            "email": unverified_user.email,
            "password": self.user_password,
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_code"] == "EMAIL_NOT_VERIFIED"
        assert "verify your email" in response.data["detail"].lower()

    def test_login_with_unverified_user_includes_resend_information(
        self, api_client, login_url, unverified_user
    ):
        """Test that unverified user login includes resend endpoint."""
        # Arrange
        unverified_user.set_password(self.user_password)
        unverified_user.save()

        credentials = {
            "email": unverified_user.email,
            "password": self.user_password,
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["action_required"] == "verify_email"
        assert response.data["resend_endpoint"] == "/api/v1/auth/resend-verification/"

    def test_login_with_admin_disabled_account_returns_403(
        self, api_client, login_url, user_with_password
    ):
        """Test that login with admin-disabled account returns ACCOUNT_DISABLED error."""
        # Arrange
        user_with_password.is_active = False
        user_with_password.save()
        # Don't create verification token - simulates admin-disabled account

        credentials = {
            "email": user_with_password.email,
            "password": self.user_password,
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_code"] == "ACCOUNT_DISABLED"
        assert "disabled" in response.data["detail"].lower()

    def test_login_distinguishes_unverified_vs_disabled(
        self, api_client, login_url, unverified_user, user_with_password
    ):
        """Test that login distinguishes between unverified and disabled accounts."""
        # Arrange - Unverified user
        unverified_user.set_password(self.user_password)
        unverified_user.save()

        # Arrange - Disabled user (no verification token)
        user_with_password.is_active = False
        user_with_password.save()

        # Act 1 - Login with unverified user
        response1 = api_client.post(
            login_url,
            {"email": unverified_user.email, "password": self.user_password},
        )

        # Act 2 - Login with disabled user
        response2 = api_client.post(
            login_url,
            {"email": user_with_password.email, "password": self.user_password},
        )

        # Assert - Different error codes
        assert response1.data["error_code"] == "EMAIL_NOT_VERIFIED"
        assert response2.data["error_code"] == "ACCOUNT_DISABLED"

    def test_login_without_email_returns_400(self, api_client, login_url):
        """Test that login without email returns 400."""
        # Arrange
        credentials = {"password": self.user_password}

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data

    def test_login_without_password_returns_400(
        self, api_client, login_url, user_with_password
    ):
        """Test that login without password returns 400."""
        # Arrange
        credentials = {"email": user_with_password.email}

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
