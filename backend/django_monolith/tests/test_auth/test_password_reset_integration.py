"""Integration tests for password reset system."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from user_auth.models import PasswordResetToken

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestPasswordResetIntegration:
    """Integration tests for password reset flow."""

    @pytest.fixture
    def reset_request_url(self):
        return "/api/v1/auth/password-reset-request/"

    @pytest.fixture
    def set_password_url(self):
        return "/api/v1/auth/set-new-password/"

    @pytest.fixture
    def login_url(self):
        return "/api/v1/auth/login/"

    def test_full_password_reset_flow_verified_user(
        self,
        api_client,
        user,
        reset_request_url,
        set_password_url,
        login_url,
        mocker,
    ):
        """
        Test complete password reset flow for verified user.

        Flow:
        1. Request password reset
        2. Receive reset token
        3. Set new password
        4. Old password stops working
        5. Login with new password
        """
        # Arrange
        old_password = "oldpassword123"
        user.set_password(old_password)
        user.save()

        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act 1: Request password reset
        reset_response = api_client.post(reset_request_url, {"email": user.email})

        # Assert 1: Reset request successful
        assert reset_response.status_code == status.HTTP_200_OK
        assert PasswordResetToken.objects.filter(user=user).exists()

        # Act 2: Set new password
        new_password = "newpassword456"
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        set_password_response = api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": new_password},
        )

        # Assert 2: Password set successfully
        assert set_password_response.status_code == status.HTTP_200_OK
        assert "access" in set_password_response.data

        # Assert 3: Old password no longer works
        old_login_response = api_client.post(
            login_url, {"email": user.email, "password": old_password}
        )
        assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED

        # Act 3: Login with new password
        new_login_response = api_client.post(
            login_url, {"email": user.email, "password": new_password}
        )

        # Assert 4: Login successful with new password
        assert new_login_response.status_code == status.HTTP_200_OK
        assert "access" in new_login_response.data

    def test_unverified_user_gets_verification_email(
        self,
        api_client,
        unverified_user,
        reset_request_url,
        mocker,
    ):
        """
        Test that unverified user receives verification email instead of reset.

        Flow:
        1. Unverified user requests password reset
        2. System sends verification email instead
        3. No password reset token created
        """
        # Arrange
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act
        response = api_client.post(reset_request_url, {"email": unverified_user.email})

        # Assert 1: Response indicates verification needed
        assert response.status_code == status.HTTP_200_OK
        assert "not verified" in response.data["detail"].lower()
        assert response.data["action_required"] == "verify_email"

        # Assert 2: Email was sent
        mock_send_mail.assert_called_once()

        # Assert 3: No password reset token created
        assert not PasswordResetToken.objects.filter(user=unverified_user).exists()

    def test_password_reset_rate_limiting(
        self,
        api_client,
        user,
        reset_request_url,
        mocker,
    ):
        """
        Test password reset rate limiting.

        Tests:
        1. Cannot request reset within cooldown
        2. Can request after cooldown expires
        3. Cannot exceed max attempts
        """
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

        # Assert 1: Second request blocked by cooldown
        assert response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "wait" in response2.data["detail"].lower()

        # Act 3: Advance time past cooldown
        reset_token = PasswordResetToken.objects.get(user=user)
        reset_token.last_requested_at = timezone.now() - timedelta(minutes=11)
        reset_token.save()

        # Act 4: Request after cooldown
        response3 = api_client.post(reset_request_url, {"email": user.email})

        # Assert 2: Request allowed after cooldown
        assert response3.status_code == status.HTTP_200_OK

        # Act 5: Make 4 more requests (total 5)
        for i in range(4):
            reset_token.refresh_from_db()
            reset_token.last_requested_at = timezone.now() - timedelta(minutes=11)
            reset_token.save()

            response = api_client.post(reset_request_url, {"email": user.email})
            assert response.status_code == status.HTTP_200_OK

        # Act 6: Attempt 6th request (exceeds max)
        reset_token.refresh_from_db()
        reset_token.last_requested_at = timezone.now() - timedelta(minutes=11)
        reset_token.save()

        response_max = api_client.post(reset_request_url, {"email": user.email})

        # Assert 3: Blocked - max attempts reached
        assert response_max.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Maximum" in response_max.data["detail"]

    def test_old_password_continues_working_until_reset(
        self,
        api_client,
        user,
        reset_request_url,
        set_password_url,
        login_url,
        mocker,
    ):
        """
        Test that old password continues working until new password is set.

        Flow:
        1. User has old password
        2. Request password reset
        3. Old password still works
        4. Set new password
        5. Old password stops working
        """
        # Arrange
        old_password = "oldpassword123"
        user.set_password(old_password)
        user.save()

        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act 1: Request password reset
        api_client.post(reset_request_url, {"email": user.email})

        # Assert 1: Old password still works
        login_response = api_client.post(
            login_url, {"email": user.email, "password": old_password}
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Act 2: Set new password
        new_password = "newpassword456"
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": new_password},
        )

        # Assert 2: Old password no longer works
        old_login_response = api_client.post(
            login_url, {"email": user.email, "password": old_password}
        )
        assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED

        # Assert 3: New password works
        new_login_response = api_client.post(
            login_url, {"email": user.email, "password": new_password}
        )
        assert new_login_response.status_code == status.HTTP_200_OK

    def test_password_reset_token_marked_as_used(
        self,
        api_client,
        user,
        reset_request_url,
        set_password_url,
        mocker,
    ):
        """
        Test that password reset token is marked as used after reset.

        Flow:
        1. Request password reset
        2. Reset token created
        3. Set new password
        4. Token marked as used
        """
        # Arrange
        mocker.patch(
            "user_auth.views.email_password_auth.password_reset_request.send_mail",
            return_value=1,
        )

        # Act 1: Request password reset
        api_client.post(reset_request_url, {"email": user.email})

        reset_token = PasswordResetToken.objects.get(user=user)
        assert reset_token.is_used is False

        # Act 2: Set new password
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        api_client.post(
            set_password_url,
            {"uid": uid, "token": token, "new_password": "newpassword123"},
        )

        # Assert: Token marked as used
        reset_token.refresh_from_db()
        assert reset_token.is_used is True
        assert reset_token.used_at is not None

    def test_dual_authentication_old_password_method(
        self,
        api_client,
        user,
        set_password_url,
        login_url,
    ):
        """
        Test setting password via old password (authenticated change).

        Flow:
        1. User wants to change password
        2. Provides email + old password + new password
        3. Password changed successfully
        4. Can login with new password
        """
        # Arrange
        old_password = "oldpassword123"
        user.set_password(old_password)
        user.save()

        new_password = "newpassword456"

        # Act: Set new password via old password
        response = api_client.post(
            set_password_url,
            {
                "email": user.email,
                "old_password": old_password,
                "new_password": new_password,
            },
        )

        # Assert 1: Password changed successfully
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

        # Assert 2: Can login with new password
        login_response = api_client.post(
            login_url, {"email": user.email, "password": new_password}
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Assert 3: Cannot login with old password
        old_login_response = api_client.post(
            login_url, {"email": user.email, "password": old_password}
        )
        assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_reset_email_enumeration_prevention(
        self,
        api_client,
        reset_request_url,
    ):
        """
        Test that password reset doesn't reveal if email exists.

        Both existing and non-existing emails return same response.
        """
        # Act 1: Request for non-existent email
        response1 = api_client.post(
            reset_request_url, {"email": "nonexistent@example.com"}
        )

        # Act 2: Request for existing user
        from tests.factories import UserFactory

        user = UserFactory()
        response2 = api_client.post(reset_request_url, {"email": user.email})

        # Assert: Both return same generic message
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data["detail"] == response2.data["detail"]
        assert "password reset email has been sent" in response1.data["detail"].lower()

    def test_expired_reset_token_rejected(
        self,
        api_client,
        user,
        set_password_url,
        mocker,
    ):
        """
        Test that expired reset token is rejected.

        Flow:
        1. Generate reset token
        2. Token expires
        3. Attempt to use expired token
        4. Rejected with appropriate error
        """
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
            {"uid": uid, "token": token, "new_password": "newpassword123"},
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.data["detail"].lower()
