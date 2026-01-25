from django.contrib import admin
from .models import (
    Diagram,
    DiagramVersion,
    ChatMessage,
    UserQuota,
    DiagramGenerationLog,
)


class DiagramVersionInline(admin.TabularInline):
    model = DiagramVersion
    extra = 0


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0


@admin.register(Diagram)
class DiagramAdmin(admin.ModelAdmin):
    inlines = [DiagramVersionInline, ChatMessageInline]
    list_display = ("title", "owner", "created_at")
    search_fields = ("title", "owner__username")


@admin.register(DiagramVersion)
class DiagramVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "diagram", "created_at")
    list_filter = ("diagram",)
    search_fields = ("diagram__title",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "diagram", "role", "created_at")
    list_filter = ("diagram", "role")
    search_fields = ("content",)


@admin.register(UserQuota)
class UserQuotaAdmin(admin.ModelAdmin):
    list_display = ("user", "quota_limit", "period", "is_unlimited", "updated_at")
    list_filter = ("period", "is_unlimited")
    search_fields = ("user__username", "user__email")
    list_editable = ("quota_limit", "period", "is_unlimited")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user",)}),
        (
            "Quota Settings",
            {
                "fields": ("quota_limit", "period", "is_unlimited"),
                "description": "Configure the rate limit for diagram generation. "
                'Set "is_unlimited" to True to remove all limits for this user.',
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(DiagramGenerationLog)
class DiagramGenerationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    list_filter = ("user", "created_at")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
    readonly_fields = ("id", "user", "created_at")

    def has_add_permission(self, request):
        # Logs should only be created by the system
        return False

    def has_change_permission(self, request, obj=None):
        return False
