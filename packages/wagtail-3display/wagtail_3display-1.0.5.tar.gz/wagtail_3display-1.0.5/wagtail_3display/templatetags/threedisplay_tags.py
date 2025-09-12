from django.template import Library
import uuid

register = Library()

@register.simple_tag(name='threedisplay_id')
def threedisplay_id():
    return uuid.uuid4()
