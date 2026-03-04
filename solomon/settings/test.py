"""
Solomon — Test settings.

- Fast password hashing
- In-memory email
- SQLite for speed
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug
# =============================================================================
DEBUG = False

# =============================================================================
# Database — in-memory SQLite for fast tests
# =============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# =============================================================================
# Password hashing — fast hasher for tests
# =============================================================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# =============================================================================
# Email — in-memory backend
# =============================================================================
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# =============================================================================
# Media files — temp directory for tests
# =============================================================================
MEDIA_ROOT = BASE_DIR / "test_media"  # noqa: F405

# =============================================================================
# Static files — no manifest in tests
# =============================================================================
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# =============================================================================
# Logging — suppress noisy logs during tests
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
