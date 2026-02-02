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
            errors["email"] = ["A user with this email already exists."]

        if not password1:
            errors["password1"] = ["Password is required."]
        elif len(password1) < 8:
            errors["password1"] = ["Password must be at least 8 characters."]

        if password1 != password2:
            errors["password2"] = ["Passwords do not match."]

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
        )

        # Send verification email (in production)
        if settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory":
            sent = self._send_verification_email(user)
            if not sent:
                return Response(
                    {
                        "detail": "Password reset email was not sent due to some unforeseen error"
                    },
                    status=500,
                )
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
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email/{uid}/{token}"

        subject = "Verify your Diagramik account"
        message = f"Please click the link to verify your email: {verification_url}"

        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
