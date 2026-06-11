from django.utils import timezone
from django.db.models import Avg, Max, Count,Exists, OuterRef
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .utils import _get_client_ip, _get_peak_viewers,_send_ws_event
from .models import Event, EventStatus, BroadcastSession, ViewerSession
from registrations.models import Registration

from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    BroadcastSessionCreateSerializer,
    BroadcastSessionSerializer,
    ViewerSessionSerializer,
    ViewerJoinSerializer,
    EventAnalyticsSerializer,
    UpcomingEventSerializer,
)
from .permissions import (
    IsEventAdminOrAbove,
    IsModeratorOrAbove,
    IsBroadcasterOrAdmin,
    IsEventCreatorOrAdmin,
)


# ---------------------------------------------------------------------------
# EventViewSet
# ---------------------------------------------------------------------------

class EventViewSet(viewsets.ModelViewSet):
    """
    list:   GET  /events/                  — all users
    create: POST /events/                  — EVENT_ADMIN+
    detail: GET  /events/{id}/             — all users
    update: PUT  /events/{id}/             — creator or admin
    delete: DELETE /events/{id}/           — creator or admin

    Custom actions:
      POST /events/{id}/go_live/           — EVENT_ADMIN+
      POST /events/{id}/end_stream/        — EVENT_ADMIN+
      POST /events/{id}/join/              — authenticated viewer
      POST /events/{id}/leave/             — authenticated viewer
      POST /events/{id}/heartbeat/         — authenticated viewer
      GET  /events/{id}/analytics/         — MODERATOR+
      GET  /events/{id}/viewers/           — MODERATOR+
      GET  /events/{id}/upcoming/          — all events with registration status
    """

    queryset = Event.objects.select_related("created_by").all()

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        if self.action == "upcoming":
            return UpcomingEventSerializer
        if self.action in ("create", "update", "partial_update"):
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def get_permissions(self):
        if self.action in ("upcoming",):
            return [AllowAny()]
        if self.action in ("create",):
            return [IsEventAdminOrAbove()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsEventCreatorOrAdmin()]
        if self.action in ("go_live", "end_stream"):
            return [IsEventAdminOrAbove()]
        if self.action in ("analytics", "viewers"):
            return [IsModeratorOrAbove()]
        return [IsAuthenticated()]

    # ------------------------------------------------------------------
    # Stream lifecycle
    # ------------------------------------------------------------------
    @action(detail=False,methods=["get"])
    def upcoming(self, request):
        queryset = Event.objects.filter(
            scheduled_start__gte=timezone.now(),
        ).order_by("scheduled_start")

        if request.user.is_authenticated:
            user_registered = Registration.objects.filter(
                event=OuterRef("pk"),
                user=request.user,
            )
            queryset = queryset.annotate(is_registered=Exists(user_registered))

        page = self.paginate_queryset(queryset)
        if page is not None:
            
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=True, methods=["post"], url_path="go_live")
    def go_live(self, request, pk=None):
        event = self.get_object()

        if event.status == EventStatus.LIVE:
            return Response({"detail": "Event is already live."}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(event, "broadcast_session"):
            return Response(
                {"detail": "No broadcast session configured. Create one first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.status = EventStatus.LIVE
        event.stream_start_time = timezone.now()
        event.save(update_fields=["status", "stream_start_time", "updated_at"])

        bs = event.broadcast_session
        bs.is_active = True
        bs.started_at = event.stream_start_time
        bs.save(update_fields=["is_active", "started_at"])

        # Notify connected viewers via WebSocket
        _send_ws_event(event.id, {"type": "stream.started", "playback_url": event.playback_url})

        return Response(EventDetailSerializer(event, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="end_stream")
    def end_stream(self, request, pk=None):
        event = self.get_object()

        if event.status != EventStatus.LIVE:
            return Response({"detail": "Event is not live."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        event.status = EventStatus.ENDED
        event.stream_end_time = now
        event.save(update_fields=["status", "stream_end_time", "updated_at"])

        bs = event.broadcast_session
        bs.is_active = False
        bs.ended_at = now
        bs.save(update_fields=["is_active", "ended_at"])

        # Close all active viewer sessions
        ViewerSession.objects.filter(event=event, left_at=None).update(left_at=now)

        _send_ws_event(event.id, {"type": "stream.ended"})

        return Response({"detail": "Stream ended."})

    # ------------------------------------------------------------------
    # Viewer actions
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="join")
    def join(self, request, pk=None):
        event = self.get_object()

        if event.status != EventStatus.LIVE:
            return Response(
                {"detail": "Event is not currently live."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Close any stale open session for this user
        ViewerSession.objects.filter(event=event, user=request.user, left_at=None).update(
            left_at=timezone.now()
        )

        session = ViewerSession.objects.create(
            user=request.user,
            event=event,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        concurrent = event.viewer_sessions.filter(left_at=None).count()
        _send_ws_event(event.id, {"type": "viewer.joined", "concurrent_viewers": concurrent})

        payload = {
            "event_id": event.id,
            "event_title": event.title,
            "playback_url": event.playback_url,
            "viewer_session_id": session.id,
            "concurrent_viewers": concurrent,
            "video_muted_by_default": event.video_muted_by_default,
        }
        return Response(ViewerJoinSerializer(payload).data)

    @action(detail=True, methods=["post"], url_path="leave")
    def leave(self, request, pk=None):
        event = self.get_object()
        now = timezone.now()

        updated = ViewerSession.objects.filter(
            event=event, user=request.user, left_at=None
        ).update(left_at=now)

        if not updated:
            return Response({"detail": "No active viewer session found."}, status=status.HTTP_404_NOT_FOUND)

        concurrent = event.viewer_sessions.filter(left_at=None).count()
        _send_ws_event(event.id, {"type": "viewer.left", "concurrent_viewers": concurrent})

        return Response({"detail": "Left the stream."})

    @action(detail=True, methods=["post"], url_path="heartbeat")
    def heartbeat(self, request, pk=None):
        """
        Client calls this every ~30s while watching.
        Keeps viewer session alive and accumulates watch time.
        """
        event = self.get_object()
        now = timezone.now()

        session = ViewerSession.objects.filter(
            event=event, user=request.user, left_at=None
        ).first()

        if not session:
            return Response({"detail": "No active session."}, status=status.HTTP_404_NOT_FOUND)

        if session.last_heartbeat:
            elapsed = int((now - session.last_heartbeat).total_seconds())
            # Cap at 60s to avoid inflating on missed heartbeats
            session.watch_duration_seconds += min(elapsed, 60)

        session.last_heartbeat = now
        session.save(update_fields=["last_heartbeat", "watch_duration_seconds"])

        return Response({"status": "ok", "watch_duration_seconds": session.watch_duration_seconds})

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="analytics")
    def analytics(self, request, pk=None):
        event = self.get_object()
        sessions = event.viewer_sessions.all()

        duration_minutes = None
        if event.stream_start_time and event.stream_end_time:
            delta = event.stream_end_time - event.stream_start_time
            duration_minutes = round(delta.total_seconds() / 60, 1)

        avg_watch = sessions.aggregate(avg=Avg("watch_duration_seconds"))["avg"] or 0

        payload = {
            "event_id": event.id,
            "event_title": event.title,
            "status": event.status,
            "total_joins": sessions.count(),
            "concurrent_viewers": sessions.filter(left_at=None).count(),
            "peak_viewers": _get_peak_viewers(event),
            "avg_watch_duration_minutes": round(avg_watch / 60, 1),
            "stream_duration_minutes": duration_minutes,
        }
        return Response(EventAnalyticsSerializer(payload).data)

    @action(detail=True, methods=["get"], url_path="viewers")
    def viewers(self, request, pk=None):
        event = self.get_object()
        sessions = event.viewer_sessions.select_related("user").filter(left_at=None)
        serializer = ViewerSessionSerializer(sessions, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# BroadcastSessionViewSet
# ---------------------------------------------------------------------------

class BroadcastSessionViewSet(viewsets.ModelViewSet):
    """
    POST   /broadcast-sessions/              — create (EVENT_ADMIN+)
    GET    /broadcast-sessions/{id}/         — retrieve
    DELETE /broadcast-sessions/{id}/         — destroy

    POST /broadcast-sessions/{id}/regenerate_key/  — rotate stream key
    """

    queryset = BroadcastSession.objects.select_related("event", "broadcaster").all()
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return BroadcastSessionCreateSerializer
        return BroadcastSessionSerializer

    def get_permissions(self):
        if self.action in ("retrieve",):
            return [IsBroadcasterOrAdmin()]
        return [IsEventAdminOrAbove()]

    @action(detail=True, methods=["post"], url_path="regenerate_key")
    def regenerate_key(self, request, pk=None):
        session = self.get_object()
        if session.is_active:
            return Response(
                {"detail": "Cannot rotate key while stream is active."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.stream_key = BroadcastSession.generate_stream_key()
        session.save(update_fields=["stream_key"])
        return Response({"stream_key": session.stream_key})

