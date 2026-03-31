from netbox.plugins import PluginConfig


class SolomonThemeConfig(PluginConfig):
    name = "solomon_theme"
    verbose_name = "Solomon Theme"
    version = "0.1.0"
    author = "Solomon Dev"
    description = "Hardcoded dark Material Design theme for Solomon / NetBox"
    base_url = "solomon-theme"
    min_version = "4.0.0"

    default_settings = {}


config = SolomonThemeConfig
