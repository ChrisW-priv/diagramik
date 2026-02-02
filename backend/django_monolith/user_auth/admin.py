from django.contrib import admin
from .models import SocialAccount


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "uid", "created_at"]
    list_filter = ["provider"]
    search_fields = ["user__email", "user__username", "uid"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user"]
