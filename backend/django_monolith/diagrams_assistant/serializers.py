from rest_framework import serializers
from .models import Diagram, DiagramVersion, ChatMessage, Workspace
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
    workspace_id = serializers.UUIDField(
        source="workspace.id", read_only=True, allow_null=True
    )
    workspace_name = serializers.CharField(
        source="workspace.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Diagram
        fields = ["id", "title", "updated_at", "workspace_id", "workspace_name"]

    def get_updated_at(self, obj):
        # Use annotated latest version date if available, fall back to diagram creation date
        return getattr(obj, "latest_version_at", None) or obj.created_at


class DiagramUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagram
        fields = ["title"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Workspace name cannot be blank.")
        return value


class DiagramWorkspaceAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagram
        fields = ["workspace"]

    def validate_workspace(self, value):
        request = self.context.get("request")
        if value is not None and value.owner != request.user:
            raise serializers.ValidationError("Workspace not found.")
        return value
