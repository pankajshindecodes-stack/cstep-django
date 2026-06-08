from rest_framework import serializers
from django.utils import timezone
from .models import Event, EventStatus, BroadcastSession, ViewerSession, EventLogin


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

class EventListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    concurrent_viewers = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "status",
            "scheduled_start", "scheduled_end",
            "stream_start_time", "playback_url",
            "created_by_name", "concurrent_viewers",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}"

    def get_concurrent_viewers(self, obj):
        return obj.viewer_sessions.filter(left_at=None).count()


class EventDetailSerializer(EventListSerializer):
    broadcast_session = serializers.SerializerMethodField()

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            "video_muted_by_default", "pause_continue_enabled",
            "scheduled_end", "stream_end_time", "recording_url",
            "broadcast_session", "updated_at",
        ]

    def get_broadcast_session(self, obj):
        """Only expose ingest credentials to the broadcaster themselves."""
        request = self.context.get("request")
        try:
            session = obj.broadcast_session
        except BroadcastSession.DoesNotExist:
            return None

        data = {"is_active": session.is_active, "protocol": session.protocol}

        if request and (
            request.user == session.broadcaster
            or request.user.role in ("EVENT_ADMIN", "SUPER_ADMIN")
        ):
            data.update({
                "stream_key": session.stream_key,
                "ingest_url": session.ingest_url,
                "started_at": session.started_at,
            })
        return data


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "title", "description", "scheduled_start", "scheduled_end",
            "video_muted_by_default", "pause_continue_enabled",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# BroadcastSession
# ---------------------------------------------------------------------------

class BroadcastSessionSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source="event.title", read_only=True)
    broadcaster_name = serializers.SerializerMethodField()

    class Meta:
        model = BroadcastSession
        fields = [
            "id", "event", "event_title", "broadcaster", "broadcaster_name",
            "stream_key", "ingest_url", "protocol",
            "is_active", "started_at", "ended_at", "created_at",
        ]
        read_only_fields = [
            "stream_key", "is_active", "started_at", "ended_at", "created_at",
        ]

    def get_broadcaster_name(self, obj):
        return f"{obj.broadcaster.first_name} {obj.broadcaster.last_name}"

    def validate_event(self, event):
        if hasattr(event, "broadcast_session"):
            raise serializers.ValidationError("A broadcast session already exists for this event.")
        return event

    def create(self, validated_data):
        validated_data["stream_key"] = BroadcastSession.generate_stream_key()
        return super().create(validated_data)


class BroadcastSessionCreateSerializer(serializers.ModelSerializer):
    """Minimal input — backend fills credentials."""
    class Meta:
        model = BroadcastSession
        fields = ["event", "broadcaster", "ingest_url", "protocol"]

    def validate_event(self, event):
        if hasattr(event, "broadcast_session"):
            raise serializers.ValidationError("Broadcast session already exists for this event.")
        return event

    def create(self, validated_data):
        validated_data["stream_key"] = BroadcastSession.generate_stream_key()
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# ViewerSession
# ---------------------------------------------------------------------------

class ViewerSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    watch_duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = ViewerSession
        fields = [
            "id", "user", "user_name", "event",
            "joined_at", "left_at", "is_active",
            "watch_duration_seconds", "watch_duration_minutes",
            "last_heartbeat",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_watch_duration_minutes(self, obj):
        return round(obj.watch_duration_seconds / 60, 1)


class ViewerJoinSerializer(serializers.Serializer):
    """Response payload when a viewer joins a live event."""
    event_id = serializers.IntegerField()
    event_title = serializers.CharField()
    playback_url = serializers.URLField()
    viewer_session_id = serializers.IntegerField()
    concurrent_viewers = serializers.IntegerField()
    video_muted_by_default = serializers.BooleanField()


# ---------------------------------------------------------------------------
# Webhook (inbound from media server)
# ---------------------------------------------------------------------------

class StreamWebhookSerializer(serializers.Serializer):
    ACTIONS = ["stream.started", "stream.ended", "stream.error"]

    action = serializers.ChoiceField(choices=ACTIONS)
    stream_key = serializers.CharField()
    playback_url = serializers.URLField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False)

    def validate_stream_key(self, value):
        try:
            self._broadcast_session = BroadcastSession.objects.select_related("event").get(
                stream_key=value
            )
        except BroadcastSession.DoesNotExist:
            raise serializers.ValidationError("Invalid stream key.")
        return value

    @property
    def broadcast_session(self):
        return self._broadcast_session


# ---------------------------------------------------------------------------
# Analytics (read-only summary)
# ---------------------------------------------------------------------------

class EventAnalyticsSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    event_title = serializers.CharField()
    status = serializers.CharField()
    total_joins = serializers.IntegerField()
    concurrent_viewers = serializers.IntegerField()
    peak_viewers = serializers.IntegerField()
    avg_watch_duration_minutes = serializers.FloatField()
    stream_duration_minutes = serializers.FloatField(allow_null=True)