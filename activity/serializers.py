from rest_framework import serializers
from .models import Website, Activity, People, Tag

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'name', 'site_id', 'tracking_code', 'domain', 'created_at']
        read_only_fields = ['site_id', 'tracking_code']

class ActivitySmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'activity_type', 'page_title', 'occured_at','page_url','form_data']

class PeopleWithActivitiesSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()
    class Meta:
        model = People
        fields = [
            'id', 'name', 'email', 'phone', 'last_activity', 
            'stage', 'source', 'source_url', 'created_at',
            'activities'
        ]
    def get_activities(self, obj):
        activities = Activity.objects.filter(people=obj).order_by('-occured_at')[:2]
        return ActivitySmallSerializer(activities, many=True).data

class PeopleSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = People
        fields = [
            'id', 'name', 'email', 'phone', 'last_activity', 
            'stage', 'source', 'source_url', 'created_at',
            'is_online'
        ]

class PeopleFromVisitorIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = People
        fields = ['id', 'name']

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
