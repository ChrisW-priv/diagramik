import asyncio
from datetime import timedelta
from django.shortcuts import redirect
from django.db.models import Max
from django.db.models.functions import Coalesce

from google.oauth2 import service_account

from agent import agent

from .models import Diagram, DiagramVersion, ChatMessage, ChatSession, DiagramCheckpoint
from .serializers import (
    DiagramSerializer,
    DiagramListItemSerializer,
    DiagramVersionSerializer,
    DiagramCheckpointSerializer,
    DiagramCheckpointCreateSerializer,
    RenderCodeSerializer,
)
from .utils import extract_diagram_source
from quota_management.throttles import DiagramGenerationThrottle, log_diagram_generation
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from django.conf import settings
from google.cloud.storage import Client, Blob


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


def _populate_version_source(version: DiagramVersion, history_json: str) -> None:
    """Extract and save source code from agent history to a version."""
    source_info = extract_diagram_source(history_json)
    if source_info:
        version.source_code = source_info["source_code"]
        version.diagram_type = source_info["diagram_type"]
        version.save(update_fields=["source_code", "diagram_type"])


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
        return (
            Diagram.objects.filter(owner=self.request.user)
            .annotate(latest_version_at=Max("versions__created_at"))
            .order_by(Coalesce("latest_version_at", "created_at").desc())
        )

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

        # Create session for the diagram
        session = ChatSession.objects.create(
            diagram=diagram,
            agent_history=agent_result.history_json,
        )
        diagram.active_session = session
        diagram.save(update_fields=["active_session"])

        version = DiagramVersion.objects.create(
            diagram=diagram,
            session=session,
            image_uri=agent_result.media_uri,
            prompt_text=text,
            agent_history_snapshot=agent_result.history_json,
        )
        _populate_version_source(version, agent_result.history_json)

        ChatMessage.objects.create(
            diagram=diagram, session=session, role="user", content=text
        )
        ChatMessage.objects.create(
            diagram=diagram, session=session, role="assistant", content="Image Ready!"
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

        session = diagram.active_session
        if not session:
            # Create a session if none exists (shouldn't happen normally)
            session = ChatSession.objects.create(
                diagram=diagram,
                agent_history=diagram.agent_history or "",
            )
            diagram.active_session = session
            diagram.save(update_fields=["active_session"])

        ChatMessage.objects.create(
            diagram=diagram, session=session, role="user", content=text
        )

        # Pass session's history to agent
        previous_history = session.agent_history if session.agent_history else None

        agent_result = asyncio.run(agent(text, previous_history_json=previous_history))

        # Check if diagram was generated
        if not agent_result.media_uri:
            clarification_msg = _extract_clarification_from_history(
                agent_result.history_json
            )
            # Update session history even for clarifications
            session.agent_history = agent_result.history_json
            session.save(update_fields=["agent_history"])
            return Response(
                {"clarification_needed": True, "question": clarification_msg},
                status=status.HTTP_200_OK,
            )

        # Success - update session history
        session.agent_history = agent_result.history_json
        session.save(update_fields=["agent_history"])

        # Also keep diagram.agent_history in sync (backward compat)
        diagram.agent_history = agent_result.history_json
        diagram.save(update_fields=["agent_history"])

        version = DiagramVersion.objects.create(
            diagram=diagram,
            session=session,
            image_uri=agent_result.media_uri,
            prompt_text=text,
            agent_history_snapshot=agent_result.history_json,
        )
        _populate_version_source(version, agent_result.history_json)

        ChatMessage.objects.create(
            diagram=diagram, session=session, role="assistant", content="Image Ready!"
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


class CheckpointListCreate(APIView):
    def get(self, request, diagram_id):
        try:
            diagram = Diagram.objects.get(pk=diagram_id, owner=request.user)
        except Diagram.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        checkpoints = diagram.checkpoints.all().order_by("-created_at")
        serializer = DiagramCheckpointSerializer(checkpoints, many=True)
        return Response(serializer.data)

    def post(self, request, diagram_id):
        try:
            diagram = Diagram.objects.get(pk=diagram_id, owner=request.user)
        except Diagram.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = DiagramCheckpointCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version_id = serializer.validated_data["version_id"]
        name = serializer.validated_data["name"]
        description = serializer.validated_data.get("description", "")

        # Validate version belongs to diagram
        try:
            version = DiagramVersion.objects.get(pk=version_id, diagram=diagram)
        except DiagramVersion.DoesNotExist:
            return Response(
                {"error": "Version not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check name uniqueness
        if DiagramCheckpoint.objects.filter(diagram=diagram, name=name).exists():
            return Response(
                {"error": "A checkpoint with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract source code from version's agent_history_snapshot
        source_info = extract_diagram_source(version.agent_history_snapshot)
        if not source_info:
            # Fall back to version's stored source_code
            if version.source_code:
                source_info = {
                    "source_code": version.source_code,
                    "diagram_type": version.diagram_type or "technical",
                }
            else:
                return Response(
                    {"error": "Could not extract source code for this version"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        checkpoint = DiagramCheckpoint.objects.create(
            diagram=diagram,
            version=version,
            name=name,
            description=description,
            source_code=source_info["source_code"],
            diagram_type=source_info["diagram_type"],
        )

        return Response(
            DiagramCheckpointSerializer(checkpoint).data,
            status=status.HTTP_201_CREATED,
        )


class CheckpointDelete(APIView):
    def delete(self, request, diagram_id, checkpoint_id):
        try:
            checkpoint = DiagramCheckpoint.objects.get(
                pk=checkpoint_id, diagram_id=diagram_id, diagram__owner=request.user
            )
        except DiagramCheckpoint.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        checkpoint.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckpointBranch(APIView):
    throttle_classes = [DiagramGenerationThrottle]

    def post(self, request, diagram_id, checkpoint_id):
        try:
            diagram = Diagram.objects.get(pk=diagram_id, owner=request.user)
        except Diagram.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            checkpoint = DiagramCheckpoint.objects.get(
                pk=checkpoint_id, diagram=diagram
            )
        except DiagramCheckpoint.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        text = request.data.get("text")
        if not text:
            return Response(
                {"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create new session branching from checkpoint
        session = ChatSession.objects.create(
            diagram=diagram,
            parent_checkpoint=checkpoint,
        )

        # Compose synthetic prompt with checkpoint code as context
        synthetic_prompt = (
            f"Here is the current diagram code that I want to iterate on:\n\n"
            f"```\n{checkpoint.source_code}\n```\n\n"
            f"Please modify it based on this request: {text}"
        )

        # Call agent with fresh history (no previous history)
        agent_result = asyncio.run(agent(synthetic_prompt, previous_history_json=None))

        if not agent_result.media_uri:
            clarification_msg = _extract_clarification_from_history(
                agent_result.history_json
            )
            session.agent_history = agent_result.history_json
            session.save(update_fields=["agent_history"])
            diagram.active_session = session
            diagram.save(update_fields=["active_session"])
            return Response(
                {"clarification_needed": True, "question": clarification_msg},
                status=status.HTTP_200_OK,
            )

        # Update session with history
        session.agent_history = agent_result.history_json
        session.save(update_fields=["agent_history"])

        # Set as active session
        diagram.active_session = session
        diagram.save(update_fields=["active_session"])

        version = DiagramVersion.objects.create(
            diagram=diagram,
            session=session,
            image_uri=agent_result.media_uri,
            prompt_text=text,
            agent_history_snapshot=agent_result.history_json,
        )
        _populate_version_source(version, agent_result.history_json)

        # Create banner message
        ChatMessage.objects.create(
            diagram=diagram,
            session=session,
            role="assistant",
            content=f'Branched from checkpoint "{checkpoint.name}"',
        )
        ChatMessage.objects.create(
            diagram=diagram, session=session, role="user", content=text
        )
        ChatMessage.objects.create(
            diagram=diagram, session=session, role="assistant", content="Image Ready!"
        )

        log_diagram_generation(request.user)

        serializer = DiagramVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DirectRender(APIView):
    throttle_classes = [DiagramGenerationThrottle]

    def post(self, request, diagram_id):
        try:
            diagram = Diagram.objects.get(pk=diagram_id, owner=request.user)
        except Diagram.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = RenderCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        diagram_type = serializer.validated_data["diagram_type"]

        session = diagram.active_session
        if not session:
            session = ChatSession.objects.create(
                diagram=diagram,
                agent_history="",
            )
            diagram.active_session = session
            diagram.save(update_fields=["active_session"])

        # Create a synthetic prompt with the user's code
        synthetic_prompt = (
            f"I changed the code myself, here is what I've got. "
            f"Please render this {diagram_type} diagram exactly as-is, "
            f"do not modify the code:\n\n```\n{code}\n```"
        )

        # Pass session's history to agent
        previous_history = session.agent_history if session.agent_history else None
        agent_result = asyncio.run(
            agent(synthetic_prompt, previous_history_json=previous_history)
        )

        if not agent_result.media_uri:
            clarification_msg = _extract_clarification_from_history(
                agent_result.history_json
            )
            session.agent_history = agent_result.history_json
            session.save(update_fields=["agent_history"])
            return Response(
                {"clarification_needed": True, "question": clarification_msg},
                status=status.HTTP_200_OK,
            )

        # Update session history
        session.agent_history = agent_result.history_json
        session.save(update_fields=["agent_history"])

        version = DiagramVersion.objects.create(
            diagram=diagram,
            session=session,
            image_uri=agent_result.media_uri,
            prompt_text=f"[Direct edit] {code[:100]}...",
            agent_history_snapshot=agent_result.history_json,
            source_code=code,
            diagram_type=diagram_type,
        )

        ChatMessage.objects.create(
            diagram=diagram,
            session=session,
            role="user",
            content=f"I edited the {diagram_type} code directly",
        )
        ChatMessage.objects.create(
            diagram=diagram, session=session, role="assistant", content="Image Ready!"
        )

        log_diagram_generation(request.user)

        serializer = DiagramVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
