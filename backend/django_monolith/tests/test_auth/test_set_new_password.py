"""Unit tests for set new password endpoint."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

from user_auth.models import PasswordResetToken

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestSetNewPasswordView:
    """Tests for SetNewPasswordView."""

    @pytest.fixture
    def set_password_url(self):
        return "/api/v1/auth/set-new-password/"

    def test_set_password_via_email_token(self, api_client, user, set_password_url):
        """Test setting password via email reset token."""
        # Arrange
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        new_password = "newpassword123"

        # Act
        response = api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": new_password},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password(new_password)

    def test_set_password_via_old_password(self, api_client, set_password_url):
        """Test setting password via old password authentication."""
        # Arrange
        from tests.factories import UserFactory

        old_password = "oldpassword123"
        user = UserFactory()
        user.set_password(old_password)
        user.save()

        new_password = "newpassword456"

        # Act
        response = api_client.post(
            set_password_url,
            {
                "email": user.email,
                "old_password": old_password,
                "new_password": new_password,
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password(new_password)
        assert not user.check_password(old_password)

    def test_set_password_missing_new_password(
        self, api_client, user, set_password_url
    ):
        """Test set password without new_password returns 400."""
        # Arrange
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = api_client.post(set_password_url, {"uid": uid, "token": token})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "New password is required" in response.data["detail"]

    def test_set_password_missing_auth_params(self, api_client, set_password_url):
        """Test set password without auth params returns 400."""
        # Act
        response = api_client.post(set_password_url, {"new_password": "newpass123"})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "required" in response.data["detail"].lower()

    def test_set_password_invalid_uid(self, api_client, set_password_url):
        """Test set password with invalid uid returns 400."""
        # Act
        response = api_client.post(
            set_password_url,
            {"uid": "invalid-uid", "token": "sometoken", "new_password": "newpass123"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid password reset link" in response.data["detail"]

    def test_set_password_invalid_token(self, api_client, user, set_password_url):
        """Test set password with invalid token returns 400."""
        # Arrange
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = api_client.post(
            set_password_url,
            {"uid": uid, "token": "invalid-token", "new_password": "newpass123"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired" in response.data["detail"]

    def test_set_password_expired_token(
        self, api_client, user, set_password_url, mocker
    ):
        """Test set password with expired token returns 400."""
        # Arrange
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Mock token check to return False (expired)
        mocker.patch(
            "user_auth.views.email_password_auth.set_new_password.default_token_generator.check_token",
            return_value=False,
        )

        # Act
        response = api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": "newpass123"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.data["detail"].lower()

    def test_set_password_wrong_old_password(self, api_client, user, set_password_url):
        """Test set password with wrong old password returns 401."""
        # Act
        response = api_client.post(
            set_password_url,
            {
                "email": user.email,
                "old_password": "wrongpassword",
                "new_password": "newpass123",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.data["detail"]

    def test_set_password_weak_password(self, api_client, user, set_password_url):
        """Test set password with weak password returns 400."""
        # Arrange
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act - Use very weak password
        response = api_client.post(
            set_password_url, {"uid": uid, "token": token, "new_password": "123"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Django password validators will reject this

    def test_set_password_marks_token_as_used(self, api_client, user, set_password_url):
        """Test set password marks PasswordResetToken as used."""
        # Arrange
        PasswordResetToken.objects.create(user=user, request_count=1, is_used=False)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": "newpassword123"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        reset_token = PasswordResetToken.objects.get(user=user)
        assert reset_token.is_used is True
        assert reset_token.used_at is not None

    def test_set_password_returns_jwt_tokens(self, api_client, user, set_password_url):
        """Test set password returns JWT tokens for immediate login."""
        # Arrange
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Act
        response = api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": "newpassword123"},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert isinstance(response.data["access"], str)
        assert len(response.data["access"]) > 20

    def test_set_password_old_password_continues_working_until_changed(
        self, api_client, user, set_password_url
    ):
        """Test old password continues working until new password is set."""
        # Arrange
        old_password = "oldpassword123"
        user.set_password(old_password)
        user.save()

        # Verify old password works
        assert user.check_password(old_password)

        # Get reset token but don't use it yet
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Old password should still work
        user.refresh_from_db()
        assert user.check_password(old_password)

        # Act - Now set new password
        new_password = "newpassword456"
        response = api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": new_password},
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password(new_password)
        assert not user.check_password(old_password)
