from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += (
    'django_extensions',
    'debug_toolbar',
)

INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

for logger in LOGGING['loggers'].values():
    logger['handlers'] = ['console']
    logger['level'] = 'DEBUG'

AUTH_PASSWORD_VALIDATORS = []

try:
    from .local import *
except ImportError:
    pass
