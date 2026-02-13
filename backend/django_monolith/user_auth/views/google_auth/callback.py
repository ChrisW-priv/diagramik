from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import requests
import json

from user_auth.models import SocialAccount, EmailVerificationToken, UserProfile
from user_auth.utils import get_tokens_for_user, get_user_data

User = get_user_model()


def decode_oauth_context_state(state_param):
    """Decode the OAuth state parameter to get context (from_register, etc.)"""
    if not state_param:
        return {}

    signer = TimestampSigner()
    try:
        # No max_age check - state is short-lived (only during OAuth redirect)
        unsigned = signer.unsign(state_param)
        return json.loads(unsigned)
    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return {}


def create_register_redirect_token(user_data):
    """Create a signed token containing OAuth user data for register page redirect"""
    signer = TimestampSigner()
    return signer.sign(json.dumps(user_data))


def verify_register_redirect_token(token, max_age=300):
    """Verify and decode register redirect token (5 min expiry)"""
    signer = TimestampSigner()
    try:
        unsigned = signer.unsign(token, max_age=max_age)
        return json.loads(unsigned)
    except (BadSignature, SignatureExpired):
        return None


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

        # Get OAuth state parameter from Google
        oauth_state = request.GET.get("state", "")
        context = decode_oauth_context_state(oauth_state)
        from_register = context.get("from_register", False)
        terms_accepted_on_register = context.get("terms_accepted", False)

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
                    # User exists from email/password registration
                    # Google has verified this email, so activate the account
                    if not user.is_active:
                        user.is_active = True
                        user.save()

                    # Ensure verification token exists and is marked verified
                    if hasattr(user, "verification_token"):
                        if not user.verification_token.verified_at:
                            user.verification_token.mark_verified()
                    else:
                        verification_token = EmailVerificationToken.objects.create(
                            user=user
                        )
                        verification_token.mark_verified()

                    # Ensure user profile exists (terms acceptance assumed via OAuth)
                    if not hasattr(user, "profile"):
                        from django.utils import timezone

                        UserProfile.objects.create(
                            user=user,
                            terms_accepted=True,
                            terms_accepted_at=timezone.now(),
                        )

                    # Link social account for existing user found by email
                    SocialAccount.objects.get_or_create(
                        user=user,
                        provider="google",
                        uid=google_id,
                        defaults={"extra_data": google_user},
                    )

                except User.DoesNotExist:
                    # Check if user came from register page with terms already accepted
                    if from_register and terms_accepted_on_register:
                        # Create user immediately - they already accepted terms
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            is_active=True,
                        )

                        # Mark email as verified (from Google)
                        verification_token = EmailVerificationToken.objects.create(
                            user=user
                        )
                        verification_token.mark_verified()

                        # Create user profile with terms acceptance and timestamp
                        from django.utils import timezone

                        UserProfile.objects.create(
                            user=user,
                            terms_accepted=True,
                            terms_accepted_at=timezone.now(),
                        )

                        # Link social account
                        SocialAccount.objects.create(
                            user=user,
                            provider="google",
                            uid=google_id,
                            extra_data=google_user,
                        )
                    else:
                        # User came from login page - redirect to register for terms acceptance
                        state_data = {
                            "email": email,
                            "first_name": first_name,
                            "last_name": last_name,
                            "google_id": google_id,
                            "extra_data": google_user,
                        }
                        state_token = create_register_redirect_token(state_data)
                        return redirect(
                            f"{settings.FRONTEND_URL}/auth/register?"
                            f"oauth_pending=google&state={state_token}"
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
        oauth_state = request.data.get("state", "")

        if not code:
            return Response(
                {"detail": "Authorization code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decode OAuth state parameter to check context
        context = decode_oauth_context_state(oauth_state)
        from_register = context.get("from_register", False)
        terms_accepted_on_register = context.get("terms_accepted", False)

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
                    # User exists from email/password registration
                    # Google has verified this email, so activate the account
                    if not user.is_active:
                        user.is_active = True
                        user.save()

                    # Ensure verification token exists and is marked verified
                    if hasattr(user, "verification_token"):
                        if not user.verification_token.verified_at:
                            user.verification_token.mark_verified()
                    else:
                        verification_token = EmailVerificationToken.objects.create(
                            user=user
                        )
                        verification_token.mark_verified()

                    # Ensure user profile exists (terms acceptance assumed via OAuth)
                    if not hasattr(user, "profile"):
                        from django.utils import timezone

                        UserProfile.objects.create(
                            user=user,
                            terms_accepted=True,
                            terms_accepted_at=timezone.now(),
                        )

                    # Link social account for existing user found by email
                    SocialAccount.objects.get_or_create(
                        user=user,
                        provider="google",
                        uid=google_id,
                        defaults={"extra_data": google_user},
                    )

                except User.DoesNotExist:
                    # Check if user came from register page with terms already accepted
                    if from_register and terms_accepted_on_register:
                        # Create user immediately - they already accepted terms
                        user = User.objects.create_user(
                            username=email,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            is_active=True,
                        )

                        # Mark email as verified (from Google)
                        verification_token = EmailVerificationToken.objects.create(
                            user=user
                        )
                        verification_token.mark_verified()

                        # Create user profile with terms acceptance and timestamp
                        from django.utils import timezone

                        UserProfile.objects.create(
                            user=user,
                            terms_accepted=True,
                            terms_accepted_at=timezone.now(),
                        )

                        # Link social account
                        SocialAccount.objects.create(
                            user=user,
                            provider="google",
                            uid=google_id,
                            extra_data=google_user,
                        )
                    else:
                        # User came from login page - return error requiring terms acceptance
                        return Response(
                            {
                                "detail": "Terms acceptance required. Please register first."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
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
