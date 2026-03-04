"""
Solomon — Production settings.

- DEBUG = False
- PostgreSQL database (from DATABASE_URL)
- Strict security settings
- WhiteNoise for static files
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug
# =============================================================================
DEBUG = False

# =============================================================================
# Security
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =============================================================================
# Database — PostgreSQL from DATABASE_URL (required in prod)
# =============================================================================
# Uses DATABASE_URL from .env / environment variable (set in base.py)

# =============================================================================
# Email — real SMTP in production
# =============================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")  # noqa: F405
EMAIL_PORT = env("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)  # noqa: F405
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@bdsalounova.cz")  # noqa: F405
