from django.contrib import admin
from .models import Registration, ParticipationDate, TravelAssistance, MedicalAssistance, TranslationAssistance


class ParticipationDateInline(admin.TabularInline):
    model = ParticipationDate
    extra = 0


class TravelAssistanceInline(admin.TabularInline):
    model = TravelAssistance
    extra = 0
    fields = ("transport_mode", "source_location", "destination_location", "travel_date", "status")


class MedicalAssistanceInline(admin.StackedInline):
    model = MedicalAssistance
    extra = 0
    max_num = 1
    can_delete = True
    fields = ("medical_needs", "date", "status")


class TranslationAssistanceInline(admin.StackedInline):
    model = TranslationAssistance
    extra = 0
    max_num = 1
    can_delete = True
    fields = ("language", "date", "status")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "status",
        "participation_time",
        "food_preference",
        "attendance_mode",
        "created_at",
    )

    list_filter = (
        "status",
        "participation_time",
        "food_preference",
        "attendance_mode",
        "travel_assistance__transport_mode",
        "travel_assistance__status",
        "medical_assistance__status",
        "translation_assistance__language",
        "translation_assistance__status",
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

    inlines = [
        ParticipationDateInline,
        TravelAssistanceInline,
        MedicalAssistanceInline,
        TranslationAssistanceInline,
    ]

    fieldsets = (
        (
            "Registration Details",
            {
                "fields": (
                    "user",
                    "event",
                    "status",
                    "participation_time",
                    "attendance_mode",
                    "food_preference",
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
        return (
            super().get_queryset(request)
            .select_related("user", "event")
            .prefetch_related(
                "travel_assistance",
                "medical_assistance",
                "translation_assistance",
            )
        )


@admin.register(ParticipationDate)
class ParticipationDateAdmin(admin.ModelAdmin):
    list_display = ("id", "registration", "date")
    list_filter = ("date",)
    search_fields = (
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__user__email",
        "registration__event__title",
    )
    autocomplete_fields = ("registration",)


@admin.register(TravelAssistance)
class TravelAssistanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "registration",
        "transport_mode",
        "source_location",
        "destination_location",
        "travel_date",
        "status",
        "created_at",
    )
    list_filter = ("transport_mode", "status", "travel_date")
    search_fields = (
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__user__email",
        "registration__event__title",
        "source_location",
        "destination_location",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("registration",)


@admin.register(MedicalAssistance)
class MedicalAssistanceAdmin(admin.ModelAdmin):
    list_display = ("id", "registration", "date", "status", "created_at")
    list_filter = ("status", "date")
    search_fields = (
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__user__email",
        "registration__event__title",
        "medical_needs",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("registration",)


@admin.register(TranslationAssistance)
class TranslationAssistanceAdmin(admin.ModelAdmin):
    list_display = ("id", "registration", "language", "date", "status", "created_at")
    list_filter = ("language", "status", "date")
    search_fields = (
        "registration__user__first_name",
        "registration__user__last_name",
        "registration__user__email",
        "registration__event__title",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("registration",)