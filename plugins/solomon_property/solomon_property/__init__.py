from importlib.metadata import metadata

from netbox.plugins import PluginConfig

_meta = metadata("solomon-property")


class SolomonPropertyConfig(PluginConfig):
    name = "solomon_property"
    verbose_name = "Solomon Property"
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "property"
    min_version = "4.0.0"

    default_settings = {}


config = SolomonPropertyConfig
