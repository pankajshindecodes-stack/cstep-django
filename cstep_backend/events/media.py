"""
Pure helpers for building WebRTC signaling URLs.
No model imports here — both models.py and utils.py can import this
without creating a circular dependency.

Ingest:  WHIP  (WebRTC-HTTP Ingestion Protocol) — broadcaster publishes
Egress:  WHEP  (WebRTC-HTTP Egress Protocol)    — viewers subscribe
"""

from django.conf import settings


def _base_url() -> str:
    return settings.MEDIA_SERVER_WEBRTC_BASE_URL.rstrip("/")


def build_whip_ingest_url(stream_key: str) -> str:
    return f"{_base_url()}/{stream_key}/whip"


def build_whep_playback_url(stream_key: str) -> str:
    return f"{_base_url()}/{stream_key}/whep"
