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
        "stream_key",
        "started_at",
        "ended_at",
        "created_at",
    )


class ViewerSessionInline(admin.TabularInline):
    model = ViewerSession
    extra = 0
    readonly_fields = (
        "joined_at",
        "left_at",
        "last_heartbeat",
        "watch_duration_seconds",
    )
    can_delete = False
    show_change_link = True


class EventLoginInline(admin.TabularInline):
    model = EventLogin
    extra = 0
    readonly_fields = (
        "logged_in_at",
        "ip_address",
    )
    can_delete = False
    show_change_link = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "created_by",
        "scheduled_start",
        "scheduled_end",
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
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
    )

    readonly_fields = (
        "stream_start_time",
        "stream_end_time",
        "created_at",
        "updated_at",
    )

    inlines = [
        BroadcastSessionInline,
        ViewerSessionInline,
        EventLoginInline,
    ]

    date_hierarchy = "created_at"


@admin.register(BroadcastSession)
class BroadcastSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event",
        "broadcaster",
        "protocol",
        "is_active",
        "started_at",
        "ended_at",
    )

    list_filter = (
        "protocol",
        "is_active",
        "created_at",
    )

    search_fields = (
        "event__title",
        "broadcaster__email",
        "stream_key",
    )

    readonly_fields = (
        "stream_key",
        "started_at",
        "ended_at",
        "created_at",
    )


@admin.register(ViewerSession)
class ViewerSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "joined_at",
        "left_at",
        "watch_duration_seconds",
        "is_active",
    )

    list_filter = (
        "joined_at",
        "event",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "event__title",
    )

    readonly_fields = (
        "joined_at",
        "last_heartbeat",
    )

    date_hierarchy = "joined_at"


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
        "user__email",
        "user__first_name",
        "user__last_name",
        "event__title",
        "ip_address",
    )

    readonly_fields = (
        "logged_in_at",
    )

    date_hierarchy = "logged_in_at"