"""
ASGI config for websocket_test project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import game.routing
from game.routing import wsg_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stellar_rush.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(URLRouter(wsg_urlpatterns + wsg_urlpatterns)),
})
