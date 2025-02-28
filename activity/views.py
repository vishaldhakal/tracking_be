from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Website, Activity, People
from .serializers import (
    WebsiteSerializer, 
    ActivitySerializer, 
    TrackingEventSerializer,
    PeopleSerializer,
    ActivitySmallSerializer,
    PeopleWithActivitiesSerializer,
)
from .filters import PeopleFilter
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

class WebsiteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WebsiteSerializer

    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([AllowAny])
def track_event(request):
    serializer = TrackingEventSerializer(data=request.data)
    if serializer.is_valid():
        site_id = serializer.validated_data['site_id']
        website = get_object_or_404(Website, site_id=site_id)
        
        visitor_id = serializer.validated_data.get('visitor_id')
        form_data = serializer.validated_data.get('form_data', {})
        
        # Try to find existing person by visitor_id
        person = People.objects.filter(visitor_id=visitor_id).first()
        
        # Handle form submission data
        if serializer.validated_data.get('event_type') == 'Form Submission' and form_data:
            email = form_data.get('email')
            if email:
                # Update or create person with all form data
                person, created = People.objects.update_or_create(
                    email=email,
                    defaults={
                        'name': form_data.get('name', ''),
                        'phone': form_data.get('phone', ''),
                        'visitor_id': visitor_id,
                        'user_agent': serializer.validated_data.get('user_agent'),
                        'language': serializer.validated_data.get('language'),
                        'screen_resolution': serializer.validated_data.get('screen_resolution'),
                        'last_activity': timezone.now(),
                        'stage': 'Contact',
                    }
                )
        
        # Only create activity record if we have an identified person
        if person:
            activity = Activity.objects.create(
                website=website,
                visitor_id=visitor_id,
                people=person,
                activity_type=serializer.validated_data.get('event_type'),
                page_url=serializer.validated_data.get('page_url'),
                page_title=serializer.validated_data.get('page_title'),
                page_referrer=serializer.validated_data.get('page_referrer'),
                form_data=form_data,
                metadata=serializer.validated_data.get('metadata'),
                user_agent=serializer.validated_data.get('user_agent'),
                language=serializer.validated_data.get('language'),
                screen_resolution=serializer.validated_data.get('screen_resolution'),
            )
            
            # Update person's last activity
            person.last_activity = timezone.now()
            person.save(update_fields=['last_activity'])
            
            return Response(ActivitySerializer(activity).data)
            
        # If no person found, just return success without creating activity
        return Response({'status': 'success', 'message': 'Event received but not stored (anonymous user)'})
    
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def people_list(request):
    people = People.objects.annotate(
        is_online=models.Exists(
            Activity.objects.filter(
                people=models.OuterRef('pk'),
            )
        )
    ).order_by('-last_activity')[:10]
    return Response(PeopleWithActivitiesSerializer(people, many=True).data)

@api_view(['GET'])
def person_detail(request, pk):
    person = get_object_or_404(People, pk=pk)
    return Response(PeopleSerializer(person).data)

@api_view(['GET'])
@permission_classes([AllowAny])
def person_activities(request, pk):
    activities = Activity.objects.filter(people_id=pk).order_by('-occured_at')
    return Response(ActivitySmallSerializer(activities, many=True).data)

class PeopleListCreateView(generics.ListCreateAPIView):
    queryset = People.objects.all()
    serializer_class = PeopleWithActivitiesSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PeopleFilter
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'last_activity']
    ordering = ['-last_activity']
    
    def get_queryset(self):
        return People.objects.annotate(
            is_online=models.Exists(
                Activity.objects.filter(
                    people=models.OuterRef('pk'),
                    occured_at__gte=timezone.now() - timezone.timedelta(minutes=5)
                )
            )
        )

class PeopleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = People.objects.all()
    serializer_class = PeopleWithActivitiesSerializer
    permission_classes = [AllowAny]

