from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from user_auth.utils import CsrfExemptMixin, get_tokens_for_user, get_user_data

User = get_user_model()


class RegisterView(CsrfExemptMixin, APIView):
    """User registration endpoint"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        password1 = request.data.get("password1")
        password2 = request.data.get("password2")
        first_name = request.data.get("first_name", "")

        errors = {}

        if not email:
            errors["email"] = ["Email is required."]
        elif User.objects.filter(email=email).exists():
            # Check if existing user is verified or unverified
            existing_user = User.objects.get(email=email)
            if existing_user.is_active:
                errors["email"] = ["A user with this email already exists."]
            else:
                errors["email"] = [
                    "An unverified account with this email exists. "
                    "Please check your email for the verification link or request a new one."
                ]

        if not password1:
            errors["password1"] = ["Password is required."]
        elif len(password1) < 8:
            errors["password1"] = ["Password must be at least 8 characters."]

        if password1 != password2:
            errors["password2"] = ["Passwords do not match."]

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Create user with is_active=False if verification is mandatory
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            is_active=(settings.ACCOUNT_EMAIL_VERIFICATION != "mandatory"),
        )

        # Send verification email (in production)
        if settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory":
            sent = self._send_verification_email(user)
            if not sent:
                # Delete user if email fails
                user.delete()
                return Response(
                    {
                        "detail": "Verification email could not be sent. Please try again."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Create verification token record
            from user_auth.models import EmailVerificationToken

            EmailVerificationToken.objects.create(user=user, resend_count=0)

            return Response(
                {"detail": "Verification email sent. Please check your inbox."},
                status=status.HTTP_201_CREATED,
            )

        # If no verification required, return tokens
        tokens = get_tokens_for_user(user)
        return Response(
            {
                **tokens,
                "user": get_user_data(user),
            },
            status=status.HTTP_201_CREATED,
        )

    def _send_verification_email(self, user) -> int:
        """Send verification email with expiry information."""
        # Get token expiry from settings (default 1 day)
        token_expiry_days = getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY_DAYS", 1)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email/{uid}/{token}"

        subject = "Verify your Diagramik account"
        message = f"""
Hello {user.first_name or "there"},

Thank you for registering with Diagramik!

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
