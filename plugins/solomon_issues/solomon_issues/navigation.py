from django.utils.translation import gettext_lazy as _
from netbox.plugins.navigation import PluginMenu, PluginMenuButton, PluginMenuItem


def item(link, text, model, buttons=True):
    return PluginMenuItem(
        link=f"plugins:solomon_issues:{link}_list",
        link_text=_(text),
        permissions=[f"solomon_issues.view_{model}"],
        buttons=(
            (
                PluginMenuButton(
                    link=f"plugins:solomon_issues:{link}_add",
                    title=_("Add"),
                    icon_class="mdi mdi-plus-thick",
                    permissions=[f"solomon_issues.add_{model}"],
                ),
            )
            if buttons
            else ()
        ),
    )


menu = PluginMenu(
    label=_("Issues"),
    groups=(
        (
            _("Reporting"),
            (
                item("issue", "Issues", "issue"),
                item("assettag", "QR Asset Tags", "assettag"),
                PluginMenuItem(
                    link="plugins:solomon_issues:assettag_labels",
                    link_text=_("Print QR Labels"),
                    permissions=["solomon_issues.print_assettag"],
                ),
            ),
        ),
        (
            _("Configuration"),
            (item("issuecategory", "Issue Categories", "issuecategory"),),
        ),
    ),
    icon_class="mdi mdi-qrcode-scan",
)
