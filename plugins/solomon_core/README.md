# Solomon Core Plugin

Disables default NetBox modules that are not relevant for Solomon facility management:

- Organization (Sites, Regions, etc.)
- Racks
- Devices
- Connections
- Wireless
- IPAM
- VPN
- Virtualization
- Circuits
- Power
- Provisioning

## What it does

1. **UI**: Removes disabled module menus from the navigation sidebar
2. **API**: Returns 404 for API endpoints of disabled modules
3. **Configuration**: Controlled via `PLUGINS_CONFIG` — you can re-enable any module

## Configuration

In `docker/configuration/plugins.py`:

```python
PLUGINS_CONFIG = {
    "solomon_core": {
        # Set any to True to re-enable it
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
}
```
