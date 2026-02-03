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

    @pytest.fixture
    def user_with_password(self):
        """Create a user with a known password."""
        return UserFactory(password="testpass123")

    def test_login_with_valid_credentials_returns_tokens(
        self, api_client, login_url, user_with_password
    ):
        """Test that login with valid credentials returns JWT tokens."""
        # Arrange
        credentials = {
            "email": user_with_password.email,
            "password": "testpass123",
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

    def test_login_returns_user_data(self, api_client, login_url, user_with_password):
        """Test that login returns user information."""
        # Arrange
        credentials = {
            "email": user_with_password.email,
            "password": "testpass123",
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        user_data = response.data["user"]
        assert user_data["email"] == user_with_password.email
        assert user_data["first_name"] == user_with_password.first_name

    def test_login_with_invalid_email_returns_401(self, api_client, login_url):
        """Test that login with non-existent email returns 401."""
        # Arrange
        credentials = {
            "email": "nonexistent@example.com",
            "password": "testpass123",
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        assert "invalid" in response.data["detail"].lower()

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
        assert "invalid" in response.data["detail"].lower()

    def test_login_with_inactive_user_returns_401(
        self, api_client, login_url, user_with_password
    ):
        """Test that login with inactive user returns 401."""
        # Arrange
        user_with_password.is_active = False
        user_with_password.save()

        credentials = {
            "email": user_with_password.email,
            "password": "testpass123",
        }

        # Act
        response = api_client.post(login_url, credentials)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data
        assert "disabled" in response.data["detail"].lower()

    def test_login_without_email_returns_400(self, api_client, login_url):
        """Test that login without email returns 400."""
        # Arrange
        credentials = {"password": "testpass123"}

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
