from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ApiKey, User

admin.site.register(User, UserAdmin)


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("prefix", "user", "name", "is_active", "created_at", "last_used_at")
    readonly_fields = ("key_hash",)