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
    )  # Deprecated: kept for data migration, use ChatSession.agent_history
    active_session = models.ForeignKey(
        "ChatSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagram = models.ForeignKey(
        Diagram, related_name="chat_sessions", on_delete=models.CASCADE
    )
    parent_checkpoint = models.ForeignKey(
        "DiagramCheckpoint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    agent_history = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Session {self.id} for {self.diagram.title}"


class DiagramVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagram = models.ForeignKey(
        Diagram, related_name="versions", on_delete=models.CASCADE
    )
    session = models.ForeignKey(
        ChatSession,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    image_uri = models.CharField(
        max_length=1024
    )  # Using CharField to store gs:// or other URIs
    prompt_text = models.TextField()
    agent_history_snapshot = models.TextField(blank=True, default="")
    source_code = models.TextField(blank=True, default="")
    diagram_type = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Version {self.id} for {self.diagram.title}"


class DiagramCheckpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagram = models.ForeignKey(
        Diagram, related_name="checkpoints", on_delete=models.CASCADE
    )
    version = models.OneToOneField(
        DiagramVersion, related_name="checkpoint", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    source_code = models.TextField()
    diagram_type = models.CharField(
        max_length=20,
        choices=[("technical", "Technical"), ("mermaid", "Mermaid")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["diagram", "name"],
                name="unique_checkpoint_name_per_diagram",
            )
        ]

    def __str__(self):
        return f"Checkpoint '{self.name}' for {self.diagram.title}"


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagram = models.ForeignKey(
        Diagram, related_name="chat_history", on_delete=models.CASCADE
    )
    session = models.ForeignKey(
        ChatSession,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="messages",
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
