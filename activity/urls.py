from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    WebsiteViewSet, 
    track_event,
    people_list, 
    person_detail, 
    person_activities,
    PeopleListCreateView,
    PeopleRetrieveUpdateDestroyView
)

router = DefaultRouter()
router.register(r'websites', WebsiteViewSet, basename='website')

urlpatterns = [
    path('track/', track_event, name='track-event'),
    path('people/list/', PeopleListCreateView.as_view(), name='people-list-create'),
    path('people/<int:pk>/', PeopleRetrieveUpdateDestroyView.as_view(), name='people-detail'),
    path('people/<int:pk>/activities/', person_activities, name='person-activities'),
]

urlpatterns += router.urls
