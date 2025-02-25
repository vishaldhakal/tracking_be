from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Website, Activity, People, Chat, ChatMessage
from .serializers import (
    WebsiteSerializer, 
    ActivitySerializer, 
    TrackingEventSerializer,
    PeopleSerializer,
    ChatSerializer,
    ActivitySmallSerializer,
    ChatMessageSerializer
)
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import models
from django.http import JsonResponse

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
                        'timezone': serializer.validated_data.get('timezone'),
                        'last_activity': timezone.now(),
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
                timezone=serializer.validated_data.get('timezone')
            )
            
            # Update person's last activity
            person.last_activity = timezone.now()
            person.save(update_fields=['last_activity'])
            
            return Response(ActivitySerializer(activity).data)
            
        # If no person found, just return success without creating activity
        return Response({'status': 'success', 'message': 'Event received but not stored (anonymous user)'})
    
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def start_chat(request):
    visitor_id = request.data.get('visitor_id')
    website_id = request.data.get('website_id')
    message = request.data.get('message')
    
    try:
        website = Website.objects.get(site_id=website_id)
        
        # Try to find existing person
        person = People.objects.filter(visitor_id=visitor_id).first()
        
        # Create new chat or get existing active chat
        chat, created = Chat.objects.get_or_create(
            website=website,
            visitor_id=visitor_id,
            status='active',
            defaults={
                'people': person
            }
        )
        
        if message:
            ChatMessage.objects.create(
                chat=chat,
                message=message,
                is_admin=False
            )
            chat.update_last_message(message)
        
        return Response(ChatSerializer(chat).data)
    except Website.DoesNotExist:
        return Response(
            {"error": "Website not found"}, 
            status=404
        )
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=400
        )

