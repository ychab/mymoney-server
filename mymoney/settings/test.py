from tempfile import gettempdir

from .base import *

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Boost perf a little
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

STATIC_ROOT = os.path.join(gettempdir(), 'opengst', 'static')
MEDIA_ROOT = os.path.join(gettempdir(), 'opengst', 'media')

try:
    from .local import *
except ImportError:  # pragma: no cover
    pass
