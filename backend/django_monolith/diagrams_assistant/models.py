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


class UserQuota(models.Model):
    """Configurable rate limit quota per user for diagram generation."""

    PERIOD_CHOICES = [
        ("day", "Per Day"),
        ("week", "Per Week"),
        ("month", "Per Month"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diagram_quota"
    )
    quota_limit = models.PositiveIntegerField(
        default=10, help_text="Maximum number of diagram generations allowed per period"
    )
    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        default="day",
        help_text="Time period for quota reset",
    )
    is_unlimited = models.BooleanField(
        default=False, help_text="If checked, user has unlimited diagram generations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Quota"
        verbose_name_plural = "User Quotas"

    def __str__(self):
        if self.is_unlimited:
            return f"{self.user.username} - Unlimited"
        return f"{self.user.username} - {self.quota_limit}/{self.get_period_display()}"


class DiagramGenerationLog(models.Model):
    """Logs each diagram generation for rate limiting purposes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="diagram_generation_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
