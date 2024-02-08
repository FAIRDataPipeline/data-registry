from .base_settings import *

with open('/home/ubuntu/secret_key.txt') as f:
    SECRET_KEY = f.read().strip()

ALLOWED_HOSTS = ['data.fairdatapipeline.org', '127.0.0.1', 'localhost']

REMOTE = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'scrc',
        'USER': 'scrc',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': None,
        'OPTIONS': {
            'binary': True,
        }
    }
}

BUCKETS = {
    'default': {
       'url' : '#',
       'bucket_name:': '#',
       'access_key': '#',
       'secret_key': '#',
       'duration': '600'
    }
}
CACHE_DURATION = 300