from django.utils.translation import gettext_lazy as _
from netbox.plugins.navigation import PluginMenu, PluginMenuButton, PluginMenuItem


def item(link, text, model):
    return PluginMenuItem(
        link=f"plugins:solomon_facilities:{link}_list",
        link_text=text,
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
                item("level", _("Building Levels"), "buildinglevel"),
                item("floorplan", _("Floor Plans"), "floorplan"),
                item("space", _("Spaces"), "space"),
                item("spaceflatassignment", _("Flat Assignments"), "spaceflatassignment"),
                item("spaceusage", _("Rentals and Occupancy"), "spaceusage"),
            ),
        ),
        (
            _("Access"),
            (
                item("door", _("Doors"), "door"),
                item("lockcylinder", _("Lock Cylinders"), "lockcylinder"),
                item("keyprofile", _("Key Profiles"), "keyprofile"),
                item("keycopy", _("Physical Keys"), "keycopy"),
                item("keyissue", _("Key Issues"), "keyissue"),
            ),
        ),
        (
            _("Building Systems"),
            (
                item("technicalsystem", _("Technical Systems"), "technicalsystem"),
                item("technicalasset", _("Technical Assets"), "technicalasset"),
                item(
                    "technicalconnection", _("System Connections"), "technicalconnection"
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-floor-plan",
)
