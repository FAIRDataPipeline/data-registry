
import configparser
import os
import sys

from django.conf import settings as conf_settings

CONFIG = configparser.ConfigParser()
if os.path.exists(conf_settings.CONFIG_LOCATION):
    CONFIG.read(conf_settings.CONFIG_LOCATION)
    REMOTE_REGISTRY = True
else:
    REMOTE_REGISTRY = False