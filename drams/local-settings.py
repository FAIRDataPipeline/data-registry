from .base_settings import *
import os

MIDDLEWARE += [
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
ALLOWED_HOSTS.extend(filter(None, os.environ.get("FAIR_ALLOWED_HOSTS", "").split(",")))
DOMAIN_URL = "http://127.0.0.1:8000/"

DEBUG = True
CONFIG_LOCATION = "example_config.ini"
SOCIAL_AUTH_GITHUB_KEY = "a1b2c3d4"
SOCIAL_AUTH_GITHUB_SECRET = "e5f6g7h8i9"
AUTH_METHOD = "GitHub"
