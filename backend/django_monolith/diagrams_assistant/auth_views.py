from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from allauth.socialaccount.models import SocialAccount
import requests


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class CsrfExemptMixin:
    """
    Exempts the view from CSRF requirements.

    NOTE:
        This should be the left-most mixin of a view.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for a user"""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def get_user_data(user):
    """Get user data for response"""
    return {
        "pk": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


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
            return Response(
                {"detail": "Account is disabled."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = get_tokens_for_user(user)
        return Response(
            {
                **tokens,
                "user": get_user_data(user),
            }
        )


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


class LogoutView(APIView):
    """Logout endpoint - blacklists the refresh token"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        return Response({"detail": "Successfully logged out."})


class UserView(APIView):
    """Get/update current user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_user_data(request.user))

    def patch(self, request):
        user = request.user
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        user.save()
        return Response(get_user_data(user))


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


class GoogleAuthURLView(APIView):
    """Get Google OAuth URL"""

    permission_classes = [AllowAny]

    def get(self, request):
        client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
        callback_url = f"{settings.BACKEND_URL}/api/v1/auth/social/google/"
        oauth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={callback_url}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile"
        )
        return Response({"auth_url": oauth_url})


class GoogleLoginView(APIView):
    """Handle Google OAuth callback"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        """Handle Google OAuth callback redirect"""
        code = request.query_params.get("code")
        error = request.query_params.get("error")

        if error:
            # Redirect to frontend with error
            return redirect(f"{settings.FRONTEND_URL}/?error={error}")

        if not code:
            return redirect(f"{settings.FRONTEND_URL}/?error=no_code")

        try:
            # Exchange code for tokens
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"][
                        "client_id"
                    ],
                    "client_secret": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"][
                        "secret"
                    ],
                    "redirect_uri": f"{settings.BACKEND_URL}/api/v1/auth/social/google/",
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                return redirect(f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            # Get user info from Google
            userinfo_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                return redirect(f"{settings.FRONTEND_URL}/?error=userinfo_failed")

            google_user = userinfo_response.json()
            email = google_user.get("email")
            google_id = google_user.get("id")
            first_name = google_user.get("given_name", "")
            last_name = google_user.get("family_name", "")

            if not email:
                return redirect(f"{settings.FRONTEND_URL}/?error=no_email")

            # Find or create user
            user = None

            # Check if there's a social account linked
            try:
                social_account = SocialAccount.objects.get(
                    provider="google", uid=google_id
                )
                user = social_account.user
            except SocialAccount.DoesNotExist:
                pass

            # If no social account, try to find user by email
            if not user:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    # Create new user
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                    )

                # Link social account
                SocialAccount.objects.create(
                    user=user,
                    provider="google",
                    uid=google_id,
                    extra_data=google_user,
                )

            jwt_tokens = get_tokens_for_user(user)

            # Redirect to frontend with tokens
            from urllib.parse import urlencode

            params = urlencode(
                {
                    "access": jwt_tokens["access"],
                    "refresh": jwt_tokens["refresh"],
                }
            )
            return redirect(f"{settings.FRONTEND_URL}/auth/google/callback?{params}")

        except Exception:
            return redirect(f"{settings.FRONTEND_URL}/?error=auth_failed")

    def post(self, request):
        code = request.data.get("code")

        if not code:
            return Response(
                {"detail": "Authorization code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Exchange code for tokens
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"][
                        "client_id"
                    ],
                    "client_secret": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"][
                        "secret"
                    ],
                    "redirect_uri": f"{settings.BACKEND_URL}/api/v1/auth/social/google/",
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                return Response(
                    {"detail": "Failed to exchange authorization code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            # Get user info from Google
            userinfo_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                return Response(
                    {"detail": "Failed to get user info from Google."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            google_user = userinfo_response.json()
            email = google_user.get("email")
            google_id = google_user.get("id")
            first_name = google_user.get("given_name", "")
            last_name = google_user.get("family_name", "")

            if not email:
                return Response(
                    {"detail": "Could not get email from Google."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Find or create user
            user = None

            # Check if there's a social account linked
            try:
                social_account = SocialAccount.objects.get(
                    provider="google", uid=google_id
                )
                user = social_account.user
            except SocialAccount.DoesNotExist:
                pass

            # If no social account, try to find user by email
            if not user:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    # Create new user
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                    )

                # Link social account
                SocialAccount.objects.create(
                    user=user,
                    provider="google",
                    uid=google_id,
                    extra_data=google_user,
                )

            jwt_tokens = get_tokens_for_user(user)
            return Response(
                {
                    **jwt_tokens,
                    "user": get_user_data(user),
                }
            )

        except Exception as e:
            return Response(
                {"detail": f"Google authentication failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Reuse simplejwt's token refresh view
class CustomTokenRefreshView(TokenRefreshView):
    """Token refresh endpoint"""

    pass
