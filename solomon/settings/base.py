"""
Solomon — Base settings (shared across all environments).

Environment-specific settings are in dev.py, prod.py, test.py.
Environment variables are loaded via django-environ from .env file.
"""

import os
from pathlib import Path

import environ

# =============================================================================
# Paths
# =============================================================================
# BASE_DIR = project root (where manage.py lives)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# Environment
# =============================================================================
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    LANGUAGE_CODE=(str, "cs"),
    TIME_ZONE=(str, "Europe/Prague"),
    APP_VERSION=(str, "0.1.0"),
)

# Read .env file if it exists
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# =============================================================================
# Core Django
# =============================================================================
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# =============================================================================
# Application version
# =============================================================================
APP_VERSION = env("APP_VERSION")

# =============================================================================
# Installed Apps
# =============================================================================
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "auditlog",
    "safedelete",
    "django_htmx",
]

LOCAL_APPS = [
    "core",
    "accounts",
    "buildings",
    "flats",
    "owners",
    "tenants",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# Middleware
# =============================================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "solomon.urls"

# =============================================================================
# Templates
# =============================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "solomon.context_processors.app_version",
            ],
        },
    },
]

WSGI_APPLICATION = "solomon.wsgi.application"

# =============================================================================
# Database — default is SQLite, overridden per environment
# =============================================================================
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Authentication
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# =============================================================================
# Messages — map Django message tags to Bootstrap CSS classes
# =============================================================================
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

# =============================================================================
# Internationalization / Localization
# =============================================================================
LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("cs", "Čeština"),
    ("en", "English"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Czech date/time formats
DATE_FORMAT = "d.m.Y"
DATETIME_FORMAT = "d.m.Y H:i"
SHORT_DATE_FORMAT = "d.m.Y"

# =============================================================================
# Static files
# =============================================================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# =============================================================================
# Media files
# =============================================================================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# Email — default to console (overridden in prod)
# =============================================================================
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# =============================================================================
# Audit log (django-auditlog)
# =============================================================================
AUDITLOG_INCLUDE_ALL_MODELS = True

# =============================================================================
# Logging
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
