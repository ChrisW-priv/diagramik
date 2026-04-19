from rest_framework import serializers
from .models import Diagram, DiagramVersion, ChatMessage
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


class DiagramVersionSerializer(serializers.ModelSerializer):
    diagram_id = serializers.UUIDField(source="diagram.id", read_only=True)

    class Meta:
        model = DiagramVersion
        fields = ["id", "diagram_id", "created_at"]


class DiagramSerializer(serializers.ModelSerializer):
    versions = DiagramVersionSerializer(many=True, read_only=True)
    chat_history = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Diagram
        fields = ["id", "title", "versions", "chat_history"]


class DiagramListItemSerializer(serializers.ModelSerializer):
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Diagram
        fields = ["id", "title", "updated_at"]

    def get_updated_at(self, obj):
        # Use annotated latest version date if available, fall back to diagram creation date
        return getattr(obj, "latest_version_at", None) or obj.created_at


class DiagramVersionBackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagramVersion
        fields = ["id", "created_at", "image_uri", "prompt_text"]


class ChatMessageBackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]


class DiagramBackupSerializer(serializers.ModelSerializer):
    versions = DiagramVersionBackupSerializer(many=True, read_only=True)
    chat_history = ChatMessageBackupSerializer(many=True, read_only=True)

    class Meta:
        model = Diagram
        fields = [
            "id",
            "title",
            "created_at",
            "agent_history",
            "versions",
            "chat_history",
        ]
