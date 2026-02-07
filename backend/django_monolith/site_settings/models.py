from django.db import models


class SiteSettings(models.Model):
    """Singleton model for global application configuration"""

    quota_limit_default = models.PositiveIntegerField(
        default=10,
        help_text="Default diagram generation limit for new users",
    )
    quota_period_default = models.CharField(
        max_length=10,
        choices=[("day", "Per Day"), ("week", "Per Week"), ("month", "Per Month")],
        default="day",
        help_text="Default quota period for new users",
    )
    email_rate_limit = models.PositiveIntegerField(
        default=5,
        help_text="Maximum emails per hour (registration/password reset)",
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Site Settings"
