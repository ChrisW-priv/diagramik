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

from user_auth.models import EmailVerificationToken
from user_auth.utils import CsrfExemptMixin

User = get_user_model()


class ResendVerificationEmailView(CsrfExemptMixin, APIView):
    """
    Resend verification email to unverified user.

    SIMPLIFIED: Only requires email (no password).
    Backend checks if user exists and enforces rate limiting.
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
                    "detail": "If this email is registered and unverified, a verification email has been sent."
                },
                status=status.HTTP_200_OK,
            )

        # Check if already verified
        if user.is_active:
            return Response(
                {"detail": "Email is already verified. You can log in."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create verification token record
        verification_token, created = EmailVerificationToken.objects.get_or_create(
            user=user, defaults={"resend_count": 0}
        )

        # Check if can resend (rate limiting)
        if not created:
            can_resend, error_message = verification_token.can_resend()
            if not can_resend:
                return Response(
                    {"detail": error_message},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Update existing token record
            verification_token.resend_count += 1
            verification_token.last_sent_at = timezone.now()
            verification_token.is_invalidated = False  # Reset invalidated status
            verification_token.invalidated_at = None
            verification_token.save()

        # Send verification email
        sent = self._send_verification_email(user)
        if not sent:
            return Response(
                {
                    "detail": "Failed to send verification email. Please try again later."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Get max resends from settings
        max_resends = getattr(settings, "EMAIL_VERIFICATION_MAX_RESENDS", 5)

        return Response(
            {
                "detail": "Verification email sent. Please check your inbox.",
                "resend_count": verification_token.resend_count,
                "max_resends": max_resends,
            },
            status=status.HTTP_200_OK,
        )

    def _send_verification_email(self, user) -> int:
        """Send verification email."""
        # Get token expiry from settings (default 1 day)
        token_expiry_days = getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY_DAYS", 1)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = (
            f"{settings.FRONTEND_URL}/auth/verify-email?uid={uid}&token={token}"
        )

        subject = "Verify your Diagramik account"
        message = f"""
Hello {user.first_name or "there"},

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in {token_expiry_days} day{"s" if token_expiry_days > 1 else ""}.

If you didn't create this account, you can safely ignore this email.

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
