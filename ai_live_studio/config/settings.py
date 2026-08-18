"""
Django settings for AI Live Studio.
Production-ready configuration for Render.com deployment.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from a local .env file if present (no-op on
# Render, which injects env vars directly).
load_dotenv(BASE_DIR / '.env')

# -------------------------------------------------------------------------
# Core / Security
# -------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-CHANGE-THIS-KEY-IN-PRODUCTION-abc123xyz789'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
extra_hosts = os.environ.get('ALLOWED_HOSTS', '')
if extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in extra_hosts.split(',') if h.strip()]

CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
extra_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if extra_origins:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in extra_origins.split(',') if o.strip()]

# -------------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Local apps
    'core',
    'accounts',
    'dashboard',
    'studio',
    'analytics',
    'payments',
    'notifications',
    'api',
    'broadcast',
    'admin_dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ActivityLogMiddleware',
    'core.middleware.PaymentGateMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# -------------------------------------------------------------------------
# Database
# -------------------------------------------------------------------------
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# -------------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'landing'

# -------------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------------
# Static & Media files
# -------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------------------------------------------------
# Security hardening (production)
# -------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # needed so JS can read the token for fetch() calls
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# -------------------------------------------------------------------------
# Email configuration (used for other mail features such as broadcasts)
# -------------------------------------------------------------------------
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = os.environ.get(
        'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'
    )
else:
    EMAIL_BACKEND = os.environ.get(
        'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'
    )

EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@ailivestudio.com')

# -------------------------------------------------------------------------
# Telegram support contact
# -------------------------------------------------------------------------
# Simple redirect flow: the form opens the user's Telegram DM directly.
# Prefer a public Telegram username if possible, e.g. supportcreoveya.
TELEGRAM_SUPPORT_USERNAME = os.environ.get('TELEGRAM_SUPPORT_USERNAME', '').strip()
TELEGRAM_SUPPORT_URL = os.environ.get('TELEGRAM_SUPPORT_URL', '')
if not TELEGRAM_SUPPORT_URL and TELEGRAM_SUPPORT_USERNAME:
    TELEGRAM_SUPPORT_URL = f'https://t.me/{TELEGRAM_SUPPORT_USERNAME.lstrip("@")}'
if not TELEGRAM_SUPPORT_URL:
    TELEGRAM_SUPPORT_URL = 'https://t.me/'

# Keep this for compatibility, but the contact form now redirects to Telegram.
CONTACT_FORM_RECIPIENT = os.environ.get('CONTACT_FORM_RECIPIENT', DEFAULT_FROM_EMAIL)

# Direct-download link for the Windows desktop app, shown on the landing
# page. GitHub's "latest" release pattern always points to the newest
# release's matching-named asset, so you never need to update this URL
# after tagging a new version — just replace YOUR_USERNAME/YOUR_REPO once.
WINDOWS_APP_DOWNLOAD_URL = os.environ.get(
    'WINDOWS_APP_DOWNLOAD_URL',
    'https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/CreoveyaSetup.exe'
)

# Referral program: how many bonus credits a user earns when someone they
# referred gets their FIRST payment approved.
REFERRAL_BONUS_CREDITS = int(os.environ.get('REFERRAL_BONUS_CREDITS', '50'))

# -------------------------------------------------------------------------
# Messages framework -> Bootstrap alert classes
# -------------------------------------------------------------------------
from django.contrib.messages import constants as messages_constants  # noqa: E402

MESSAGE_TAGS = {
    messages_constants.DEBUG: 'secondary',
    messages_constants.INFO: 'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR: 'danger',
}

# -------------------------------------------------------------------------
# App-specific settings
# -------------------------------------------------------------------------
SITE_NAME = 'AI Live Studio'

# ---------------------------------------------------------------------------
# Decart real-time face-swap API
# ---------------------------------------------------------------------------
# Your Decart account's PERMANENT key — set this in your .env (local) or
# Render environment variables (production). Never hardcode it here, and
# never put it in any frontend JS file. Decart's realtime model connects
# directly from the browser via WebRTC, so the permanent key never leaves
# your server — instead, api/stream.py exchanges it for a short-lived
# client token (10 min TTL) per session, and only that token reaches the
# browser. See platform.decart.ai for your key / usage dashboard.
DECART_API_KEY = os.environ.get('DECART_API_KEY', '')

# Which Decart realtime model to use. "lucy-2.5" is their flagship
# real-time character-transform model as of this build.
DECART_MODEL = os.environ.get('DECART_MODEL', 'lucy-2.5')

# How long to wait on the token-exchange call before giving up (this is
# just for fetching the short-lived token — not per video frame, since
# frames flow over the WebRTC connection directly, not through Django).
FACE_SWAP_TIMEOUT_SECONDS = float(os.environ.get('FACE_SWAP_TIMEOUT_SECONDS', '5'))

# Auto-detected: True once DECART_API_KEY is set. You can still force it
# on/off explicitly with AI_ENGINE_CONNECTED if you ever need to, but
# normally you won't need to touch this at all.
AI_ENGINE_CONNECTED = os.environ.get(
    'AI_ENGINE_CONNECTED',
    'True' if DECART_API_KEY else 'False'
) == 'True'

# ---------------------------------------------------------------------------
# SendGrid (admin bulk email broadcasts)
# ---------------------------------------------------------------------------
# THIS IS WHERE YOUR SENDGRID API KEY GOES. Set it in your .env (local) or
# Render environment variables (production) — never hardcode it here.
# Get your key from https://app.sendgrid.com/settings/api_keys (needs
# "Mail Send" permission).
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')

# The verified sender address broadcasts are sent from. SendGrid requires
# this to be a verified sender/domain in your SendGrid account, or sends
# will fail. Falls back to DEFAULT_FROM_EMAIL if unset.
BROADCAST_FROM_EMAIL = os.environ.get('BROADCAST_FROM_EMAIL', DEFAULT_FROM_EMAIL)

# How many recipients go in a single SendGrid API call. Each recipient
# gets their own private personalization block (no one sees anyone else's
# address). Kept well under SendGrid's per-request limits.
BROADCAST_BATCH_SIZE = int(os.environ.get('BROADCAST_BATCH_SIZE', '500'))

# Safety net for local testing: when True, SendGrid validates and accepts
# the request but does NOT actually deliver any email (their documented
# sandbox mode). Defaults to on whenever DEBUG is on, so you can't
# accidentally blast real test users while developing. Set explicitly via
# env var to override either way.
BROADCAST_SANDBOX_MODE = os.environ.get(
    'BROADCAST_SANDBOX_MODE', 'True' if DEBUG else 'False'
) == 'True'

PLAN_CREDITS = {
    'free': 50,
    'starter': 500,
    'professional': 2500,
    'enterprise': 10000,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
