from netbox.plugins import PluginConfig


class SolomonTestPluginConfig(PluginConfig):
    name = "solomon_test_plugin"
    verbose_name = "Solomon Test Plugin"
    version = "0.1.0"
    author = "Solomon Dev"
    description = "A test plugin to verify the Solomon plugin development workflow."
    base_url = "solomon-test"
    min_version = "4.0.0"

    # Default configuration (overridable in PLUGINS_CONFIG)
    default_settings = {
        "greeting": "Hello from Solomon!",
    }


config = SolomonTestPluginConfig
