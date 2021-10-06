from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'custom_user' and 'data_management' apps
NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=custom_user,data_management',
    '--cover-xml',
]
