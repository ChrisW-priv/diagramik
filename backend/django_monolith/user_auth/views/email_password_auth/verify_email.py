from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from user_auth.models import EmailVerificationToken
from user_auth.utils import CsrfExemptMixin, get_tokens_for_user, get_user_data

User = get_user_model()


class VerifyEmailView(CsrfExemptMixin, APIView):
    """Verify user's email with token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        """Handle GET requests (clicking link from email)."""
        uid = request.query_params.get("uid")
        token = request.query_params.get("token")
        return self._verify(uid, token)

    def post(self, request):
        """Handle POST requests (programmatic verification)."""
        uid = request.data.get("uid")
        token = request.data.get("token")
        return self._verify(uid, token)

    def _verify(self, uid, token):
        """Common verification logic."""
        errors = {}

        if not uid:
            errors["uid"] = ["User ID is required."]
        if not token:
            errors["token"] = ["Token is required."]

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Decode user ID
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already verified
        if user.is_active:
            return Response(
                {"detail": "Email already verified. You can log in."},
                status=status.HTTP_200_OK,
            )

        # Check token validity
        if not default_token_generator.check_token(user, token):
            return Response(
                {
                    "detail": "Invalid or expired verification token. Please request a new verification email."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if token was invalidated (resend was requested)
        try:
            verification_token = EmailVerificationToken.objects.get(user=user)
            if verification_token.is_invalidated:
                return Response(
                    {
                        "detail": "This verification link has been invalidated. Please use the most recent email."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except EmailVerificationToken.DoesNotExist:
            pass

        # Verify the user
        user.is_active = True
        user.save()

        # Mark token as verified
        if hasattr(user, "verification_token"):
            user.verification_token.mark_verified()

        # Generate JWT tokens for immediate login
        tokens = get_tokens_for_user(user)

        return Response(
            {
                "detail": "Email verified successfully. You are now logged in.",
                **tokens,
                "user": get_user_data(user),
            },
            status=status.HTTP_200_OK,
        )
