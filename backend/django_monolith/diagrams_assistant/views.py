import asyncio
from datetime import timedelta
from django.shortcuts import redirect

from google.oauth2 import service_account

from .models import Diagram, DiagramVersion, ChatMessage
from .serializers import (
    DiagramSerializer,
    DiagramListItemSerializer,
    DiagramVersionSerializer,
)
from quota_management.throttles import DiagramGenerationThrottle, log_diagram_generation
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from django.conf import settings
from google.cloud.storage import Client, Blob

from .agent import agent


def create_publicly_accessible_url(image_uri: str) -> str:
    if image_uri.startswith("gs://"):
        cred = service_account.Credentials.from_service_account_file(
            settings.SIGNED_URL_SA_KEY_FILENAME
        )
        storage_client = Client(credentials=cred)
        blob = Blob.from_uri(image_uri, storage_client)
        return blob.generate_signed_url(expiration=timedelta(hours=3600))
    return image_uri


class DiagramListCreate(generics.ListCreateAPIView):
    serializer_class = DiagramListItemSerializer
    throttle_classes = [DiagramGenerationThrottle]

    def get_throttles(self):
        # Only apply throttle for POST (create) requests
        if self.request.method == "POST":
            return [DiagramGenerationThrottle()]
        return []

    def get_queryset(self):
        return Diagram.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        text = request.data.get("text")
        if not text:
            return Response(
                {"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        agent_result = asyncio.run(agent(text, previous_history_json=None))
        diagram = Diagram.objects.create(
            title=agent_result.diagram_title,
            owner=user,
            agent_history=agent_result.history_json,
        )
        version = DiagramVersion.objects.create(
            diagram=diagram, image_uri=agent_result.media_uri, prompt_text=text
        )
        ChatMessage.objects.create(diagram=diagram, role="user", content=text)
        ChatMessage.objects.create(
            diagram=diagram, role="assistant", content="Image Ready!"
        )
        # Log the generation for rate limiting
        log_diagram_generation(user)
        serializer = DiagramVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DiagramDetail(generics.RetrieveDestroyAPIView):
    serializer_class = DiagramSerializer

    def get_queryset(self):
        return Diagram.objects.filter(owner=self.request.user)


class DiagramVersionCreate(APIView):
    throttle_classes = [DiagramGenerationThrottle]

    def post(self, request, diagram_id):
        try:
            diagram = Diagram.objects.get(pk=diagram_id, owner=request.user)
        except Diagram.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        text = request.data.get("text")
        if not text:
            return Response(
                {"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        ChatMessage.objects.create(diagram=diagram, role="user", content=text)

        # Pass previous history to agent
        previous_history = diagram.agent_history if diagram.agent_history else None
        agent_result = asyncio.run(agent(text, previous_history_json=previous_history))

        # Update stored history
        diagram.agent_history = agent_result.history_json
        diagram.save(update_fields=["agent_history"])

        version = DiagramVersion.objects.create(
            diagram=diagram, image_uri=agent_result.media_uri, prompt_text=text
        )

        ChatMessage.objects.create(
            diagram=diagram, role="assistant", content="Image Ready!"
        )

        # Log the generation for rate limiting
        log_diagram_generation(request.user)

        serializer = DiagramVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DiagramVersionImage(APIView):
    def get(self, request: Request, diagram_id, version_id):
        try:
            version = DiagramVersion.objects.get(
                pk=version_id, diagram_id=diagram_id, diagram__owner=request.user
            )
        except DiagramVersion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        image_url = create_publicly_accessible_url(version.image_uri)
        should_redirect = request.query_params.get("redirect", "true") == "true"
        if should_redirect:
            return redirect(image_url)
        else:
            return Response({"image_url": image_url})


class DiagramVersionDelete(APIView):
    def delete(self, request, diagram_id, version_id):
        try:
            # Ensure the user owns the diagram this version belongs to
            version = DiagramVersion.objects.get(
                pk=version_id, diagram_id=diagram_id, diagram__owner=request.user
            )
        except DiagramVersion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        version.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
