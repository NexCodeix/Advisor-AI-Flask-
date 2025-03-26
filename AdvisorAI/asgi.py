import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AdvisorAI.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from main.consumers import AIConsumer

websocket_urlpatterns = [
    path("connect-ai/", AIConsumer.as_asgi(), ),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket":(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
