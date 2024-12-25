from django.urls import re_path
from activity.consumers import ChatConsumer, AdminChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<visitor_id>[^/]+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/admin/chat/(?P<chat_id>\d+)/$', AdminChatConsumer.as_asgi()),
] 