@api_view(['POST'])
def send_message(request):
    chat_id = request.data.get('chat_id')
    message = request.data.get('message')
    is_admin = request.data.get('is_admin', False)
    
    try:
        chat = Chat.objects.get(id=chat_id)
        chat_message = ChatMessage.objects.create(
            chat=chat,
            message=message,
            is_admin=is_admin
        )
        chat.update_last_message(message)
        return Response(ChatMessageSerializer(chat_message).data)
    except Chat.DoesNotExist:
        return Response({"error": "Chat not found"}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    now = timezone.now()
    online_threshold = now - timedelta(minutes=1)
    
    # Only count activities from identified users
    total_visits = Activity.objects.filter(
        activity_type='Viewed Page',
        people__isnull=False
    ).count()
    
    # Count identified online visitors
    online_visitors = Activity.objects.filter(
        occured_at__gte=online_threshold,
        people__isnull=False
    ).values('people').distinct().count()
    
    # Get active chats
    active_chats = Chat.objects.filter(status='active')
    
    return Response({
        'totalVisits': total_visits,
        'totalPeople': People.objects.count(),
        'onlineVisitors': online_visitors,
        'activeChats': ChatSerializer(active_chats, many=True).data,
        'recentActivities': ActivitySerializer(
            Activity.objects.select_related('people', 'website')
            .filter(people__isnull=False)  # Only show activities from identified users
            .order_by('-occured_at')[:10], 
            many=True
        ).data
    })

@api_view(['GET'])
def people_list(request):
    people = People.objects.annotate(
        is_online=models.Exists(
            Activity.objects.filter(
                people=models.OuterRef('pk'),
            )
        )
    ).order_by('-last_activity')
    
    return Response(PeopleSerializer(people, many=True).data)

@api_view(['GET'])
def person_detail(request, pk):
    person = get_object_or_404(People, pk=pk)
    return Response(PeopleSerializer(person).data)

@api_view(['GET'])
def person_activities(request, pk):
    activities = Activity.objects.filter(people_id=pk).order_by('-occured_at')
    return Response(ActivitySmallSerializer(activities, many=True).data)

@api_view(['GET'])
def chat_messages(request, chat_id):
    since = request.GET.get('since', '0')
    try:
        since_dt = datetime.fromtimestamp(float(since))
    except ValueError:
        since_dt = datetime.fromtimestamp(0)

    messages = ChatMessage.objects.filter(
        chat_id=chat_id,
        created_at__gt=since_dt
    ).order_by('created_at')

    return Response(ChatMessageSerializer(messages, many=True).data)

@api_view(['GET'])
def live_visitors(request):
    now = timezone.now()
    online_threshold = now - timedelta(minutes=1)
    
    # Get all online visitors with their latest activity and details
    visitors = Activity.objects.filter(
        last_heartbeat__gte=online_threshold
    ).values('visitor_id').annotate(
        latest_activity=models.Max('occured_at'),
        is_known=models.Exists(
            People.objects.filter(visitor_id=models.OuterRef('visitor_id'))
        ),
        visitor_name=models.Subquery(
            People.objects.filter(
                visitor_id=models.OuterRef('visitor_id')
            ).values('name')[:1]
        ),
        visitor_email=models.Subquery(
            People.objects.filter(
                visitor_id=models.OuterRef('visitor_id')
            ).values('email')[:1]
        ),
        current_page=models.Subquery(
            Activity.objects.filter(
                visitor_id=models.OuterRef('visitor_id'),
                activity_type='Viewed Page'
            ).order_by('-occured_at').values('page_url')[:1]
        ),
        current_page_title=models.Subquery(
            Activity.objects.filter(
                visitor_id=models.OuterRef('visitor_id'),
                activity_type='Viewed Page'
            ).order_by('-occured_at').values('page_title')[:1]
        )
    ).order_by('-latest_activity')

    return Response({
        'visitors': visitors
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_chat(request):
    visitor_id = request.data.get('visitor_id')
    initial_message = request.data.get('message')
    website_id = request.data.get('website_id')
    
    try:
        print(f"Initiating chat for visitor: {visitor_id}")  # Debug log
        
        # Find website by site_id
        website = Website.objects.get(site_id=website_id)
        
        # Find visitor's person record if exists
        person = People.objects.filter(visitor_id=visitor_id).first()
        
        # Create new chat or get existing active chat
        chat, created = Chat.objects.get_or_create(
            website=website,
            visitor_id=visitor_id,
            status='active',
            defaults={
                'people': person
            }
        )
        
        if created and initial_message:
            ChatMessage.objects.create(
                chat=chat,
                message=initial_message,
                is_admin=True
            )
        
        print(f"Chat {'created' if created else 'retrieved'}: {chat.id}")  # Debug log
        return Response(ChatSerializer(chat).data)
        
    except Website.DoesNotExist:
        return Response(
            {"error": "Website not found"}, 
            status=404
        )
    except Exception as e:
        print(f"Error initiating chat: {str(e)}")  # Debug log
        return Response(
            {"error": str(e)}, 
            status=400
        )

@api_view(['GET'])
def visitor_activities(request, visitor_id):
    activities = Activity.objects.filter(
        visitor_id=visitor_id
    ).exclude(
        activity_type='Heartbeat'
    ).select_related(
        'website'
    ).order_by(
        '-occured_at'
    )[:50]  # Limit to last 50 activities
    
    return Response(ActivitySerializer(activities, many=True).data)

@api_view(['GET'])
def visitor_chat(request, visitor_id):
    chat = Chat.objects.filter(visitor_id=visitor_id, status='active').first()
    if not chat:
        return Response(None)
    return Response(ChatSerializer(chat).data)

@api_view(['GET'])
def get_visitor_chat(request, visitor_id):
    try:
        # Get the most recent active chat for the visitor
        chat = Chat.objects.filter(
            visitor_id=visitor_id,
            status='active'
        ).select_related('people').latest('created_at')
        
        return Response(ChatSerializer(chat).data)
    except Chat.DoesNotExist:
        return Response(None, status=200)  # Return null if no chat exists
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=500
        )
