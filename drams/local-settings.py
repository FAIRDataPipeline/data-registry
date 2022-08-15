from .base_settings import *
import os

MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware', ]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ALLOWED_HOSTS.extend(
    filter(None, os.environ.get("FAIR_ALLOWED_HOSTS", "").split(","))
)