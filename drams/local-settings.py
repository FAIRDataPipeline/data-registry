from .base_settings import *
import os

MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware', ]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
ALLOWED_HOSTS.extend(
    filter(None, os.environ.get("FAIR_ALLOWED_HOSTS", "").split(","))
)