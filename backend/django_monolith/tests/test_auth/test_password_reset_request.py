"""Unit tests for password reset request endpoint."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from user_auth.models import PasswordResetToken

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestPasswordResetRequestView:
    """Tests for PasswordResetRequestView."""

    @pytest.fixture
    def reset_request_url(self):
        return "/api/v1/auth/password-reset-request/"

    def test_password_reset_for_verified_user(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset request for verified user sends reset email."""
        # Arrange
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(reset_request_url, {"email": user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "password reset email has been sent" in response.data["detail"].lower()
        mock_send_mail.assert_called_once()

        # Verify reset token was created
        assert PasswordResetToken.objects.filter(user=user).exists()

    def test_password_reset_for_unverified_user_sends_verification(
        self, api_client, unverified_user, reset_request_url, mocker
    ):
        """Test password reset for unverified user sends verification email instead."""
        # Arrange
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(reset_request_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "not verified" in response.data["detail"].lower()
        assert response.data["action_required"] == "verify_email"
        mock_send_mail.assert_called_once()

        # Verify no password reset token was created
        assert not PasswordResetToken.objects.filter(user=unverified_user).exists()

    def test_password_reset_nonexistent_email(self, api_client, reset_request_url):
        """Test password reset with non-existent email returns generic success."""
        # Act
        response = api_client.post(
            reset_request_url, {"email": "nonexistent@example.com"}
        )

        # Assert - Generic success to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK
        assert "password reset email has been sent" in response.data["detail"].lower()

    def test_password_reset_missing_email(self, api_client, reset_request_url):
        """Test password reset without email returns 400."""
        # Act
        response = api_client.post(reset_request_url, {})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email is required" in response.data["detail"]

    def test_password_reset_enforces_cooldown(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset enforces 10-minute cooldown."""
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act 1: First request
        response1 = api_client.post(reset_request_url, {"email": user.email})
        assert response1.status_code == status.HTTP_200_OK

        # Act 2: Immediate second request (within cooldown)
        response2 = api_client.post(reset_request_url, {"email": user.email})

        # Assert
        assert response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "wait" in response2.data["detail"].lower()
        assert "minute" in response2.data["detail"].lower()

    def test_password_reset_allows_after_cooldown(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset is allowed after cooldown expires."""
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # First request
        api_client.post(reset_request_url, {"email": user.email})

        # Advance time past cooldown
        reset_token = PasswordResetToken.objects.get(user=user)
        reset_token.last_requested_at = timezone.now() - timedelta(minutes=11)
        reset_token.save()

        # Act - Second request after cooldown
        response = api_client.post(reset_request_url, {"email": user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_blocks_after_max_attempts(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset blocks after 5 attempts."""
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Create token with max requests
        PasswordResetToken.objects.create(user=user, request_count=5)

        # Advance time past cooldown
        reset_token = PasswordResetToken.objects.get(user=user)
        reset_token.last_requested_at = timezone.now() - timedelta(minutes=11)
        reset_token.save()

        # Act
        response = api_client.post(reset_request_url, {"email": user.email})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Maximum" in response.data["detail"]
        assert "5" in response.data["detail"]

    def test_password_reset_increments_count(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset increments request count."""
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # First request
        api_client.post(reset_request_url, {"email": user.email})
        reset_token = PasswordResetToken.objects.get(user=user)
        assert reset_token.request_count == 0

        # Advance time past cooldown
        reset_token.last_requested_at = timezone.now() - timedelta(minutes=11)
        reset_token.save()

        # Act - Second request
        api_client.post(reset_request_url, {"email": user.email})

        # Assert
        reset_token.refresh_from_db()
        assert reset_token.request_count == 1

    def test_password_reset_handles_email_failure(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset handles email send failure."""
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=0,  # Email send failed
        )

        # Act
        response = api_client.post(reset_request_url, {"email": user.email})

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to send" in response.data["detail"]

    def test_password_reset_creates_token_record(
        self, api_client, user, reset_request_url, mocker
    ):
        """Test password reset creates PasswordResetToken record."""
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(reset_request_url, {"email": user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert PasswordResetToken.objects.filter(user=user).exists()

        token = PasswordResetToken.objects.get(user=user)
        assert token.request_count == 0
        assert token.is_used is False
