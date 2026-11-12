"""
Django settings for hostel_project project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-tvkois13r*$)5!i#odwztg!c3o9n)504fzh5@b0wlgta^w3192'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom apps
    'accounts.apps.AccountsConfig',
    'hostels.apps.HostelsConfig',
    'applications.apps.ApplicationsConfig',
    'allocations.apps.AllocationsConfig',
    'fees.apps.FeesConfig',
    'complaints.apps.ComplaintsConfig',
    'notifications.apps.NotificationsConfig',
    'reports.apps.ReportsConfig',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must come directly after SecurityMiddleware so it can serve
    # compressed, cached static files for both Django dev server and production.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hostel_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notifications_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'hostel_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

# Directory where collectstatic gathers all static files for production serving.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# STATICFILES_DIRS lists extra locations Django's finders search (dev only).
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise: serve compressed + fingerprinted static files in production.
# CompressedManifestStaticFilesStorage adds content hashes to filenames
# (cache-busting) and pre-compresses assets with gzip/brotli.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Allow WhiteNoise to use Django's finders in DEBUG mode so collectstatic
# is not required during local development.
WHITENOISE_USE_FINDERS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_redirect'
LOGOUT_REDIRECT_URL = 'login'

# Email backend: Console email backend for notifications
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'hostel-admin@college.edu'
