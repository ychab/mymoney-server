import os

from django.utils.log import DEFAULT_LOGGING

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'mymoney.core',
    'mymoney.api.users',
    'mymoney.api.bankaccounts',
    'mymoney.api.banktransactiontags',
    'mymoney.api.banktransactions',
    'mymoney.api.banktransactionschedulers',
    'mymoney.api.banktransactionanalytics',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'mymoney.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,  # For back-office only
        'OPTIONS': {
            'context_processors': [
                # Except i18n, keep others just for admin back-office.
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'mymoney.wsgi.application'

LOGGING = DEFAULT_LOGGING.copy()
LOGGING['loggers']['mymoney.errors'] = {'handlers': ['mail_admins']}

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)
USE_I18N = True
USE_L10N = True
TIME_ZONE = 'UTC'
USE_TZ = True

FORMAT_MODULE_PATH = [
    'mymoney.formats',
]

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'PAGE_SIZE': 25,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

MYMONEY = {
    'ADMIN_BASE_URL': 'admin',
    'USE_L10N_DIST': False,  # See l10n.dist
    'BULK_MAX': 50,
}
