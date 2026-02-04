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


class EmailVerificationToken(models.Model):
    """Tracks email verification tokens and resend attempts."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_token",
    )
    resend_count = models.PositiveIntegerField(default=0)
    last_sent_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    is_invalidated = models.BooleanField(default=False)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        indexes = [
            models.Index(fields=["user", "is_invalidated"]),
        ]

    def can_resend(self):
        """Check if user can request another verification email."""
        from django.utils import timezone
        from datetime import timedelta

        # Get configurable values from settings (with defaults)
        max_resends = getattr(settings, "EMAIL_VERIFICATION_MAX_RESENDS", 5)
        cooldown_minutes = getattr(settings, "EMAIL_VERIFICATION_COOLDOWN_MINUTES", 10)

        if self.resend_count >= max_resends:
            return False, f"Maximum resend attempts ({max_resends}) reached."

        cooldown_period = timedelta(minutes=cooldown_minutes)
        if timezone.now() - self.last_sent_at < cooldown_period:
            remaining = (self.last_sent_at + cooldown_period) - timezone.now()
            minutes_left = int(remaining.total_seconds() / 60) + 1
            return (
                False,
                f"Please wait {minutes_left} more minute(s) before requesting a new email.",
            )

        return True, None

    def mark_verified(self):
        """Mark the email as verified."""
        from django.utils import timezone

        self.verified_at = timezone.now()
        self.save()

    def invalidate(self):
        """Invalidate this token (used before resending)."""
        from django.utils import timezone

        self.is_invalidated = True
        self.invalidated_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.email} - Resends: {self.resend_count}"


class PasswordResetToken(models.Model):
    """Tracks password reset requests and rate limiting."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    request_count = models.PositiveIntegerField(default=0)
    last_requested_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        indexes = [
            models.Index(fields=["user", "is_used"]),
        ]

    def can_request_reset(self):
        """Check if user can request password reset."""
        from django.utils import timezone
        from datetime import timedelta

        max_requests = getattr(settings, "PASSWORD_RESET_MAX_REQUESTS", 5)
        cooldown_minutes = getattr(settings, "PASSWORD_RESET_COOLDOWN_MINUTES", 10)

        if self.request_count >= max_requests:
            return False, f"Maximum password reset requests ({max_requests}) reached."

        cooldown_period = timedelta(minutes=cooldown_minutes)
        if timezone.now() - self.last_requested_at < cooldown_period:
            remaining = (self.last_requested_at + cooldown_period) - timezone.now()
            minutes_left = int(remaining.total_seconds() / 60) + 1
            return (
                False,
                f"Please wait {minutes_left} more minute(s) before requesting another reset.",
            )

        return True, None

    def mark_used(self):
        """Mark token as used."""
        from django.utils import timezone

        self.is_used = True
        self.used_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.email} - Requests: {self.request_count}"
