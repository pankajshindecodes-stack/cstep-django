# events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, BroadcastSessionViewSet
from .webhooks import media_server_webhook

router = DefaultRouter()
router.register("events", EventViewSet, basename="event")
router.register("broadcast-sessions", BroadcastSessionViewSet, basename="broadcast-session")

urlpatterns = [
    path("", include(router.urls)),
    path("webhooks/stream/", media_server_webhook, name="stream-webhook"),
]
