from django import template

register = template.Library()

@register.filter
def para(value):
    """10000 → 10.000"""
    try:
        value = int(round(float(value)))
        return f"{value:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
