from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from user_auth.utils import CsrfExemptMixin
from .callback import verify_register_redirect_token


class DecodeOAuthStateView(CsrfExemptMixin, APIView):
    """Decode register redirect token for frontend prefilling

    This is only used when redirecting users from login → register flow.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        state_token = request.data.get("state_token")

        if not state_token:
            return Response({"detail": "State token required"}, status=400)

        user_data = verify_register_redirect_token(state_token)
        if not user_data:
            return Response({"detail": "Invalid or expired token"}, status=400)

        # Return safe subset of data for prefilling
        return Response(
            {
                "email": user_data["email"],
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
            }
        )
