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
                    link="plugins:solomon_property:buildingobject_list",
                    link_text=_("Building Objects"),
                    permissions=["solomon_property.view_buildingobject"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:buildingobject_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_buildingobject"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:building_list",
                    link_text=_("Buildings"),
                    permissions=["solomon_property.view_building"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:building_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_building"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:flat_list",
                    link_text=_("Flats"),
                    permissions=["solomon_property.view_flat"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:flat_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_flat"],
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
                    permissions=["solomon_property.view_propertyowner"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:propertyowner_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_propertyowner"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:flatowner_list",
                    link_text=_("Flat Ownerships"),
                    permissions=["solomon_property.view_flatowner"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:flatowner_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_flatowner"],
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
                    permissions=["solomon_property.view_person"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:person_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_person"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:propertytenant_list",
                    link_text=_("Tenants"),
                    permissions=["solomon_property.view_propertytenant"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:propertytenant_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_property.add_propertytenant"],
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
                    permissions=["solomon_property.import_cuzk_data"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:cuzk-import-search",
                            title=_("Import"),
                            icon_class="mdi mdi-cloud-download",
                            permissions=["solomon_property.import_cuzk_data"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:owners-import",
                    link_text=_("Import Owners from Text"),
                    permissions=["solomon_property.import_owner_data"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:owners-import",
                            title=_("Import"),
                            icon_class="mdi mdi-file-import",
                            permissions=["solomon_property.import_owner_data"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:flat-area-calculation",
                    link_text=_("Calculate Flat Areas"),
                    permissions=["solomon_property.calculate_flat_area"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:flat-area-calculation",
                            title=_("Calculate"),
                            icon_class="mdi mdi-calculator-variant",
                            permissions=["solomon_property.calculate_flat_area"],
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
                    permissions=["solomon_property.import_contacts_data"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:contacts-import",
                            title=_("Import"),
                            icon_class="mdi mdi-file-upload",
                            permissions=["solomon_property.import_contacts_data"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_property:contacts-export",
                    link_text=_("Export Contacts (Google CSV)"),
                    permissions=["solomon_property.export_contacts_data"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_property:contacts-export",
                            title=_("Export"),
                            icon_class="mdi mdi-file-download",
                            permissions=["solomon_property.export_contacts_data"],
                        ),
                    ),
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-home-city",
)

menu = property_menu
