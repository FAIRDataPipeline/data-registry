from django.conf import settings

if settings.REMOTE:
    REMOTE_REGISTRY = settings.REMOTE
else:
    REMOTE_REGISTRY = False
