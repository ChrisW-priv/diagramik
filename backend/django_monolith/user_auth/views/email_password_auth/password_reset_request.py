from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from user_auth.models import PasswordResetToken
from user_auth.utils import CsrfExemptMixin

User = get_user_model()


class PasswordResetRequestView(CsrfExemptMixin, APIView):
    """
    Request password reset.

    SMART ROUTING:
    - Unverified users receive verification email instead
    - Verified users receive password reset link
    - Old password continues working until new one is set
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists - return generic success
            return Response(
                {
                    "detail": "If this email is registered, a password reset email has been sent."
                },
                status=status.HTTP_200_OK,
            )

        # SMART ROUTING: Check if user is verified
        if not user.is_active:
            # Unverified user - send verification email instead
            sent = self._send_verification_email(user)
            if sent:
                return Response(
                    {
                        "detail": "Your email is not verified. A verification email has been sent.",
                        "action_required": "verify_email",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "Failed to send email. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Get or create password reset token record
        reset_token, created = PasswordResetToken.objects.get_or_create(
            user=user, is_used=False, defaults={"request_count": 0}
        )

        # Check if can request reset (rate limiting)
        if not created:
            can_request, error_message = reset_token.can_request_reset()
            if not can_request:
                return Response(
                    {"detail": error_message},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Increment request count
            reset_token.request_count += 1
            reset_token.last_requested_at = timezone.now()
            reset_token.save()

        # Send password reset email
        sent = self._send_password_reset_email(user)
        if not sent:
            return Response(
                {
                    "detail": "Failed to send password reset email. Please try again later."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "detail": "If this email is registered, a password reset email has been sent.",
            },
            status=status.HTTP_200_OK,
        )

    def _send_verification_email(self, user) -> int:
        """Send verification email for unverified users."""
        from user_auth.models import EmailVerificationToken

        # Get or create verification token
        verification_token, _ = EmailVerificationToken.objects.get_or_create(
            user=user, defaults={"resend_count": 0}
        )

        token_expiry_days = getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY_DAYS", 1)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email/{uid}/{token}"

        subject = "Verify your Diagramik account"
        message = f"""
Hello {user.first_name or "there"},

You requested a password reset, but your email is not verified yet.

Please verify your email address first by clicking the link below:

{verification_url}

This link will expire in {token_expiry_days} day{"s" if token_expiry_days > 1 else ""}.

After verification, you can reset your password.

Best regards,
The Diagramik Team
        """.strip()

        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

    def _send_password_reset_email(self, user) -> int:
        """Send password reset email for verified users."""
        token_expiry_days = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY_DAYS", 1)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = (
            f"{settings.FRONTEND_URL}/auth/set-new-password?uid={uid}&token={token}"
        )

        subject = "Reset your Diagramik password"
        message = f"""
Hello {user.first_name or "there"},

You requested a password reset. Click the link below to set a new password:

{reset_url}

This link will expire in {token_expiry_days} day{"s" if token_expiry_days > 1 else ""}.

Your current password will continue to work until you set a new one.

If you didn't request this reset, you can safely ignore this email.

Best regards,
The Diagramik Team
        """.strip()

        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
