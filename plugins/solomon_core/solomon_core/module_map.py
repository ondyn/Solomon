"""
Solomon Core — mapping of config keys to NetBox menu labels and URL prefixes.

Each entry maps a solomon_core config key to:
  - menu_labels: the navigation Menu.label values to hide
  - url_prefixes: the URL path prefixes to block (both UI and API)
"""

# Config key → (menu labels to hide, URL prefixes to block)
MODULE_MAP = {
    "enable_organization": {
        "menu_labels": ["Organization"],
        "url_prefixes": [
            # Organization includes dcim sites/regions/locations AND tenancy
            # We keep tenancy (contacts, tenants) since Solomon needs them
            # Only block the "Organization" menu, not the underlying URLs
            # because tenancy models are shared with Solomon
        ],
    },
    "enable_racks": {
        "menu_labels": ["Racks"],
        "url_prefixes": [],
    },
    "enable_devices": {
        "menu_labels": ["Devices"],
        "url_prefixes": [],
    },
    "enable_connections": {
        "menu_labels": ["Connections"],
        "url_prefixes": [],
    },
    "enable_wireless": {
        "menu_labels": ["Wireless"],
        "url_prefixes": [
            "/wireless/",
            "/api/wireless/",
        ],
    },
    "enable_ipam": {
        "menu_labels": ["IPAM"],
        "url_prefixes": [
            "/ipam/",
            "/api/ipam/",
        ],
    },
    "enable_vpn": {
        "menu_labels": ["VPN"],
        "url_prefixes": [
            "/vpn/",
            "/api/vpn/",
        ],
    },
    "enable_virtualization": {
        "menu_labels": ["Virtualization"],
        "url_prefixes": [
            "/virtualization/",
            "/api/virtualization/",
        ],
    },
    "enable_circuits": {
        "menu_labels": ["Circuits"],
        "url_prefixes": [
            "/circuits/",
            "/api/circuits/",
        ],
    },
    "enable_power": {
        "menu_labels": ["Power"],
        "url_prefixes": [],
    },
    "enable_provisioning": {
        "menu_labels": ["Provisioning"],
        "url_prefixes": [],
    },
}


def get_disabled_menu_labels():
    """Return set of menu label strings that should be hidden."""
    from django.conf import settings

    plugin_cfg = settings.PLUGINS_CONFIG.get("solomon_core", {})
    labels = set()
    for key, mapping in MODULE_MAP.items():
        if not plugin_cfg.get(key, False):
            labels.update(mapping["menu_labels"])
    return labels


def get_blocked_url_prefixes():
    """Return list of URL path prefixes that should return 404."""
    from django.conf import settings

    plugin_cfg = settings.PLUGINS_CONFIG.get("solomon_core", {})
    prefixes = []
    for key, mapping in MODULE_MAP.items():
        if not plugin_cfg.get(key, False):
            prefixes.extend(mapping["url_prefixes"])
    return prefixes
