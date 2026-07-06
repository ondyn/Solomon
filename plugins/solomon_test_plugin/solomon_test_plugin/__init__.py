from importlib.metadata import metadata

from netbox.plugins import PluginConfig
from django.utils.translation import gettext_lazy as _

_meta = metadata("solomon-test-plugin")


class SolomonTestPluginConfig(PluginConfig):
    name = "solomon_test_plugin"
    verbose_name = _("Solomon Test Plugin")
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "solomon-test"
    min_version = "4.0.0"

    # Default configuration (overridable in PLUGINS_CONFIG)
    default_settings = {
        "greeting": "Hello from Solomon!",
    }


config = SolomonTestPluginConfig
