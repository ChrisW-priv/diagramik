"""Tests for JWT token functionality."""

import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from freezegun import freeze_time

pytestmark = pytest.mark.django_db


class TestJWTTokens:
    """Tests for JWT token functionality."""

    @pytest.fixture
    def protected_url(self):
        """A protected endpoint that requires authentication."""
        return "/api/v1/diagrams/"

    @pytest.fixture
    def refresh_url(self):
        return "/api/v1/auth/token/refresh/"

    @pytest.fixture
    def logout_url(self):
        return "/api/v1/auth/logout/"

    def test_access_token_allows_authenticated_requests(
        self, api_client, protected_url, user, jwt_tokens
    ):
        """Test that valid access token allows access to protected endpoints."""
        # Arrange
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_tokens['access']}")

        # Act
        response = api_client.get(protected_url)

        # Assert
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_expired_access_token_returns_401(
        self, api_client, protected_url, user, settings
    ):
        """Test that expired access token returns 401."""
        # Arrange
        with freeze_time("2026-01-01 12:00:00"):
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

        # Travel to future (past token expiry)
        with freeze_time("2026-01-02 12:00:00"):
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

            # Act
            response = api_client.get(protected_url)

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_generates_new_access_token(
        self, api_client, refresh_url, jwt_tokens
    ):
        """Test that refresh token can generate new access token."""
        # Arrange
        refresh_data = {"refresh": jwt_tokens["refresh"]}

        # Act
        response = api_client.post(refresh_url, refresh_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert response.data["access"] != jwt_tokens["access"]

    def test_invalid_refresh_token_returns_401(self, api_client, refresh_url):
        """Test that invalid refresh token returns 401."""
        # Arrange
        refresh_data = {"refresh": "invalid-token"}

        # Act
        response = api_client.post(refresh_url, refresh_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_blacklists_refresh_token(
        self, authenticated_client, logout_url, refresh_url, jwt_tokens
    ):
        """Test that logout blacklists the refresh token."""
        # Arrange
        logout_data = {"refresh": jwt_tokens["refresh"]}

        # Act - logout (needs authentication)
        response = authenticated_client.post(logout_url, logout_data)

        # Assert - logout successful
        assert response.status_code == status.HTTP_200_OK

        # Act - try to use the refresh token (no auth needed for refresh endpoint)
        from rest_framework.test import APIClient

        api_client = APIClient()
        refresh_response = api_client.post(refresh_url, logout_data)

        # Assert - refresh token is blacklisted
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_request_without_token_returns_401(self, api_client, protected_url):
        """Test that request without token returns 401."""
        # Act
        response = api_client.get(protected_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_request_with_malformed_token_returns_401(self, api_client, protected_url):
        """Test that request with malformed token returns 401."""
        # Arrange
        api_client.credentials(HTTP_AUTHORIZATION="Bearer malformed-token")

        # Act
        response = api_client.get(protected_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
