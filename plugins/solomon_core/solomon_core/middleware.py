"""
Solomon Core — middleware to block URL routes for disabled modules.

Returns HTTP 404 for any request whose path matches a blocked prefix.
This effectively hides disabled modules from both the UI and API.
"""
from django.http import Http404

from .module_map import get_blocked_url_prefixes


class DisabledModulesMiddleware:
    """
    Django middleware that intercepts requests to disabled NetBox module URLs
    and returns a 404 response.

    Blocked prefixes are determined by solomon_core plugin configuration.
    The prefix list is computed once and cached for the process lifetime.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Compute blocked prefixes once at startup (they don't change at runtime)
        self._blocked_prefixes = tuple(get_blocked_url_prefixes())

    def __call__(self, request):
        if self._blocked_prefixes and request.path.startswith(self._blocked_prefixes):
            raise Http404
        return self.get_response(request)
