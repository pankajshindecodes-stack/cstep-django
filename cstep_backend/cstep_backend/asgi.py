import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .middleware import JWTAuthMiddlewareStack
from events.routing import websocket_urlpatterns     

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cstep_backend.settings")
 
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})