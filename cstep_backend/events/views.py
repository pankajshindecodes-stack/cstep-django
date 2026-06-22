from django.utils import timezone
from django.db.models import Avg, Q, Exists, OuterRef, Value, BooleanField

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated

from .utils import _get_client_ip, _get_peak_viewers, _send_ws_event
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
      GET  /events/{id}/broadcast/         — the broadcaster (or admin) — WHIP ingest URL
      GET  /events/{id}/watch/             — any viewer — WHEP playback URL
      POST /events/{id}/join/              — authenticated viewer
      POST /events/{id}/leave/             — authenticated viewer
      POST /events/{id}/heartbeat/         — authenticated viewer
      GET  /events/{id}/analytics/         — MODERATOR+
      GET  /events/{id}/viewers/           — MODERATOR+
      GET  /events/{id}/upcoming/          — all events with registration status
    """

    queryset = Event.objects.select_related("created_by").all()
    search_fields = [
        "title", "description",
        "created_by__first_name", "created_by__last_name", "created_by__email",
    ]
    filterset_fields = {
        "status": ["exact"],
        "created_by": ["exact"],
        "video_muted_by_default": ["exact"],
        "pause_continue_enabled": ["exact"],
        "scheduled_start": ["gte", "lte"],
        "scheduled_end": ["gte", "lte"],
        "created_at": ["gte", "lte"],
    }
    ordering_fields = [
        "title", "status", "scheduled_start", "scheduled_end",
        "stream_start_time", "stream_end_time", "created_at", "updated_at",
    ]

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
        if self.action in ("broadcast",):
            # the designated broadcaster needs their own ingest URL too,
            # not just admins
            return [IsAuthenticated(), IsBroadcasterOrAdmin()]
        if self.action in ("analytics", "viewers"):
            return [IsModeratorOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        event_type = self.request.query_params.get("type")
        if self.action == "list" and event_type:
            TYPE_FILTERS = {
                "upcoming": (Q(scheduled_start__gt=timezone.now()), "scheduled_start"),
                "live": (
                    Q(scheduled_start__lte=timezone.now())
                    & (Q(scheduled_end__gte=timezone.now()) | Q(scheduled_end__isnull=True)),
                    "scheduled_start",
                ),
                "past": (Q(scheduled_end__lt=timezone.now()), "-scheduled_end"),
            }
            entry = TYPE_FILTERS.get(event_type)
            if entry is None:
                raise ValidationError(
                    {"type": f"Invalid value. Choose from: {', '.join(TYPE_FILTERS)}"}
                )
            condition, ordering = entry
            queryset = queryset.filter(condition).order_by(ordering)
        return queryset

    # ------------------------------------------------------------------
    # Stream lifecycle
    # ------------------------------------------------------------------

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        queryset = Event.objects.filter(scheduled_start__gte=timezone.now()).order_by("scheduled_start")

        if request.user.is_authenticated:
            user_registered = Registration.objects.filter(event=OuterRef("pk"), user=request.user)
            queryset = queryset.annotate(is_registered=Exists(user_registered))
        else:
            queryset = queryset.annotate(is_registered=Value(False, output_field=BooleanField()))

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

        sessions = list(event.broadcast_sessions.all())
        if not sessions:
            return Response(
                {"detail": "No broadcast session configured. Create one first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        primary_session = event.primary_broadcast_session

        event.status = EventStatus.LIVE
        event.stream_start_time = timezone.now()
        event.playback_url = primary_session.playback_url
        event.save(update_fields=["status", "stream_start_time", "playback_url", "updated_at"])

        event.broadcast_sessions.update(is_active=True, started_at=event.stream_start_time)

        _send_ws_event(
            event.id,
            {
                "type": "stream.started",
                "playback_urls": [session.playback_url for session in sessions],
            },
        )

        return Response(EventDetailSerializer(event, context={"request": request}).data)

    def _select_broadcast_session(self, event, request, sessions=None):
        camera_id = request.query_params.get("camera_id")
        camera_name = request.query_params.get("camera")
        if sessions is None:
            sessions = event.broadcast_sessions.all()

        if camera_id:
            return sessions.filter(id=camera_id).first()
        if camera_name:
            return sessions.filter(name=camera_name).first()
        return sessions.order_by("-is_primary", "id").first()

    @action(detail=True, methods=["get"], url_path="broadcast")
    def broadcast(self, request, pk=None):
        """
        WHIP is POST-based SDP signaling — the publisher's WebRTC client
        does the handshake via fetch(), so this just hands back the ingest
        URL + key as JSON rather than redirecting a browser to it.
        """
        event = self.get_object()

        if request.user.role in ("EVENT_ADMIN", "SUPER_ADMIN"):
            visible_sessions = event.broadcast_sessions.all()
        else:
            visible_sessions = event.broadcast_sessions.filter(broadcaster=request.user)

        sessions = list(visible_sessions)
        if not sessions:
            return Response(
                {"detail": "No broadcast session configured. Create one first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bs = self._select_broadcast_session(event, request, visible_sessions)
        if bs is None:
            return Response({"detail": "Camera not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "broadcast_sessions": BroadcastSessionSerializer(sessions, many=True).data,
        })

    @action(detail=True, methods=["get"], url_path="watch")
    def watch(self, request, pk=None):
        """Returns the WHEP playback URL for the viewer's client to subscribe to."""
        event = self.get_object()

        sessions = list(event.broadcast_sessions.all())
        if not sessions:
            return Response(
                {"detail": "No broadcast session configured. Create one first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bs = self._select_broadcast_session(event, request)
        if bs is None:
            return Response({"detail": "Camera not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "broadcast_sessions": BroadcastSessionSerializer(sessions, many=True).data,
        })

    @action(detail=True, methods=["post"], url_path="end_stream")
    def end_stream(self, request, pk=None):
        event = self.get_object()

        if event.status != EventStatus.LIVE:
            return Response({"detail": "Event is not live."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        event.status = EventStatus.ENDED
        event.stream_end_time = now
        event.save(update_fields=["status", "stream_end_time", "updated_at"])

        event.broadcast_sessions.update(is_active=False, ended_at=now)

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
            return Response({"detail": "Event is not currently live."}, status=status.HTTP_400_BAD_REQUEST)

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
            "broadcast_sessions": event.broadcast_sessions.all(),
            "viewer_session_id": session.id,
            "concurrent_viewers": concurrent,
            "video_muted_by_default": event.video_muted_by_default,
        }
        return Response(ViewerJoinSerializer(payload).data)

    @action(detail=True, methods=["post"], url_path="leave")
    def leave(self, request, pk=None):
        event = self.get_object()
        now = timezone.now()

        updated = ViewerSession.objects.filter(event=event, user=request.user, left_at=None).update(left_at=now)
        if not updated:
            return Response({"detail": "No active viewer session found."}, status=status.HTTP_404_NOT_FOUND)

        concurrent = event.viewer_sessions.filter(left_at=None).count()
        _send_ws_event(event.id, {"type": "viewer.left", "concurrent_viewers": concurrent})

        return Response({"detail": "Left the stream."})

    @action(detail=True, methods=["post"], url_path="heartbeat")
    def heartbeat(self, request, pk=None):
        event = self.get_object()
        now = timezone.now()

        session = ViewerSession.objects.filter(event=event, user=request.user, left_at=None).first()
        if not session:
            return Response({"detail": "No active session."}, status=status.HTTP_404_NOT_FOUND)

        if session.last_heartbeat:
            elapsed = int((now - session.last_heartbeat).total_seconds())
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
        return Response(ViewerSessionSerializer(sessions, many=True).data)


class BroadcastSessionViewSet(viewsets.ModelViewSet):
    """
    POST   /broadcast-sessions/                     — create (EVENT_ADMIN+)
    GET    /broadcast-sessions/{id}/                — retrieve (broadcaster or admin)
    DELETE /broadcast-sessions/{id}/                — destroy

    POST /broadcast-sessions/{id}/regenerate_key/   — rotate key + URLs together
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
        
        # leaving the URLs pointing at a dead key
        session.stream_key = BroadcastSession.generate_stream_key()
        session.ingest_url = ""
        session.playback_url = ""
        session.save(update_fields=["stream_key", "ingest_url", "playback_url"])
        return Response(BroadcastSessionSerializer(session).data)
