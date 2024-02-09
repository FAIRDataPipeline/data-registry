from django.conf import settings

if settings.AUTHORISED_USER_FILE:
    REMOTE_REGISTRY = settings.REMOTE
else:
    REMOTE_REGISTRY = False
