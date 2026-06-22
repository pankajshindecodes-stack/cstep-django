from django.contrib import admin
from .models import Registration, ParticipationDate, RegistrationDetails


class ParticipationDateInline(admin.TabularInline):
    model = ParticipationDate
    extra = 0


class RegistrationDetailsInline(admin.StackedInline):
    model = RegistrationDetails
    extra = 0
    max_num = 1
    can_delete = True
    fieldsets = (
        ("Food Preference", {"fields": ("food_preference",)}),
        ("Travel", {"fields": ("travel_arrangement", "travel_status")}),
        ("Medical Support", {"fields": ("medical_support",)}),
        ("Translation", {"fields": ("translation_language", "translation_status")}),
    )


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "status",
        "participation_time",
        "get_food_preference",
        "get_travel_arrangement",
        "get_travel_status",
        "get_translation_language",
        "get_translation_status",
        "created_at",
    )

    list_filter = (
        "status",
        "participation_time",
        "details__food_preference",
        "details__travel_arrangement",
        "details__travel_status",
        "details__medical_support",
        "details__translation_language",
        "details__translation_status",
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

    inlines = [RegistrationDetailsInline, ParticipationDateInline]

    fieldsets = (
        (
            "Registration Details",
            {
                "fields": (
                    "user",
                    "event",
                    "status",
                    "participation_time",
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "user", "event", "details"
        )

    @admin.display(description="Food Preference")
    def get_food_preference(self, obj):
        return getattr(obj.details, "food_preference", None)

    @admin.display(description="Travel Arrangement")
    def get_travel_arrangement(self, obj):
        return getattr(obj.details, "travel_arrangement", None)

    @admin.display(description="Travel Status")
    def get_travel_status(self, obj):
        return getattr(obj.details, "travel_status", None)

    @admin.display(description="Translation Language")
    def get_translation_language(self, obj):
        return getattr(obj.details, "translation_language", None)

    @admin.display(description="Translation Status")
    def get_translation_status(self, obj):
        return getattr(obj.details, "translation_status", None)


@admin.register(ParticipationDate)
class ParticipationDateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "registration",
        "date",
    )

    list_filter = (
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