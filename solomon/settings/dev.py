"""
Solomon — Development settings.

- DEBUG = True
- Django Debug Toolbar enabled
- Console email backend
- Database from DATABASE_URL env var (PostgreSQL in Docker, SQLite fallback)
"""

from .base import *  # noqa: F403

# =============================================================================
# Debug
# =============================================================================
DEBUG = True

# =============================================================================
# Debug Toolbar
# =============================================================================
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# =============================================================================
# Database — uses DATABASE_URL from environment (set by docker-compose.yml)
# Falls back to SQLite if DATABASE_URL is not set (see base.py)
# =============================================================================

# =============================================================================
# Email — print to console
# =============================================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# Static files — no compression in dev
# =============================================================================
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# =============================================================================
# Logging — more verbose in dev
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}
