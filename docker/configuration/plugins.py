####
## Solomon - NetBox Plugins Configuration
##
## This file is mounted into the NetBox container at /etc/netbox/config/plugins.py
##
## Local plugins:  develop in ./plugins/, auto-installed in editable mode at startup
## PyPI plugins:   add to plugin-requirements.txt, rebuild image
##
## See: https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins
####

# List of enabled plugins (must be installed in the container image)
PLUGINS = [
    "solomon_core",
    "solomon_test_plugin",
    "solomon_theme",
    "solomon_property",
    "solomon_meetings",
    # "netbox_bgp",
    # "netbox_topology_views",
    # "netbox_documents",
]

# Plugin-specific configuration
PLUGINS_CONFIG = {
    "solomon_core": {
        # All disabled by default — set to True to re-enable
        "enable_organization": False,
        "enable_racks": False,
        "enable_devices": False,
        "enable_connections": False,
        "enable_wireless": False,
        "enable_ipam": False,
        "enable_vpn": False,
        "enable_virtualization": False,
        "enable_circuits": False,
        "enable_power": False,
        "enable_provisioning": False,
    },
    "solomon_test_plugin": {
        "greeting": "Hello from Solomon!",
    },
    "solomon_theme": {},
    "solomon_property": {},
    "solomon_meetings": {},
    # "netbox_bgp": {
    #     "top_level_menu": True,
    # },
    # "netbox_topology_views": {
    #     "preselected_device_roles": ["Router", "Switch"],
    # },
}
