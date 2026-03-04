"""
Solomon — Development settings.

- DEBUG = True
- SQLite database
- Django Debug Toolbar enabled
- Console email backend
"""

from .base import *  # noqa: F401, F403

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
# Database — SQLite for easy local dev
# =============================================================================
# Uses DATABASE_URL from .env, defaults to SQLite (set in base.py)

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
