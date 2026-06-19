# Live Streaming With Self-Hosted WebRTC

This project includes a self-hosted MediaMTX container. For browser-based streaming, use WebRTC/WHIP. No paid streaming service or OBS is required.

## Start Services

Start the media server:

```powershell
docker compose up -d mediamtx
```

Start Django separately:

```powershell
python manage.py runserver
```

## Django Settings

The backend uses these defaults:

```env
MEDIA_SERVER_WEBRTC_BASE_URL=http://localhost:8889/live
MEDIA_SERVER_RTMP_BASE_URL=rtmp://localhost:1935/live
MEDIA_SERVER_HLS_BASE_URL=http://localhost:8888/live
```

Use your server domain or IP instead of `localhost` when testing from another device. Browser camera access usually requires `localhost` or HTTPS.

## Create A WebRTC Broadcast Session

`ingest_url` is optional. For WebRTC, send `protocol: "WHIP"`:

```json
{
  "event": 1,
  "broadcaster": 1,
  "protocol": "WHIP"
}
```

The response includes:

```json
{
  "stream_key": "...",
  "ingest_url": "http://localhost:8889/live/<stream_key>/whip",
  "publish_url": "http://localhost:8889/live/<stream_key>/publish",
  "playback_url": "http://localhost:8889/live/<stream_key>"
}
```

## Open Broadcaster In Browser

Open the Django redirect endpoint:

```text
http://localhost:8000/events/<event_id>/broadcast/
```

Django redirects to the MediaMTX browser publisher:

```text
http://localhost:8889/live/<stream_key>/publish
```

Allow camera and microphone access, then start publishing.

## Start Event In Django

After the browser publisher is open, call:

```http
POST /events/<event_id>/go_live/
```

For a `WHIP` session, Django sets the event playback URL to:

```text
http://localhost:8889/live/<stream_key>
```

## Open Viewer In Browser

Open the Django redirect endpoint:

```text
http://localhost:8000/events/<event_id>/watch/
```

Or open the returned playback URL directly:

```text
http://localhost:8889/live/<stream_key>
```

## Viewer API Flow

After the event is live:

```http
POST /events/<event_id>/join/
```

The response returns `playback_url` and `viewer_session_id`.

For live status updates, connect:

```text
ws://localhost:8000/ws/events/<event_id>/?token=<access_token>
```

## Stop Stream

Stop publishing in the browser, then call:

```http
POST /events/<event_id>/end_stream/
```
