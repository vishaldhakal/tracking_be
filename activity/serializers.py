from rest_framework import serializers
from .models import Website, Activity, People, Tag, Chat, ChatMessage

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'name', 'site_id', 'tracking_code', 'domain', 'created_at']
        read_only_fields = ['site_id', 'tracking_code']

class PeopleSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = People
        fields = [
            'id', 'name', 'email', 'phone', 'last_activity', 
            'stage', 'source', 'source_url', 'created_at',
            'is_online'
        ]

class ActivitySerializer(serializers.ModelSerializer):
    website = WebsiteSerializer()
    people = PeopleSerializer()
    
    class Meta:
        model = Activity
        fields = [
            'id',
            'website',
            'people',
            'activity_type',
            'message',
            'page_title',
            'page_url',
            'page_referrer',
            'form_data',
            'metadata',
            'occured_at',
            'visitor_id',
            'user_agent',
            'language',
            'screen_resolution',
            'timezone',
        ]

class TrackingEventSerializer(serializers.Serializer):
    site_id = serializers.CharField()
    event_type = serializers.CharField()
    visitor_id = serializers.CharField(required=False, allow_null=True)
    visitor_email = serializers.EmailField(required=False, allow_null=True)
    page_url = serializers.CharField(required=False, allow_null=True)
    page_title = serializers.CharField(required=False, allow_null=True)
    page_referrer = serializers.CharField(required=False, allow_null=True)
    form_data = serializers.JSONField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_null=True)
    language = serializers.CharField(required=False, allow_null=True)
    screen_resolution = serializers.CharField(required=False, allow_null=True)
    timezone = serializers.CharField(required=False, allow_null=True)

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'chat', 'message', 'is_admin', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    last_heartbeat = serializers.SerializerMethodField()

    def get_last_heartbeat(self, obj):
        last_activity = Activity.objects.filter(
            visitor_id=obj.visitor_id,
            activity_type='Heartbeat'
        ).order_by('-last_heartbeat').first()
        return last_activity.last_heartbeat if last_activity else None

    messages = ChatMessageSerializer(many=True, read_only=True)
    people = PeopleSerializer(read_only=True)
    
    class Meta:
        model = Chat
        fields = '__all__'