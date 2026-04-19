import json
import logging
from datetime import datetime, timezone

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user_auth.utils import get_user_data

logger = logging.getLogger(__name__)


def _backup_user_diagrams_to_gcs(user):
    from diagrams_assistant.models import Diagram
    from diagrams_assistant.serializers import DiagramBackupSerializer
    from google.cloud.storage import Client
    from google.oauth2 import service_account

    diagrams = Diagram.objects.filter(owner=user).prefetch_related(
        "versions", "chat_history"
    )
    data = DiagramBackupSerializer(diagrams, many=True).data
    payload = json.dumps(list(data), default=str)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    blob_path = f"deleted_accounts/{user.pk}/{timestamp}/diagrams.json"

    cred = service_account.Credentials.from_service_account_file(
        settings.SIGNED_URL_SA_KEY_FILENAME
    )
    storage_client = Client(credentials=cred)
    bucket = storage_client.bucket(settings.DIAGRAMS_BUCKET_NAME)
    bucket.blob(blob_path).upload_from_string(payload, content_type="application/json")


class UserView(APIView):
    """Get/update/delete current user"""

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

    def delete(self, request):
        user = request.user
        try:
            _backup_user_diagrams_to_gcs(user)
        except Exception as exc:
            logger.error("GCS backup failed for user %s: %s", user.pk, exc)
            return Response(
                {
                    "detail": "Account deletion is temporarily unavailable. Please try again later."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
