import uuid
from django.db import models
from django.conf import settings


class Diagram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diagrams"
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    agent_history = models.TextField(
        blank=True, default=""
    )  # JSON serialized Fast-Agent history

    def __str__(self):
        return self.title


class DiagramVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagram = models.ForeignKey(
        Diagram, related_name="versions", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    image_uri = models.CharField(
        max_length=1024
    )  # Using CharField to store gs:// or other URIs
    prompt_text = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Version {self.id} for {self.diagram.title}"


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagram = models.ForeignKey(
        Diagram, related_name="chat_history", on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=10, choices=[("user", "user"), ("assistant", "assistant")]
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.diagram.id}] {self.role}: {self.content}"
