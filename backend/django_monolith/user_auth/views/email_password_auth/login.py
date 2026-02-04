from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from user_auth.utils import CsrfExemptMixin, get_tokens_for_user, get_user_data

User = get_user_model()


class LoginView(CsrfExemptMixin, APIView):
    """Email/password login endpoint"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try to find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check password
        if not user.check_password(password):
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            # Check if this is an unverified email vs. disabled account
            has_verification_token = hasattr(user, "verification_token")

            if has_verification_token and not user.verification_token.verified_at:
                # Unverified email
                return Response(
                    {
                        "error_code": "EMAIL_NOT_VERIFIED",
                        "detail": "Please verify your email before logging in.",
                        "action_required": "verify_email",
                        "resend_endpoint": "/api/v1/auth/resend-verification/",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            else:
                # Account disabled by admin
                return Response(
                    {
                        "error_code": "ACCOUNT_DISABLED",
                        "detail": "Your account has been disabled. Please contact support.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        tokens = get_tokens_for_user(user)
        return Response(
            {
                **tokens,
                "user": get_user_data(user),
            }
        )
