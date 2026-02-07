from django.conf import settings
from django.core.signing import TimestampSigner
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import json
from urllib.parse import urlencode


class GoogleAuthURLView(APIView):
    """Get Google OAuth URL with optional context encoding"""

    permission_classes = [AllowAny]

    def get(self, request):
        client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
        callback_url = f"{settings.BACKEND_URL}/api/v1/auth/social/google/"

        # Check if this is from register page with terms already accepted
        from_register = request.GET.get("from_register", "").lower() == "true"
        terms_accepted = request.GET.get("terms_accepted", "").lower() == "true"

        # Create OAuth state parameter with context
        state_data = {}
        if from_register and terms_accepted:
            state_data = {"from_register": True, "terms_accepted": True}

        # Sign the state to prevent tampering
        signer = TimestampSigner()
        state_token = signer.sign(json.dumps(state_data)) if state_data else ""

        # Build OAuth URL
        params = {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid email profile",
        }
        if state_token:
            params["state"] = state_token

        oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        return Response({"auth_url": oauth_url})
