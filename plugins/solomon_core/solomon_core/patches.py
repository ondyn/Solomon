"""
Solomon Core — monkey-patches applied at plugin ready().

Patches the `get_menus()` function in NetBox navigation to filter out
disabled modules based on solomon_core configuration.
"""
from functools import cache

from netbox.navigation import menu as menu_module

from .module_map import get_disabled_menu_labels

# Save reference to the original function.
# functools.cache wraps the function; __wrapped__ gives us the original.
_original_get_menus = getattr(menu_module.get_menus, "__wrapped__", menu_module.get_menus)


@cache
def _patched_get_menus():
    """
    Replacement for netbox.navigation.menu.get_menus() that filters out
    menus whose labels are in the disabled set.
    """
    disabled_labels = get_disabled_menu_labels()
    original_menus = _original_get_menus()
    return [m for m in original_menus if str(m.label) not in disabled_labels]


# Apply the patch
menu_module.get_menus = _patched_get_menus
