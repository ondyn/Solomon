from django.utils.translation import gettext_lazy as _
from netbox.plugins.navigation import PluginMenu, PluginMenuButton, PluginMenuItem


def item(link, text, model):
    return PluginMenuItem(
        link=f"plugins:solomon_facilities:{link}_list",
        link_text=_(text),
        permissions=[f"solomon_facilities.view_{model}"],
        buttons=(
            PluginMenuButton(
                link=f"plugins:solomon_facilities:{link}_add",
                title=_("Add"),
                icon_class="mdi mdi-plus-thick",
                permissions=[f"solomon_facilities.add_{model}"],
            ),
        ),
    )


menu = PluginMenu(
    label=_("Facilities"),
    groups=(
        (
            _("Schematics"),
            (
                item("level", "Building Levels", "buildinglevel"),
                item("floorplan", "Floor Plans", "floorplan"),
                item("space", "Spaces", "space"),
                item("spaceflatassignment", "Flat Assignments", "spaceflatassignment"),
                item("spaceusage", "Rentals and Occupancy", "spaceusage"),
            ),
        ),
        (
            _("Access"),
            (
                item("door", "Doors", "door"),
                item("lockcylinder", "Lock Cylinders", "lockcylinder"),
                item("keyprofile", "Key Profiles", "keyprofile"),
                item("keycopy", "Physical Keys", "keycopy"),
                item("keyissue", "Key Issues", "keyissue"),
            ),
        ),
        (
            _("Building Systems"),
            (
                item("technicalsystem", "Technical Systems", "technicalsystem"),
                item("technicalasset", "Technical Assets", "technicalasset"),
                item(
                    "technicalconnection", "System Connections", "technicalconnection"
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-floor-plan",
)
