from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Website, Activity, People, Tag

@admin.register(Website)
class WebsiteAdmin(ModelAdmin):
    list_display = ['get_name', 'domain', 'user', 'created_at']
    search_fields = ['domain', 'name', 'site_id']
    readonly_fields = ['site_id', 'tracking_code']
    list_filter = ['created_at', 'user']

    def get_name(self, obj):
        if not obj:
            return "Deleted Website"
        return obj.name or obj.domain
    get_name.short_description = 'Name'

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()

@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    list_display = ['activity_type', 'website', 'get_visitor', 'page_title', 'occured_at']
    list_filter = ['activity_type', 'website', 'occured_at']
    search_fields = ['people__name', 'people__email', 'page_title', 'visitor_id']
    date_hierarchy = 'occured_at'

    def get_visitor(self, obj):
        return obj.people.name if obj.people else f"Anonymous ({obj.visitor_id})"
    get_visitor.short_description = 'Visitor'

@admin.register(People)
class PeopleAdmin(ModelAdmin):
    list_display = ['name', 'email', 'phone', 'stage', 'last_activity']
    list_filter = ['stage', 'created_at']
    search_fields = ['name', 'email', 'phone', 'visitor_id']
    filter_horizontal = ['tags']
    readonly_fields = ['visitor_id', 'last_activity']

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

