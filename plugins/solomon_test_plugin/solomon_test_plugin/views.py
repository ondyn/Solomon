from django.http import JsonResponse
from django.views.generic import View

from netbox.plugins import get_plugin_config


class SolomonTestView(View):
    """Simple view to verify the plugin is loaded and working."""

    def get(self, request):
        greeting = get_plugin_config("solomon_test_plugin", "greeting")
        return JsonResponse(
            {
                "status": "ok",
                "plugin": "solomon_test_plugin",
                "version": "0.1.0",
                "greeting": greeting,
            }
        )
