from django.utils.translation import gettext as _

from netbox.plugins.navigation import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link="plugins:solomon_test_plugin:solomon_test_status",
        link_text=_("Test Status"),
    ),
)
