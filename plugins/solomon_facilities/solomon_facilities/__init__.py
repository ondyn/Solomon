from importlib.metadata import metadata

from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginConfig

_meta = metadata("solomon-facilities")


class SolomonFacilitiesConfig(PluginConfig):
    name = "solomon_facilities"
    verbose_name = _("Solomon Facilities")
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "facilities"
    min_version = "4.0.0"

    default_settings = {}

    def ready(self):
        super().ready()
        from . import views  # noqa: F401


config = SolomonFacilitiesConfig
