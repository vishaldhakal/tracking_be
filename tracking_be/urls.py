from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from activity.views import (
    WebsiteViewSet, track_event, dashboard_stats,
    people_list, person_detail, person_activities,
    start_chat, send_message, chat_messages,
    live_visitors, visitor_activities, initiate_chat,
    visitor_chat, get_visitor_chat
)

router = DefaultRouter()
router.register(r'websites', WebsiteViewSet, basename='website')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/track/', track_event, name='track-event'),
    path('api/dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('api/people/', people_list, name='people-list'),
    path('api/people/<int:pk>/', person_detail, name='person-detail'),
    path('api/people/<int:pk>/activities/', person_activities, name='person-activities'),
    path('api/chat/start/', start_chat, name='start-chat'),
    path('api/chat/message/', send_message, name='send-message'),
    path('api/chat/<int:chat_id>/messages/', chat_messages, name='chat-messages'),
    path('api/dashboard/live-visitors/', live_visitors, name='live-visitors'),
    path('api/visitor/<str:visitor_id>/activities/', visitor_activities, name='visitor-activities'),
    path('api/chat/initiate/', initiate_chat, name='initiate-chat'),
    path('api/visitor/<str:visitor_id>/chat/', visitor_chat, name='visitor-chat'),
    path('api/chat/visitor/<str:visitor_id>/chat/', get_visitor_chat, name='get-visitor-chat'),
]
