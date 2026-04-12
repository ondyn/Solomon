from importlib.metadata import metadata

from netbox.plugins import PluginConfig

_meta = metadata("solomon-meetings")


class SolomonMeetingsConfig(PluginConfig):
    name = "solomon_meetings"
    verbose_name = "Solomon Meetings"
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "meetings"
    min_version = "4.0.0"

    default_settings = {}


config = SolomonMeetingsConfig
