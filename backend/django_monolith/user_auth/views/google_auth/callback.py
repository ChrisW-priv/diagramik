from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import requests

from user_auth.models import SocialAccount
from user_auth.utils import get_tokens_for_user, get_user_data

User = get_user_model()


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
