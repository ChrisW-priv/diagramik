from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from user_auth.utils import CsrfExemptMixin, get_tokens_for_user, get_user_data
from user_auth.models import SocialAccount, EmailVerificationToken, UserProfile
from .callback import verify_register_redirect_token

User = get_user_model()


class CompleteOAuthRegistrationView(CsrfExemptMixin, APIView):
    """Complete OAuth registration after terms acceptance

    This endpoint handles the flow: Login → OAuth → Register Page → Complete
    Users who clicked Google from register page are handled directly in callback.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        state_token = request.data.get("state_token")
        terms_accepted = request.data.get("terms_accepted", False)

        if not state_token:
            return Response(
                {"detail": "State token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not terms_accepted:
            return Response(
                {"detail": "Terms must be accepted to continue"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify and decode register redirect token (5 min expiry)
        user_data = verify_register_redirect_token(state_token)
        if not user_data:
            return Response(
                {
                    "detail": "Invalid or expired registration link. Please try signing in again."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = user_data["email"]
        google_id = user_data["google_id"]

        # Check if user was created in the meantime (race condition protection)
        try:
            user = User.objects.get(email=email)
            # User exists - ensure social account is linked
            social_account = SocialAccount.objects.filter(
                provider="google", uid=google_id
            ).first()
            if not social_account:
                SocialAccount.objects.create(
                    user=user,
                    provider="google",
                    uid=google_id,
                    extra_data=user_data["extra_data"],
                )
            # Ensure terms are marked as accepted with timestamp
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if not profile.terms_accepted:
                profile.terms_accepted = True
                profile.terms_accepted_at = timezone.now()
                profile.save()
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                is_active=True,
            )

            # Mark email as verified (from Google)
            verification_token = EmailVerificationToken.objects.create(user=user)
            verification_token.mark_verified()

            # Create user profile with terms acceptance and timestamp
            UserProfile.objects.create(
                user=user, terms_accepted=True, terms_accepted_at=timezone.now()
            )

            # Link social account
            SocialAccount.objects.create(
                user=user,
                provider="google",
                uid=google_id,
                extra_data=user_data["extra_data"],
            )

        # Issue JWT tokens
        tokens = get_tokens_for_user(user)
        return Response({**tokens, "user": get_user_data(user)})
