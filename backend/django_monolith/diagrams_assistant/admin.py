from django.contrib import admin
from .models import Diagram, DiagramVersion, ChatMessage, ChatSession, DiagramCheckpoint


class DiagramVersionInline(admin.TabularInline):
    model = DiagramVersion
    extra = 0


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0


class ChatSessionInline(admin.TabularInline):
    model = ChatSession
    extra = 0


class DiagramCheckpointInline(admin.TabularInline):
    model = DiagramCheckpoint
    extra = 0


@admin.register(Diagram)
class DiagramAdmin(admin.ModelAdmin):
    inlines = [ChatSessionInline, DiagramVersionInline, DiagramCheckpointInline]
    list_display = ("title", "owner", "created_at")
    search_fields = ("title", "owner__username")


@admin.register(DiagramVersion)
class DiagramVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "diagram", "session", "created_at")
    list_filter = ("diagram",)
    search_fields = ("diagram__title",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "diagram", "session", "role", "created_at")
    list_filter = ("diagram", "role")
    search_fields = ("content",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "diagram", "parent_checkpoint", "created_at")
    list_filter = ("diagram",)


@admin.register(DiagramCheckpoint)
class DiagramCheckpointAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "diagram", "diagram_type", "created_at")
    list_filter = ("diagram", "diagram_type")
    search_fields = ("name", "diagram__title")
