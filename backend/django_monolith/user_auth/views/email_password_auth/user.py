from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from user_auth.utils import get_user_data


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
