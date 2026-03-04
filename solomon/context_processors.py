"""
Solomon — Custom template context processors.
"""

from django.conf import settings


def app_version(request):
    """Add APP_VERSION to template context."""
    return {
        "APP_VERSION": getattr(settings, "APP_VERSION", "0.0.0"),
    }
