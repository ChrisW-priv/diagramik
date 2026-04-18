import asyncio
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Max
from django.db.models.functions import Coalesce
from django.shortcuts import redirect
from google.cloud.storage import Blob, Client
from google.oauth2 import service_account
from quota_management.throttles import DiagramGenerationThrottle, log_diagram_generation
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from agent import agent

from .models import ChatMessage, Diagram, DiagramShareLink, DiagramVersion, Workspace
from .serializers import (
    DiagramListItemSerializer,
    DiagramSerializer,
    DiagramUpdateSerializer,
    DiagramVersionSerializer,
    DiagramWorkspaceAssignSerializer,
    WorkspaceSerializer,
)


def _extract_clarification_from_history(history_json: str) -> str:
    """Extract the last assistant message from history (fallback response).

    Args:
        history_json: JSON string containing conversation history

    Returns:
        The clarification message from the fallback agent
    """
    from fast_agent.mcp.prompt_serialization import from_json

    messages = from_json(history_json)
    # Find last assistant message (the fallback agent's response)
    for msg in reversed(messages):
        if msg.role == "assistant" and msg.content:
            for content_item in msg.content:
                if hasattr(content_item, "text"):
                    return content_item.text

    return "Could not generate diagram. Please try rephrasing your request."


def create_publicly_accessible_url(image_uri: str) -> str:
    if image_uri.startswith("gs://"):
        if settings.SIGNED_URL_SA_KEY_FILENAME is None:
            raise ImproperlyConfigured(
                "SIGNED_URL_SA_KEY_FILENAME setting is not configured. "
                "Set the SIGNED_URL_SA_KEY_FILENAME environment variable to the path "
                "of a service account key JSON file."
            )
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
        qs = (
            Diagram.objects.filter(owner=self.request.user)
            .annotate(latest_version_at=Max("versions__created_at"))
            .order_by(Coalesce("latest_version_at", "created_at").desc())
        )
        workspace_param = self.request.query_params.get("workspace")
        if workspace_param is not None:
            if workspace_param == "none":
                qs = qs.filter(workspace__isnull=True)
            else:
                qs = qs.filter(workspace_id=workspace_param)
        return qs

    def create(self, request, *args, **kwargs):
        text = request.data.get("text")
        if not text:
            return Response(
                {"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user

        agent_result = asyncio.run(agent(text, previous_history_json=None))

        # Check if diagram was generated (media_uri will be empty if fallback agent was called)
        if not agent_result.media_uri:
            # No diagram generated - fallback agent was called
            # Extract clarification message from history
            clarification_msg = _extract_clarification_from_history(
                agent_result.history_json
            )
            return Response(
                {"clarification_needed": True, "question": clarification_msg},
                status=status.HTTP_200_OK,
            )

        # Success - diagram was generated
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


class DiagramDetail(generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Diagram.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DiagramUpdateSerializer
        return DiagramSerializer


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

        # Check if diagram was generated (media_uri will be empty if fallback agent was called)
        if not agent_result.media_uri:
            # No diagram generated - fallback agent was called
            # Extract clarification message from history
            clarification_msg = _extract_clarification_from_history(
                agent_result.history_json
            )
            # Update stored history even for clarifications
            diagram.agent_history = agent_result.history_json
            diagram.save(update_fields=["agent_history"])
            return Response(
                {"clarification_needed": True, "question": clarification_msg},
                status=status.HTTP_200_OK,
            )

        # Success - diagram was generated
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


class DiagramShareLinkCreate(APIView):
    """POST /api/v1/diagrams/{diagram_id}/versions/{version_id}/share/
    Public. Returns (or creates) a shareable link for a diagram version."""

    def post(self, request, diagram_id, version_id):
        try:
            version = DiagramVersion.objects.get(pk=version_id, diagram_id=diagram_id)
        except DiagramVersion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        share_link, created = DiagramShareLink.objects.get_or_create(
            diagram_version=version
        )
        share_url = f"{settings.SITE_URL}/share/{share_link.token}"
        return Response(
            {"token": share_link.token, "share_url": share_url},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DiagramShareLinkResolve(APIView):
    """GET /api/v1/share/{token}/
    No auth required. Returns image_uri for the given token. Used by the Cloud Function."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        try:
            share_link = DiagramShareLink.objects.select_related("diagram_version").get(
                pk=token
            )
        except DiagramShareLink.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({"image_uri": share_link.diagram_version.image_uri})


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


class WorkspaceListCreate(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        return Workspace.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class WorkspaceDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceSerializer
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Workspace.objects.filter(owner=self.request.user)


class DiagramWorkspaceAssign(generics.UpdateAPIView):
    serializer_class = DiagramWorkspaceAssignSerializer
    http_method_names = ["patch", "head", "options"]

    def get_queryset(self):
        return Diagram.objects.filter(owner=self.request.user)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx
