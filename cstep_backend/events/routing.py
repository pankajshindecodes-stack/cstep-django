from django.urls import re_path
from .consumers import EventStreamConsumer

websocket_urlpatterns = [
    re_path(r"ws/events/(?P<event_id>\d+)/$", EventStreamConsumer.as_asgi()),
]