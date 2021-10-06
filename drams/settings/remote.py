from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
with open('/home/ubuntu/secret_key.txt') as f:
    SECRET_KEY = f.read().strip()

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_REFERRER_POLICY = 'origin'

ALLOWED_HOSTS = ['data.scrc.uk', '127.0.0.1', 'localhost']

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
