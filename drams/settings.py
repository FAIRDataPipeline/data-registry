from .base_settings import *

with open("/home/ubuntu/secret_key.txt") as f:
    SECRET_KEY = f.read().strip()

ALLOWED_HOSTS = ["data.fairdatapipeline.org", "127.0.0.1", "localhost"]

DOMAIN_URL = "https://data.fairdatapipeline.org/"

REMOTE = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "scrc",
        "USER": "scrc",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

BUCKETS = {
    "default": {
        "url": "#",
        "bucket_name": "#",
        "access_key": "#",
        "secret_key": "#",
        "duration": "600",
    }
}
CACHE_DURATION = 0
