from django.db import models
from django.conf import settings


class SocialAccount(models.Model):
    """Links external OAuth provider accounts to Django users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(
        max_length=50, help_text="OAuth provider name (e.g., 'google', 'facebook')"
    )
    uid = models.CharField(max_length=255, help_text="User ID from the OAuth provider")
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional profile data from provider",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("provider", "uid")]
        verbose_name = "Social Account"
        verbose_name_plural = "Social Accounts"
        indexes = [
            models.Index(fields=["provider", "uid"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.provider}"
