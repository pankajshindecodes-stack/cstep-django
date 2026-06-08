from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
        "email_verified",
        "phone_verified",
    )

    list_filter = (
        "role",
        "gender",
        "is_staff",
        "is_active",
        "is_superuser",
        "email_verified",
        "phone_verified",
    )

    search_fields = (
        "email",
        "phone_number",
        "first_name",
        "middle_name",
        "last_name",
    )

    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "phone_number", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "salutation",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "gender",
                )
            },
        ),
        (
            "Role and verification",
            {
                "fields": (
                    "role",
                    "email_verified",
                    "phone_verified",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone_number",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "role",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")