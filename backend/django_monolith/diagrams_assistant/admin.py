from django.contrib import admin
from .models import Diagram, DiagramVersion, ChatMessage


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
