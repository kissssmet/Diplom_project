# diploma_orders/templatetags/custom_filters.py
from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Возвращает только имя файла из пути"""
    return os.path.basename(value) if value else ''

@register.filter
def filesizeformat(value):
    """Форматирование размера файла"""
    if value is None:
        return "0 bytes"
    
    try:
        bytes_value = int(value)
    except (ValueError, TypeError):
        return "0 bytes"
    
    if bytes_value < 1024:
        return f"{bytes_value} bytes"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"