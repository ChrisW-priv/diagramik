import uuid
from django.db import models
from django.conf import settings


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
        db_table = "diagrams_assistant_userquota"

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
        db_table = "diagrams_assistant_diagramgenerationlog"

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
