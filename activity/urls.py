from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (WebsiteViewSet, track_event,people_list, person_detail, person_activities)

router = DefaultRouter()
router.register(r'websites', WebsiteViewSet, basename='website')

urlpatterns = [
    path('track/', track_event, name='track-event'),
    path('people/', people_list, name='people-list'),
    path('people/<int:pk>/', person_detail, name='person-detail'),
    path('people/<int:pk>/activities/', person_activities, name='person-activities'),
]

urlpatterns += router.urls
