"""
Django settings for hostel_project project.
Hardened for production deployment according to OWASP & NIST security standards.
"""

from pathlib import Path
import os
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# 1. Environment Loading (.env support)
# -----------------------------------------------------------------------------
env_path = BASE_DIR / '.env'
if env_path.exists():
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception as e:
        pass

# -----------------------------------------------------------------------------
# 2. Core Security & Environment Variables
# -----------------------------------------------------------------------------
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-prod-fallback-key-please-set-env-var-in-dashboard-3o9n504fzh5'
)

allowed_hosts_raw = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost,.onrender.com,.vercel.app,.railway.app')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_raw.split(',') if h.strip()]
# Guarantee cloud domains and local development are always permitted
for default_host in ['.vercel.app', '.onrender.com', '.railway.app', 'localhost', '127.0.0.1']:
    if default_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(default_host)

csrf_trusted_raw = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.onrender.com,https://*.vercel.app,https://*.railway.app')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_trusted_raw.split(',') if o.strip()]
for default_origin in ['https://*.vercel.app', 'https://*.onrender.com', 'https://*.railway.app']:
    if default_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(default_origin)

# -----------------------------------------------------------------------------
# 3. Application Definition
# -----------------------------------------------------------------------------
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
    'mess.apps.MessConfig',
    'maintenance.apps.MaintenanceConfig',

    # Two-Factor Authentication (django-otp)
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must come directly after SecurityMiddleware for static files
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # Content Security Policy and Browser Permissions Policy
    'hostel_project.middleware.SecurityHeadersMiddleware',
    # IP-based rate limiting on sensitive routes & general traffic
    'hostel_project.middleware.RateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
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

# -----------------------------------------------------------------------------
# 4. Database & Connection Pooling (Supabase Postgres & SQLite Support)
# -----------------------------------------------------------------------------
db_url = os.environ.get('DATABASE_URL')
conn_max_age = int(os.environ.get('DB_CONN_MAX_AGE', '600'))

if db_url and (db_url.startswith('postgres://') or db_url.startswith('postgresql://')):
    parsed = urllib.parse.urlparse(db_url)
    
    # Check if host is Supabase
    host_str = parsed.hostname or ''
    is_supabase = 'supabase.co' in host_str or 'supabase.com' in host_str
    
    # Query parameters (e.g. ?sslmode=require)
    query_params = urllib.parse.parse_qs(parsed.query)
    ssl_mode = query_params.get('sslmode', ['require' if is_supabase else 'prefer'])[0]

    # Handle PgBouncer transaction pooler (port 6543)
    db_port = parsed.port or 5432
    effective_conn_max_age = 0 if (is_supabase and db_port == 6543) else conn_max_age

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': urllib.parse.unquote(parsed.username or ''),
            'PASSWORD': urllib.parse.unquote(parsed.password or ''),
            'HOST': host_str,
            'PORT': db_port,
            'CONN_MAX_AGE': effective_conn_max_age,
            'OPTIONS': {
                'sslmode': ssl_mode,
            }
        }
    }
else:
    # On serverless platforms like Vercel or AWS Lambda, the app root is read-only.
    # Fallback to /tmp for local sqlite if writable.
    db_path = Path('/tmp/db.sqlite3') if os.environ.get('VERCEL') else (BASE_DIR / 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
            'CONN_MAX_AGE': conn_max_age,
        }
    }

# -----------------------------------------------------------------------------
# 5. Enterprise Password Validators
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# -----------------------------------------------------------------------------
# 6. Internationalization & Timezones
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# 7. Static & Media Assets
# -----------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise storage: CompressedStaticFilesStorage compresses assets safely without
# requiring staticfiles.json manifest during serverless builds.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_USE_FINDERS = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_redirect'
LOGOUT_REDIRECT_URL = 'login'

# -----------------------------------------------------------------------------
# 8. Email Dispatch Configuration
# -----------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '25'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() in ('true', '1')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'hostel-admin@college.edu')

# -----------------------------------------------------------------------------
# 9. Session & Cookie Hardening
# -----------------------------------------------------------------------------
SESSION_COOKIE_AGE = 1800  # 30 minutes inactivity timeout
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# -----------------------------------------------------------------------------
# 10. Production HTTPS / TLS & Browser Protection Headers
# -----------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'

# Account Security & Failed Attempts Lockout
MAX_FAILED_LOGIN_ATTEMPTS = int(os.environ.get('MAX_FAILED_LOGIN_ATTEMPTS', '5'))
LOGIN_LOCKOUT_MINUTES = int(os.environ.get('LOGIN_LOCKOUT_MINUTES', '15'))

RATE_LIMIT_AUTH = int(os.environ.get('RATE_LIMIT_AUTH', '15'))
RATE_LIMIT_GLOBAL = int(os.environ.get('RATE_LIMIT_GLOBAL', '200'))

# -----------------------------------------------------------------------------
# 11. Structured Logging & Auditing
# -----------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
        },
        'security': {
            'format': '[SECURITY AUDIT] [{asctime}] {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'security',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.security': {
            'handlers': ['security_console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'accounts.security': {
            'handlers': ['security_console'],
            'level': 'INFO',
            'propagate': False,
        },
        'allocations': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'fees': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
