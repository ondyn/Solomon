from importlib.metadata import metadata

from netbox.plugins import PluginConfig
from django.utils.translation import gettext_lazy as _

_meta = metadata("solomon-theme")


class SolomonThemeConfig(PluginConfig):
    name = "solomon_theme"
    verbose_name = _("Solomon Theme")
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "solomon-theme"
    min_version = "4.0.0"

    default_settings = {}


config = SolomonThemeConfig
