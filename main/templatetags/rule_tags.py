from django import template

register = template.Library()

from ..models import Rule


@register.simple_tag()
def rules_of_class(class_name):
    rules = Rule.objects.filter(cluster_class=class_name)
    return rules
