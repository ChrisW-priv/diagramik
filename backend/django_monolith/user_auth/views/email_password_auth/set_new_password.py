from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from user_auth.models import PasswordResetToken
from user_auth.utils import CsrfExemptMixin, get_tokens_for_user, get_user_data

User = get_user_model()


class SetNewPasswordView(CsrfExemptMixin, APIView):
    """
    Set new password with dual authentication.

    DUAL AUTHENTICATION:
    - Via email token (uid + token from reset link)
    - Via old password (for logged-in users changing password)
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # Get request data
        uid = request.data.get("uid")
        token = request.data.get("token")
        email = request.data.get("email")
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not new_password:
            return Response(
                {"detail": "New password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine authentication method
        if uid and token:
            # Method 1: Email token authentication
            return self._set_password_via_token(uid, token, new_password)
        elif email and old_password:
            # Method 2: Old password authentication
            return self._set_password_via_old_password(
                email, old_password, new_password
            )
        else:
            return Response(
                {
                    "detail": "Either (uid + token) or (email + old_password) is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _set_password_via_token(self, uid, token, new_password):
        """Set password using email token."""
        # Decode user ID
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid password reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check token validity
        if not default_token_generator.check_token(user, token):
            return Response(
                {
                    "detail": "Invalid or expired password reset token. Please request a new password reset."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate new password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"detail": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        # Mark reset token as used
        try:
            reset_token = PasswordResetToken.objects.filter(
                user=user, is_used=False
            ).latest("created_at")
            reset_token.mark_used()
        except PasswordResetToken.DoesNotExist:
            pass

        # Generate JWT tokens for immediate login
        tokens = get_tokens_for_user(user)

        return Response(
            {
                "detail": "Password reset successfully. You are now logged in.",
                **tokens,
                "user": get_user_data(user),
            },
            status=status.HTTP_200_OK,
        )

    def _set_password_via_old_password(self, email, old_password, new_password):
        """Set password using old password."""
        # Authenticate with old password
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(old_password):
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Validate new password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {"detail": e.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        # Generate JWT tokens for immediate login
        tokens = get_tokens_for_user(user)

        return Response(
            {
                "detail": "Password changed successfully. You are now logged in.",
                **tokens,
                "user": get_user_data(user),
            },
            status=status.HTTP_200_OK,
        )
