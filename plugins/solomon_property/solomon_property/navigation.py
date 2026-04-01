"""Solomon Property - Navigation menu items."""

from django.utils.translation import gettext_lazy as _

from netbox.plugins.navigation import PluginMenu, PluginMenuButton, PluginMenuItem


property_menu = PluginMenu(
    label=_("Property"),
    groups=(
        (
            _("Buildings & Flats"),
            (
                PluginMenuItem(
                    link="plugins:solomon_property:building_list",
                    link_text=_("Buildings"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:building_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:flat_list",
                    link_text=_("Flats"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:flat_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
            ),
        ),
        (
            _("Ownership"),
            (
                PluginMenuItem(
                    link="plugins:solomon_property:propertyowner_list",
                    link_text=_("Owners"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:propertyowner_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:flatowner_list",
                    link_text=_("Flat Ownerships"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:flatowner_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
            ),
        ),
        (
            _("Tenants & Persons"),
            (
                PluginMenuItem(
                    link="plugins:solomon_property:person_list",
                    link_text=_("Persons"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:person_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:propertytenant_list",
                    link_text=_("Tenants"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:propertytenant_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
            ),
        ),
        (
            _("CUZK Import"),
            (
                PluginMenuItem(
                    link="plugins:solomon_property:cuzk-import-search",
                    link_text=_("Import Building from CUZK"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:cuzk-import-search",
                            title=_("Import"),
                            icon_class="mdi mdi-cloud-download",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:owners-import",
                    link_text=_("Import Owners from Text"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:owners-import",
                            title=_("Import"),
                            icon_class="mdi mdi-file-import",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:flat-area-calculation",
                    link_text=_("Calculate Flat Areas"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:flat-area-calculation",
                            title=_("Calculate"),
                            icon_class="mdi mdi-calculator-variant",
                        ),
                    ),
                ),
            ),
        ),
        (
            _("Contacts"),
            (
                PluginMenuItem(
                    link="plugins:solomon_property:contacts-import",
                    link_text=_("Import Contacts (Google CSV)"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:contacts-import",
                            title=_("Import"),
                            icon_class="mdi mdi-file-upload",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:contacts-export",
                    link_text=_("Export Contacts (Google CSV)"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:contacts-export",
                            title=_("Export"),
                            icon_class="mdi mdi-file-download",
                        ),
                    ),
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-home-city",
)

menu = property_menu
