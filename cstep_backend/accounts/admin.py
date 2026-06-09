from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)

    list_display = (
        "id",
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "role",
        "gender",
        "phone_verified",
        "email_verified",
        "is_active",
        "is_staff",
        "created_at",
    )

    list_filter = (
        "role",
        "gender",
        "phone_verified",
        "email_verified",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "email",
        "phone_number",
        "first_name",
        "middle_name",
        "last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
    )

    fieldsets = (
        (
            "Personal Information",
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
            "Contact Information",
            {
                "fields": (
                    "email",
                    "phone_number",
                )
            },
        ),
        (
            "Role & Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "phone_verified",
                    "email_verified",
                )
            },
        ),
        (
            "Authentication",
            {
                "fields": (
                    "password",
                    "last_login",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "salutation",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "gender",
                    "role",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )