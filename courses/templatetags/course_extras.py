from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using its key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key) 