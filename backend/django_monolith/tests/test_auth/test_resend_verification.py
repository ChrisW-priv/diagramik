"""Unit tests for resend verification email endpoint."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from user_auth.models import EmailVerificationToken

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestResendVerificationEmailView:
    """Tests for ResendVerificationEmailView (simplified - email only)."""

    @pytest.fixture
    def resend_url(self):
        return "/api/v1/auth/resend-verification/"

    def test_resend_with_valid_email(
        self, api_client, unverified_user, resend_url, mocker
    ):
        """Test resending verification email with valid email."""
        # Arrange - Advance time past cooldown
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        # Mock send_mail at the correct path
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.resend_verification.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "Verification email sent" in response.data["detail"]
        assert response.data["resend_count"] == 1
        assert response.data["max_resends"] == 5
        mock_send_mail.assert_called_once()

    def test_resend_increments_count(
        self, api_client, unverified_user, resend_url, mock_send_mail
    ):
        """Test that resend count is incremented."""
        # Arrange
        initial_count = unverified_user.verification_token.resend_count
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Refresh token from database
        unverified_user.verification_token.refresh_from_db()
        assert unverified_user.verification_token.resend_count == initial_count + 1

    def test_resend_updates_timestamp(
        self, api_client, unverified_user, resend_url, mock_send_mail
    ):
        """Test that last_sent_at is updated after resend."""
        # Arrange
        old_timestamp = timezone.now() - timedelta(minutes=11)
        unverified_user.verification_token.last_sent_at = old_timestamp
        unverified_user.verification_token.save()

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Timestamp should be updated
        unverified_user.verification_token.refresh_from_db()
        assert unverified_user.verification_token.last_sent_at > old_timestamp

    def test_resend_missing_email(self, api_client, resend_url):
        """Test resend without email returns 400."""
        # Act
        response = api_client.post(resend_url, {})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email is required" in response.data["detail"]

    def test_resend_nonexistent_email(self, api_client, resend_url):
        """Test resend with non-existent email returns generic success (no enumeration)."""
        # Act
        response = api_client.post(resend_url, {"email": "nonexistent@example.com"})

        # Assert - Returns success to prevent email enumeration
        assert response.status_code == status.HTTP_200_OK
        assert "If this email is registered" in response.data["detail"]

    def test_resend_already_verified_user(self, api_client, verified_user, resend_url):
        """Test resend for already verified user returns 400."""
        # Act
        response = api_client.post(resend_url, {"email": verified_user.email})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already verified" in response.data["detail"].lower()

    def test_resend_enforces_cooldown(self, api_client, unverified_user, resend_url):
        """Test that resend enforces 10-minute cooldown period."""
        # Arrange - Token was just sent (within cooldown)
        unverified_user.verification_token.last_sent_at = timezone.now()
        unverified_user.verification_token.save()

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "wait" in response.data["detail"].lower()
        assert "minute" in response.data["detail"].lower()

    def test_resend_allows_after_cooldown(
        self, api_client, unverified_user, resend_url, mocker
    ):
        """Test that resend is allowed after cooldown period expires."""
        # Arrange - Set last_sent_at to 11 minutes ago (past 10-minute cooldown)
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        # Mock send_mail at the correct path
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.resend_verification.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        mock_send_mail.assert_called_once()

    def test_resend_blocks_after_max_attempts(
        self, api_client, user_with_max_resends, resend_url
    ):
        """Test that resend is blocked after 5 attempts."""
        # Arrange - User already has 5 resends
        user_with_max_resends.verification_token.last_sent_at = (
            timezone.now() - timedelta(minutes=11)
        )
        user_with_max_resends.verification_token.save()

        # Act
        response = api_client.post(resend_url, {"email": user_with_max_resends.email})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Maximum resend attempts" in response.data["detail"]
        assert "5" in response.data["detail"]

    def test_resend_returns_remaining_cooldown_time(
        self, api_client, unverified_user, resend_url
    ):
        """Test that rate limit error includes remaining cooldown time."""
        # Arrange - Token sent 5 minutes ago (5 minutes remaining)
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=5
        )
        unverified_user.verification_token.save()

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "minute" in response.data["detail"].lower()
        # Should mention remaining time
        assert any(str(i) in response.data["detail"] for i in range(1, 10))

    def test_resend_creates_token_if_missing(self, api_client, resend_url, mocker):
        """Test resend creates EmailVerificationToken if it doesn't exist."""
        # Arrange - Create unverified user WITHOUT verification token
        from tests.factories import UserFactory

        user = UserFactory(is_active=False)
        # No EmailVerificationToken created

        # Mock send_mail at the correct path
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.resend_verification.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(resend_url, {"email": user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert EmailVerificationToken.objects.filter(user=user).exists()
        mock_send_mail.assert_called_once()

    def test_resend_handles_email_send_failure(
        self, api_client, unverified_user, resend_url, mocker
    ):
        """Test resend handles email send failure gracefully."""
        # Arrange
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        # Mock email send to fail
        mocker.patch(
            "user_auth.views.email_password_auth.resend_verification.send_mail",
            return_value=0,  # Email send failed
        )

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to send" in response.data["detail"]

    def test_resend_returns_max_resends_config(
        self, api_client, unverified_user, resend_url, mock_send_mail, settings
    ):
        """Test that response includes max_resends from settings."""
        # Arrange
        settings.EMAIL_VERIFICATION_MAX_RESENDS = 3  # Custom value
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        # Act
        response = api_client.post(resend_url, {"email": unverified_user.email})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["max_resends"] == 3

    def test_resend_multiple_times_sequential(
        self, api_client, unverified_user, resend_url, mock_send_mail
    ):
        """Test multiple sequential resends with cooldown respected."""
        # Act & Assert - Resend 1
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        response1 = api_client.post(resend_url, {"email": unverified_user.email})
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["resend_count"] == 1

        # Act & Assert - Resend 2 (after cooldown)
        unverified_user.verification_token.refresh_from_db()
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        response2 = api_client.post(resend_url, {"email": unverified_user.email})
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["resend_count"] == 2

        # Act & Assert - Resend 3 (after cooldown)
        unverified_user.verification_token.refresh_from_db()
        unverified_user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=11
        )
        unverified_user.verification_token.save()

        response3 = api_client.post(resend_url, {"email": unverified_user.email})
        assert response3.status_code == status.HTTP_200_OK
        assert response3.data["resend_count"] == 3
