from .base import *

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

try:
    from .local import *  # isort:skip
except ImportError:
    pass  # NOQA
