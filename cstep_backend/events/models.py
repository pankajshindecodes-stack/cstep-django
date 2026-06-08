import secrets
from django.db import models
from django.conf import settings


class EventStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SCHEDULED = "SCHEDULED", "Scheduled"
    LIVE = "LIVE", "Live"
    ENDED = "ENDED", "Ended"
    CANCELLED = "CANCELLED", "Cancelled"


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.DRAFT)

    # Streaming settings
    video_muted_by_default = models.BooleanField(default=True)
    pause_continue_enabled = models.BooleanField(default=True)
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)

    # Actual stream times (set when broadcaster starts/stops)
    stream_start_time = models.DateTimeField(null=True, blank=True)
    stream_end_time = models.DateTimeField(null=True, blank=True)

    # HLS playback URL (set by media server webhook or manually)
    playback_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_events"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class BroadcastSession(models.Model):
    """
    One per live event. Holds the broadcaster's ingest credentials.
    Created when an admin/moderator sets up streaming for an event.
    """

    class IngestProtocol(models.TextChoices):
        RTMP = "RTMP", "RTMP"
        WHIP = "WHIP", "WHIP (WebRTC)"  # for browser-based broadcasting

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="broadcast_session")
    broadcaster = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="broadcast_sessions"
    )

    # Ingest credentials
    stream_key = models.CharField(max_length=64, unique=True, db_index=True)
    ingest_url = models.URLField()             # e.g. rtmp://yourserver/live
    protocol = models.CharField(max_length=10, choices=IngestProtocol.choices, default=IngestProtocol.RTMP)

    # Session state
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_stream_key():
        return secrets.token_urlsafe(32)

    def __str__(self):
        return f"BroadcastSession for {self.event.title}"


class ViewerSession(models.Model):
    """
    Tracks each viewer joining/leaving an event stream.
    One user can have multiple sessions (rejoins).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="viewer_sessions"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="viewer_sessions")

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Playback state (optional, for analytics)
    last_heartbeat = models.DateTimeField(null=True, blank=True)  # periodic ping from client
    watch_duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-joined_at"]

    @property
    def is_active(self):
        return self.left_at is None

    def __str__(self):
        return f"{self.user} watching {self.event.title}"


class EventLogin(models.Model):
    """Keep as-is — tracks auth logins to the event, separate from viewer sessions."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_logins"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="logins")
    logged_in_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)