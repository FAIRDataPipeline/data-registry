from .base_settings import *  # NOSONAR: a settings module takes every setting of the one it extends
import os

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "scrc",
        "USER": "scrc",
        "PASSWORD": "password",
        "HOST": "127.0.0.1",
        "PORT": os.environ.get("FAIR_TEST_POSTGRES_PORT", "5432"),
    }
}
