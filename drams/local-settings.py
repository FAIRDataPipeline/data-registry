from .base_settings import *

INSTALLED_APPS += ['import_export', ]

MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware', ]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

IMPORT_EXPORT_USE_TRANSACTIONS = True
