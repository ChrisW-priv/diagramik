from django.contrib import admin
from .models import SocialAccount, EmailVerificationToken, PasswordResetToken


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "uid", "created_at"]
    list_filter = ["provider"]
    search_fields = ["user__email", "user__username", "uid"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user"]


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "resend_count",
        "last_sent_at",
        "verified_at",
        "is_invalidated",
    ]
    list_filter = ["is_invalidated", "verified_at"]
    search_fields = ["user__email", "user__username"]
    readonly_fields = ["created_at", "last_sent_at", "verified_at", "invalidated_at"]
    raw_id_fields = ["user"]

    def has_add_permission(self, request):
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "request_count", "last_requested_at", "is_used", "used_at"]
    list_filter = ["is_used"]
    search_fields = ["user__email", "user__username"]
    readonly_fields = ["created_at", "last_requested_at", "used_at"]
    raw_id_fields = ["user"]

    def has_add_permission(self, request):
        return False
