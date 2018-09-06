#####
# All
#####

SECRET_KEY = 'blah-blah-blah'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mymoney',
        'USER': 'mymoney',
        'PASSWORD': 'mymoney',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

LANGUAGE_CODE = 'fr-fr'

############
# Production
############

# ALLOWED_HOSTS = []
# ADMINS = ()

# STATIC_ROOT = ''
# MEDIA_ROOT = ''

# DEFAULT_FROM_EMAIL = ''
# EMAIL_HOST = ''
# EMAIL_PORT = ''
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''

# For Django back-office, enable SSL if needed
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True  # Just in case, should be done by webserver instead
