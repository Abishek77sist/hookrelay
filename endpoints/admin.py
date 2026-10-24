from django.contrib import admin

from .models import Endpoint


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_url", "is_active", "consecutive_failures")
    readonly_fields = ("secret",)