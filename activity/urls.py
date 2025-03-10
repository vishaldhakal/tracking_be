from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    WebsiteViewSet, 
    track_event,
    person_activities,
    PeopleListCreateView,
    PeopleRetrieveUpdateDestroyView,
    PeopleFromVisitorIdView
)

router = DefaultRouter()
router.register(r'websites', WebsiteViewSet, basename='website')

urlpatterns = [
    path('track/', track_event, name='track-event'),
    path('people/list/', PeopleListCreateView.as_view(), name='people-list-create'),
    path('people/<int:pk>/', PeopleRetrieveUpdateDestroyView.as_view(), name='people-detail'),
    path('people/<int:pk>/activities/', person_activities, name='person-activities'),
    path('people/visitor_id/<str:visitor_id>/', PeopleFromVisitorIdView.as_view(), name='people-from-visitor-id'),
]

urlpatterns += router.urls
