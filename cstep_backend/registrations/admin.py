from django.contrib import admin
from .models import Registration, ParticipationDate


class ParticipationDateInline(admin.TabularInline):
    model = ParticipationDate
    extra = 0


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "status",
        "food_preference",
        "travel_arrangement",
        "travel_status",
        "translation_language",
        "translation_status",
        "created_at",
    )

    list_filter = (
        "status",
        "food_preference",
        "travel_arrangement",
        "travel_status",
        "medical_support",
        "translation_language",
        "translation_status",
        "created_at",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone_number",
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

    inlines = [ParticipationDateInline]

    fieldsets = (
        (
            "Registration Details",
            {
                "fields": (
                    "user",
                    "event",
                    "status",
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
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(ParticipationDate)
class ParticipationDateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "registration",
        "date",
        "participation_time",
    )

    list_filter = (
        "participation_time",
        "date",
    )

    search_fields = (
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__user__email",
        "registration__event__title",
    )

    autocomplete_fields = (
        "registration",
    )
