from django import template
import base64

register = template.Library()

@register.filter(name='b64encode')
def b64encode_filter(value):
    return base64.b64encode(value).decode('utf-8')
