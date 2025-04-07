from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def is_auth_method(method):
    _auth_method = settings.AUTH_METHOD
    if _auth_method:
        if _auth_method == method:
            return True
    return False
