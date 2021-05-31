import django_filters
from .models import Rule

class RuleFilter(django_filters.FilterSet):
    class Meta:
        model = Rule
        fields = '__all__'