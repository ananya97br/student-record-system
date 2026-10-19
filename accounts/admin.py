from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Notification, OtpToken, SecurityAlert, User


@admin.register(User)
class SrsUserAdmin(UserAdmin):
    model = User
    ordering = ("login_id",)
    list_display = ("login_id", "email", "role", "status", "failed_login_attempts", "last_login_at")
    search_fields = ("login_id", "email")
    fieldsets = ((None, {"fields": ("login_id", "password")}), ("Identity", {"fields": ("email", "role", "status")}), ("Security", {"fields": ("failed_login_attempts", "locked_at", "last_login_at", "token_version")}), ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}))
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("login_id", "email", "password1", "password2", "role")} ),)


@admin.register(AuditLog)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "entity_type", "entity_id", "actor", "correlation_id")
    readonly_fields = tuple(field.name for field in AuditLog._meta.fields)
    search_fields = ("action", "entity_type", "entity_id", "correlation_id")


admin.site.register(OtpToken)
admin.site.register(SecurityAlert)
admin.site.register(Notification)
