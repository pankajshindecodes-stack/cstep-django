from django.contrib import admin
from .models import (
    Event,
    BroadcastSession,
    ViewerSession,
    EventLogin,
)


class BroadcastSessionInline(admin.StackedInline):
    model = BroadcastSession
    extra = 0
    readonly_fields = (
        "ingest_url",
        "stream_key",
        "created_at",
        "started_at",
        "ended_at",
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "created_by",
        "scheduled_start",
        "scheduled_end",
        "stream_start_time",
        "stream_end_time",
        "created_at",
    )

    list_filter = (
        "status",
        "video_muted_by_default",
        "pause_continue_enabled",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "stream_start_time",
        "stream_end_time",
    )

    autocomplete_fields = ("created_by",)

    inlines = [BroadcastSessionInline]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "title",
                    "description",
                    "status",
                    "created_by",
                )
            },
        ),
        (
            "Streaming Configuration",
            {
                "fields": (
                    "video_muted_by_default",
                    "pause_continue_enabled",
                    "scheduled_start",
                    "scheduled_end",
                )
            },
        ),
        (
            "Streaming URLs",
            {
                "fields": (
                    "playback_url",
                    "recording_url",
                )
            },
        ),
        (
            "Stream Runtime",
            {
                "fields": (
                    "stream_start_time",
                    "stream_end_time",
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


@admin.register(BroadcastSession)
class BroadcastSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event",
        "broadcaster",
        "is_active",
        "started_at",
        "ended_at",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "event__title",
        "broadcaster__first_name",
        "broadcaster__last_name",
        "broadcaster__email",
        "stream_key",
    )

    readonly_fields = (
        "ingest_url",
        "stream_key",
        "created_at",
        "started_at",
        "ended_at",
    )

    autocomplete_fields = (
        "event",
        "broadcaster",
    )

    fieldsets = (
        (
            "Event",
            {
                "fields": (
                    "event",
                    "broadcaster",
                )
            },
        ),
        (
            "Ingest Configuration",
            {
                "fields": (
                    "ingest_url",
                    "stream_key",
                )
            },
        ),
        (
            "Session Status",
            {
                "fields": (
                    "is_active",
                    "started_at",
                    "ended_at",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at",)
            },
        ),
    )


@admin.register(ViewerSession)
class ViewerSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "joined_at",
        "left_at",
        "is_active",
        "watch_duration_seconds",
    )

    list_filter = (
        "joined_at",
        "left_at",
        "event",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "event__title",
        "ip_address",
    )

    readonly_fields = (
        "joined_at",
        "last_heartbeat",
    )

    autocomplete_fields = (
        "user",
        "event",
    )


@admin.register(EventLogin)
class EventLoginAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "logged_in_at",
        "ip_address",
    )

    list_filter = (
        "logged_in_at",
        "event",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "event__title",
        "ip_address",
    )

    readonly_fields = (
        "logged_in_at",
    )

    autocomplete_fields = (
        "user",
        "event",
    )