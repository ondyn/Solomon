from importlib.metadata import metadata

from netbox.plugins import PluginConfig
from django.utils.translation import gettext_lazy as _

_meta = metadata("solomon-core")


class SolomonCoreConfig(PluginConfig):
    name = "solomon_core"
    verbose_name = _("Solomon Core")
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "solomon-core"
    min_version = "4.0.0"

    # Middleware to block disabled module URLs
    middleware = [
        "solomon_core.middleware.DisabledModulesMiddleware",
    ]

    default_settings = {
        # Set to True to re-enable a module
        "enable_organization": False,
        "enable_racks": False,
        "enable_devices": False,
        "enable_connections": False,
        "enable_wireless": False,
        "enable_ipam": False,
        "enable_vpn": False,
        "enable_virtualization": False,
        "enable_circuits": False,
        "enable_power": False,
        "enable_provisioning": False,
    }

    def ready(self):
        super().ready()
        from . import patches  # noqa: F401 - apply monkey-patches on startup


config = SolomonCoreConfig
