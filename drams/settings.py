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
        # lifetime of a presigned address, in seconds (SigV4 allows up to 7 days): an
        # upload address must outlive the slowest upload of the largest file, since the
        # store refuses the PUT once it has expired, and a 10 GB file from a home
        # connection takes hours
        "duration": "86400",
    }
}
CACHE_DURATION = 0
