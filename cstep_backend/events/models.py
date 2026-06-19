import secrets
from django.db import models
from django.conf import settings

from .media import build_whip_ingest_url, build_whep_playback_url


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

    video_muted_by_default = models.BooleanField(default=True)
    pause_continue_enabled = models.BooleanField(default=True)
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)

    stream_start_time = models.DateTimeField(null=True, blank=True)
    stream_end_time = models.DateTimeField(null=True, blank=True)

    # Denormalized copy of the primary camera playback URL, set on go_live.
    # Kept here so EventListSerializer can show it without joining broadcast_sessions.
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

    @property
    def primary_broadcast_session(self):
        return self.broadcast_sessions.order_by("-is_primary", "id").first()

    @property
    def broadcast_session(self):
        """
        Backward-compatible alias for code that previously expected one
        broadcast session per event.
        """
        return self.primary_broadcast_session


class BroadcastSession(models.Model):
    """
    One per live event. WHIP ingest / WHEP playback URLs are generated
    automatically on first save — never accept these from a client.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="broadcast_sessions")
    broadcaster = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="broadcast_sessions"
    )

    name = models.CharField(max_length=100, default="Camera 1")
    is_primary = models.BooleanField(default=False)
    stream_key = models.CharField(max_length=64, unique=True, db_index=True, editable=False)
    ingest_url = models.URLField(editable=False)    # WHIP — broadcaster publishes here
    playback_url = models.URLField(editable=False)  # WHEP — viewers subscribe here

    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event"],
                condition=models.Q(is_primary=True),
                name="unique_primary_broadcast_session_per_event",
            )
        ]

    @staticmethod
    def generate_stream_key() -> str:
        return secrets.token_urlsafe(8)  # 11 chars, ~62^11 combinations 18.4 quintillion

    def save(self, *args, **kwargs):
        if self.is_primary and self.event_id:
            BroadcastSession.objects.filter(event_id=self.event_id, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        if not self.stream_key:
            self.stream_key = self.generate_stream_key()
        if not self.ingest_url:
            self.ingest_url = build_whip_ingest_url(self.stream_key)
        if not self.playback_url:
            self.playback_url = build_whep_playback_url(self.stream_key)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} for {self.event.title}"


class ViewerSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="viewer_sessions"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="viewer_sessions")

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    last_heartbeat = models.DateTimeField(null=True, blank=True)
    watch_duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-joined_at"]

    @property
    def is_active(self):
        return self.left_at is None

    def __str__(self):
        return f"{self.user} watching {self.event.title}"


class EventLogin(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_logins"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="logins")
    logged_in_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
