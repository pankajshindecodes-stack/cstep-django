
import logging
from django.utils import timezone
from .models import Event, EventStatus, BroadcastSession, ViewerSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_peak_viewers(event):
    """
    Approximation: count of sessions that were active at any point.
    For true concurrent peak, you'd store snapshots via a periodic task.
    """
    return event.viewer_sessions.count()


def _send_ws_event(event_id: int, payload: dict):
    """
    Push a message to all viewers of this event via Django Channels.
    Import guard keeps this safe if Channels isn't installed yet.
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        layer = get_channel_layer()
        if layer:
            async_to_sync(layer.group_send)(
                f"event_{event_id}",
                {"type": "event.broadcast", "payload": payload},
            )
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Webhook Handlers
# ---------------------------------------------------------------------------

def _handle_stream_started(bs: BroadcastSession, event: Event, data: dict):
    now = data.get("timestamp") or timezone.now()
    playback_url = data.get("playback_url", "")

    bs.is_active = True
    bs.started_at = now
    bs.save(update_fields=["is_active", "started_at"])

    event.status = EventStatus.LIVE
    event.stream_start_time = now
    if playback_url:
        event.playback_url = playback_url
    event.save(update_fields=["status", "stream_start_time", "playback_url", "updated_at"])

    _send_ws_event(event.id, {
        "type": "stream.started",
        "playback_url": event.playback_url,
    })
    logger.info("Event %s went LIVE via webhook.", event.id)


def _handle_stream_ended(bs: BroadcastSession, event: Event):
    now = timezone.now()

    bs.is_active = False
    bs.ended_at = now
    bs.save(update_fields=["is_active", "ended_at"])

    event.status = EventStatus.ENDED
    event.stream_end_time = now
    event.save(update_fields=["status", "stream_end_time", "updated_at"])

    # Close all active viewer sessions
    ViewerSession.objects.filter(event=event, left_at=None).update(left_at=now)

    _send_ws_event(event.id, {"type": "stream.ended"})
    logger.info("Event %s ENDED via webhook.", event.id)


def _handle_stream_error(bs: BroadcastSession, event: Event):
    logger.error("Stream error reported for event %s.", event.id)
    bs.is_active = False
    bs.save(update_fields=["is_active"])

    _send_ws_event(event.id, {
        "type": "stream.error",
        "message": "The stream encountered an error. Please try again.",
    })