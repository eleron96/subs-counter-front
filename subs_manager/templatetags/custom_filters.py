# subs_manager/templatetags/custom_filters.py

from django import template
import json

register = template.Library()

@register.filter
def jsonify_dates(value):
    """Преобразуем список дат в формат JSON."""
    return json.dumps(value)

@register.filter
def jsonify_followers(value):
    """Преобразуем список чисел (подписчиков) в формат JSON."""
    return json.dumps(value)
