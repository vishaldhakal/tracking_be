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
    ChatMessageSerializer
)
from django.shortcuts import get_object_or_404
import json
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
        visitor_email = serializer.validated_data.get('visitor_email')
        
        # Try to find existing person
        person = None
        if visitor_email:
            person = People.objects.filter(email=visitor_email).first()
            if not person:
                person = People.objects.create(
                    email=visitor_email,
                    name=visitor_email.split('@')[0],
                    visitor_id=visitor_id
                )
                
        # Create activity for both anonymous and identified users
        activity = Activity.objects.create(
            website=website,
            visitor_id=visitor_id,  # Always store visitor_id
            people=person,  # This can be None for anonymous users
            activity_type=serializer.validated_data.get('event_type'),
            page_url=serializer.validated_data.get('page_url'),
            page_title=serializer.validated_data.get('page_title'),
            page_referrer=serializer.validated_data.get('page_referrer'),
            metadata=serializer.validated_data.get('metadata'),
            user_agent=serializer.validated_data.get('user_agent'),
            language=serializer.validated_data.get('language'),
            screen_resolution=serializer.validated_data.get('screen_resolution'),
            timezone=serializer.validated_data.get('timezone'),
            last_heartbeat=timezone.now() if serializer.validated_data.get('event_type') == 'Heartbeat' else None
        )
        
        return Response(ActivitySerializer(activity).data)
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
        
        # Update last message
        chat.update_last_message(message)
        
        # Get the serialized message
        serialized_message = ChatMessageSerializer(chat_message).data
        
        # Send to channel layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat.visitor_id}',
            {
                'type': 'chat_message',
                'message': serialized_message
            }
        )
        
        return Response(serialized_message)
    except Chat.DoesNotExist:
        return Response({"error": "Chat not found"}, status=404)
    except Exception as e:
        print(f"Error sending message: {e}")
        return Response({"error": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    now = timezone.now()
    online_threshold = now - timedelta(minutes=1)
    
    # Count all online visitors (both anonymous and identified)
    online_visitors = Activity.objects.filter(
        last_heartbeat__gte=online_threshold
    ).values('visitor_id').distinct().count()
    
    # Count identified online visitors
    identified_online = Activity.objects.filter(
        last_heartbeat__gte=online_threshold,
        people__isnull=False
    ).values('people').distinct().count()
    
    # Get anonymous online count
    anonymous_online = online_visitors - identified_online
    
    # Get active chats
    active_chats = Chat.objects.filter(status='active')
    
    return Response({
        'totalVisits': Activity.objects.filter(activity_type='Viewed Page').count(),
        'totalPeople': People.objects.count(),
        'onlineVisitors': online_visitors,
        'identifiedOnline': identified_online,
        'anonymousOnline': anonymous_online,
        'activeChats': ChatSerializer(active_chats, many=True).data,
        'recentActivities': ActivitySerializer(
            Activity.objects.select_related('people', 'website')
            .exclude(activity_type='Heartbeat')
            .order_by('-occured_at')[:10], 
            many=True
        ).data
    })

@api_view(['GET'])
def people_list(request):
    now = timezone.now()
    online_threshold = now - timedelta(minutes=1)
    
    people = People.objects.annotate(
        is_online=models.Exists(
            Activity.objects.filter(
                people=models.OuterRef('pk'),
                last_heartbeat__gte=online_threshold
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
    return Response(ActivitySerializer(activities, many=True).data)

@api_view(['GET'])
def chat_messages(request, chat_id):
    try:
        # First verify the chat exists
        chat = get_object_or_404(Chat, id=chat_id)
        
        messages = ChatMessage.objects.filter(
            chat_id=chat_id
        ).order_by('created_at')
        
        serialized_messages = ChatMessageSerializer(messages, many=True).data
        print(f"Fetched {len(serialized_messages)} messages for chat {chat_id}")
        
        return Response({
            'messages': serialized_messages,
            'chat_id': chat_id,
            'total_count': len(serialized_messages)
        })
        
    except Chat.DoesNotExist:
        return Response(
            {'error': f'Chat {chat_id} not found'},
            status=404
        )
    except Exception as e:
        print(f"Error fetching messages for chat {chat_id}: {str(e)}")
        return Response(
            {'error': str(e)},
            status=500
        )

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
