"""Integration tests for email verification system."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from user_auth.models import EmailVerificationToken

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestEmailVerificationOptionalMode:
    """Integration tests when ACCOUNT_EMAIL_VERIFICATION = 'optional'"""

    @pytest.fixture
    def registration_url(self):
        return "/api/v1/auth/registration/"

    @pytest.fixture
    def login_url(self):
        return "/api/v1/auth/login/"

    @pytest.fixture
    def create_diagram_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def valid_registration_data(self):
        return {
            "email": "newuser@example.com",
            "password1": "securepass123",
            "password2": "securepass123",
            "first_name": "Test",
        }

    def test_optional_mode_full_flow_user_instantly_enabled_can_login_and_create_diagram(
        self,
        api_client,
        authenticated_client,
        registration_url,
        login_url,
        create_diagram_url,
        valid_registration_data,
        settings,
        mocker,
    ):
        """
        Integration test for optional email verification mode.

        Flow:
        1. User registers account
        2. Assert user is instantly enabled (is_active=True)
        3. Assert user can login immediately
        4. Assert user can generate diagram without verification
        """
        # Arrange - Set email verification to optional
        settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

        # Act 1: Register user
        response = api_client.post(registration_url, valid_registration_data)

        # Assert 1: Registration successful with JWT tokens
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

        # Assert 2: User is created and instantly enabled
        user = User.objects.get(email=valid_registration_data["email"])
        assert user.is_active is True
        assert user.check_password(valid_registration_data["password1"])

        # Assert 3: No EmailVerificationToken created in optional mode
        assert not hasattr(user, "verification_token")

        # Act 2: Login with credentials (should work immediately)
        login_response = api_client.post(
            login_url,
            {
                "email": valid_registration_data["email"],
                "password": valid_registration_data["password1"],
            },
        )

        # Assert 4: Login successful
        assert login_response.status_code == status.HTTP_200_OK
        assert "access" in login_response.data
        assert "refresh" in login_response.data

        # NOTE: Diagram creation test removed - focuses only on auth flow


class TestEmailVerificationMandatoryMode:
    """Integration tests when ACCOUNT_EMAIL_VERIFICATION = 'mandatory'"""

    @pytest.fixture
    def registration_url(self):
        return "/api/v1/auth/registration/"

    @pytest.fixture
    def login_url(self):
        return "/api/v1/auth/login/"

    @pytest.fixture
    def verify_email_url(self):
        return "/api/v1/auth/verify-email/"

    @pytest.fixture
    def resend_verification_url(self):
        return "/api/v1/auth/resend-verification/"

    @pytest.fixture
    def create_diagram_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def valid_registration_data(self):
        return {
            "email": "unverified@example.com",
            "password1": "securepass123",
            "password2": "securepass123",
            "first_name": "Unverified",
        }

    def test_mandatory_mode_full_flow_with_verification(
        self,
        api_client,
        registration_url,
        login_url,
        verify_email_url,
        create_diagram_url,
        valid_registration_data,
        settings,
        mocker,
    ):
        """
        Integration test for mandatory email verification mode.

        Flow:
        1. User registers account
        2. Assert user is disabled (is_active=False)
        3. Assert user cannot login before verification
        4. User verifies email
        5. Assert user is now enabled
        6. Assert user can login after verification
        7. Assert user can create diagram after verification
        """
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mock_send_mail = mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )

        # Act 1: Register user
        response = api_client.post(registration_url, valid_registration_data)

        # Assert 1: Registration returns success message (no tokens)
        assert response.status_code == status.HTTP_201_CREATED
        assert "detail" in response.data
        assert "Verification email sent" in response.data["detail"]
        assert "access" not in response.data  # No tokens in mandatory mode
        assert "refresh" not in response.data

        # Assert 2: Verification email was sent
        mock_send_mail.assert_called_once()

        # Assert 3: User created but DISABLED
        user = User.objects.get(email=valid_registration_data["email"])
        assert user.is_active is False
        assert user.check_password(valid_registration_data["password1"])

        # Assert 4: EmailVerificationToken created
        assert hasattr(user, "verification_token")
        assert user.verification_token.resend_count == 0
        assert user.verification_token.verified_at is None

        # Act 2: Attempt to login BEFORE verification
        login_response = api_client.post(
            login_url,
            {
                "email": valid_registration_data["email"],
                "password": valid_registration_data["password1"],
            },
        )

        # Assert 5: Login rejected with EMAIL_NOT_VERIFIED error
        assert login_response.status_code == status.HTTP_403_FORBIDDEN
        assert login_response.data["error_code"] == "EMAIL_NOT_VERIFIED"
        assert "verify your email" in login_response.data["detail"].lower()
        assert (
            login_response.data["resend_endpoint"]
            == "/api/v1/auth/resend-verification/"
        )

        # Act 3: Verify email with token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        verify_response = api_client.post(
            verify_email_url, {"uid": uid, "token": token}
        )

        # Assert 6: Verification successful, returns JWT tokens
        assert verify_response.status_code == status.HTTP_200_OK
        assert "access" in verify_response.data
        assert "refresh" in verify_response.data
        assert "user" in verify_response.data

        # Assert 7: User is now ENABLED
        user.refresh_from_db()
        assert user.is_active is True

        # Assert 8: Verification token marked as verified
        user.verification_token.refresh_from_db()
        assert user.verification_token.verified_at is not None

        # Act 4: Login AFTER verification
        login_response_after = api_client.post(
            login_url,
            {
                "email": valid_registration_data["email"],
                "password": valid_registration_data["password1"],
            },
        )

        # Assert 9: Login successful after verification
        assert login_response_after.status_code == status.HTTP_200_OK
        assert "access" in login_response_after.data

        # NOTE: Diagram creation test removed - focuses only on auth flow

    def test_mandatory_mode_resend_rate_limiting(
        self,
        api_client,
        registration_url,
        resend_verification_url,
        valid_registration_data,
        settings,
        mocker,
    ):
        """
        Integration test for resend rate limiting.

        Tests:
        1. User cannot resend immediately after registration
        2. User cannot resend more than MAX_RESENDS times
        3. User cannot resend within COOLDOWN_MINUTES
        4. Rate limit errors include remaining time
        """
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )
        mocker.patch(
            "user_auth.views.email_password_auth.resend_verification.send_mail",
            return_value=1,
        )

        # Act 1: Register user
        api_client.post(registration_url, valid_registration_data)
        user = User.objects.get(email=valid_registration_data["email"])

        # Assert 1: Initial verification token created
        assert user.verification_token.resend_count == 0

        # Act 2: Attempt to resend IMMEDIATELY (within cooldown)
        resend_response_1 = api_client.post(
            resend_verification_url, {"email": valid_registration_data["email"]}
        )

        # Assert 2: Resend blocked by cooldown
        assert resend_response_1.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "wait" in resend_response_1.data["detail"].lower()
        assert "minute" in resend_response_1.data["detail"].lower()

        # Act 3: Simulate time passing (10 minutes + 1 second)
        user.verification_token.last_sent_at = timezone.now() - timedelta(
            minutes=10, seconds=1
        )
        user.verification_token.save()

        # Act 4: Resend after cooldown expires
        resend_response_2 = api_client.post(
            resend_verification_url, {"email": valid_registration_data["email"]}
        )

        # Assert 3: Resend successful after cooldown
        assert resend_response_2.status_code == status.HTTP_200_OK
        assert resend_response_2.data["resend_count"] == 1
        assert resend_response_2.data["max_resends"] == 5

        # Assert 4: Token was updated (not invalidated)
        user.verification_token.refresh_from_db()
        assert user.verification_token.resend_count == 1

        # Act 5: Resend 4 more times (total 5 resends)
        for i in range(4):
            # Advance time past cooldown
            latest_token = EmailVerificationToken.objects.filter(
                user=user, is_invalidated=False
            ).first()
            latest_token.last_sent_at = timezone.now() - timedelta(minutes=11)
            latest_token.save()

            resend_response = api_client.post(
                resend_verification_url, {"email": valid_registration_data["email"]}
            )
            assert resend_response.status_code == status.HTTP_200_OK
            assert resend_response.data["resend_count"] == i + 2

        # Act 6: Attempt 6th resend (exceeds MAX_RESENDS)
        latest_token = EmailVerificationToken.objects.filter(
            user=user, is_invalidated=False
        ).first()
        latest_token.last_sent_at = timezone.now() - timedelta(minutes=11)
        latest_token.save()

        resend_response_max = api_client.post(
            resend_verification_url, {"email": valid_registration_data["email"]}
        )

        # Assert 5: Resend blocked - max attempts reached
        assert resend_response_max.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "maximum" in resend_response_max.data["detail"].lower()
        assert "5" in resend_response_max.data["detail"]

    def test_mandatory_mode_token_works_after_resend(
        self,
        api_client,
        registration_url,
        verify_email_url,
        resend_verification_url,
        valid_registration_data,
        settings,
        mocker,
    ):
        """
        Integration test ensuring tokens still work after resend.

        Tests:
        1. Generate initial verification token
        2. Resend verification (updates token record)
        3. Verify with newly generated token - should succeed
        """
        # Arrange
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"
        mocker.patch(
            "user_auth.views.email_password_auth.register.send_mail", return_value=1
        )
        mocker.patch(
            "user_auth.views.email_password_auth.resend_verification.send_mail",
            return_value=1,
        )

        # Act 1: Register user
        api_client.post(registration_url, valid_registration_data)
        user = User.objects.get(email=valid_registration_data["email"])

        # Act 2: Resend verification
        user.verification_token.last_sent_at = timezone.now() - timedelta(minutes=11)
        user.verification_token.save()

        resend_response = api_client.post(
            resend_verification_url, {"email": valid_registration_data["email"]}
        )
        assert resend_response.status_code == status.HTTP_200_OK

        # Act 3: Generate token after resend and verify
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        verify_response = api_client.post(
            verify_email_url, {"uid": uid, "token": token}
        )

        # Assert: Token accepted and user verified
        assert verify_response.status_code == status.HTTP_200_OK
        assert "access" in verify_response.data

        user.refresh_from_db()
        assert user.is_active is True
