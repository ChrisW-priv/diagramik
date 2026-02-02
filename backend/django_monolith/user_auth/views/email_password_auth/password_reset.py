from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

User = get_user_model()


class PasswordResetView(APIView):
    """Request password reset email"""

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"email": ["Email is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            sent = self._send_reset_email(user)
            if not sent:
                return Response(
                    {
                        "detail": "Password reset email was not sent due to some unforeseen error"
                    },
                    status=500,
                )
        except User.DoesNotExist:
            pass

        # Always return success to prevent email enumeration
        return Response({"detail": "Password reset email sent if account exists."})

    def _send_reset_email(self, user) -> int:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = (
            f"{settings.FRONTEND_URL}/auth/password-reset?uid={uid}&token={token}"
        )

        subject = "Reset your Diagramik password"
        message = f"Click the link to reset your password: {reset_url}"

        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token"""

    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password1 = request.data.get("new_password1")
        new_password2 = request.data.get("new_password2")

        errors = {}

        if not uid:
            errors["uid"] = ["User ID is required."]
        if not token:
            errors["token"] = ["Token is required."]
        if not new_password1:
            errors["new_password1"] = ["New password is required."]
        elif len(new_password1) < 8:
            errors["new_password1"] = ["Password must be at least 8 characters."]
        if new_password1 != new_password2:
            errors["new_password2"] = ["Passwords do not match."]

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"uid": ["Invalid user."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"token": ["Invalid or expired token."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password1)
        user.save()

        return Response({"detail": "Password reset successful."})
