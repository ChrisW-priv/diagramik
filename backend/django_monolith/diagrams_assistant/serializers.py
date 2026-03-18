from rest_framework import serializers
from .models import Diagram, DiagramVersion, ChatMessage, ChatSession, DiagramCheckpoint
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["role", "content"]


class ChatSessionSerializer(serializers.ModelSerializer):
    parent_checkpoint_id = serializers.UUIDField(
        source="parent_checkpoint.id", read_only=True, default=None
    )
    parent_checkpoint_name = serializers.CharField(
        source="parent_checkpoint.name", read_only=True, default=None
    )

    class Meta:
        model = ChatSession
        fields = ["id", "parent_checkpoint_id", "parent_checkpoint_name", "created_at"]


class DiagramCheckpointSerializer(serializers.ModelSerializer):
    version_id = serializers.UUIDField(source="version.id", read_only=True)

    class Meta:
        model = DiagramCheckpoint
        fields = [
            "id",
            "name",
            "description",
            "version_id",
            "diagram_type",
            "created_at",
        ]


class DiagramCheckpointCreateSerializer(serializers.Serializer):
    version_id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, default="", allow_blank=True)


class DiagramVersionSerializer(serializers.ModelSerializer):
    diagram_id = serializers.UUIDField(source="diagram.id", read_only=True)
    checkpoint_name = serializers.SerializerMethodField()
    source_code = serializers.CharField(read_only=True)
    diagram_type = serializers.CharField(read_only=True)

    class Meta:
        model = DiagramVersion
        fields = [
            "id",
            "diagram_id",
            "created_at",
            "checkpoint_name",
            "source_code",
            "diagram_type",
        ]

    def get_checkpoint_name(self, obj):
        try:
            return obj.checkpoint.name
        except DiagramCheckpoint.DoesNotExist:
            return None


class DiagramSerializer(serializers.ModelSerializer):
    versions = DiagramVersionSerializer(many=True, read_only=True)
    chat_history = serializers.SerializerMethodField()
    checkpoints = DiagramCheckpointSerializer(many=True, read_only=True)
    active_session = ChatSessionSerializer(read_only=True)

    class Meta:
        model = Diagram
        fields = [
            "id",
            "title",
            "versions",
            "chat_history",
            "checkpoints",
            "active_session",
        ]

    def get_chat_history(self, obj):
        if obj.active_session:
            messages = ChatMessage.objects.filter(session=obj.active_session)
        else:
            messages = obj.chat_history.all()
        return ChatMessageSerializer(messages, many=True).data


class DiagramListItemSerializer(serializers.ModelSerializer):
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Diagram
        fields = ["id", "title", "updated_at"]

    def get_updated_at(self, obj):
        # Use annotated latest version date if available, fall back to diagram creation date
        return getattr(obj, "latest_version_at", None) or obj.created_at


class RenderCodeSerializer(serializers.Serializer):
    code = serializers.CharField()
    diagram_type = serializers.ChoiceField(choices=["technical", "mermaid"])
