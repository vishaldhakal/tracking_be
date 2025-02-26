import django_filters
from .models import People
from django.db import models

class PeopleFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter')
    stage = django_filters.ChoiceFilter(choices=People.STAGE_CHOICES)
    tags = django_filters.CharFilter(field_name='tags__name')
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(email__icontains=value) |
            models.Q(phone__icontains=value)
        )
    
    class Meta:
        model = People
        fields = ['stage', 'tags', 'search'] 