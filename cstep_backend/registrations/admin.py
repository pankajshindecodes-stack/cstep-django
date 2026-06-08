from django.contrib import admin
from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "participation_date",
        "participation_time",
        "status",
        "travel_status",
        "translation_status",
        "created_at",
    )

    list_filter = (
        "status",
        "participation_time",
        "food_preference",
        "travel_arrangement",
        "travel_status",
        "medical_support",
        "translation_language",
        "translation_status",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "event__title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "user",
        "event",
    )

    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "event",
                    "status",
                )
            },
        ),
        (
            "Participation",
            {
                "fields": (
                    "participation_date",
                    "participation_time",
                )
            },
        ),
        (
            "Food Preference",
            {
                "fields": (
                    "food_preference",
                )
            },
        ),
        (
            "Travel",
            {
                "fields": (
                    "travel_arrangement",
                    "travel_status",
                )
            },
        ),
        (
            "Medical Support",
            {
                "fields": (
                    "medical_support",
                )
            },
        ),
        (
            "Translation",
            {
                "fields": (
                    "translation_language",
                    "translation_status",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    actions = [
        "mark_accepted",
        "mark_held",
        "mark_rejected",
    ]

    @admin.action(description="Mark selected registrations as Accepted")
    def mark_accepted(self, request, queryset):
        queryset.update(status="ACCEPTED")

    @admin.action(description="Mark selected registrations as Held")
    def mark_held(self, request, queryset):
        queryset.update(status="HELD")

    @admin.action(description="Mark selected registrations as Rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(status="REJECTED")