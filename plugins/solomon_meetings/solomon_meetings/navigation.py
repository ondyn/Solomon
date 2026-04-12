from django.utils.translation import gettext_lazy as _

from netbox.plugins.navigation import PluginMenu, PluginMenuButton, PluginMenuItem


menu = PluginMenu(
    label=_("Meetings"),
    groups=(
        (
            _("Meetings"),
            (
                PluginMenuItem(
                    link="plugins:solomon_meetings:meeting_list",
                    link_text=_("Meetings"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meeting_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:meetingtype_list",
                    link_text=_("Meeting types"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetingtype_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:agendaitem_list",
                    link_text=_("Agenda items"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:agendaitem_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
            ),
        ),
        (
            _("Voting"),
            (
                PluginMenuItem(
                    link="plugins:solomon_meetings:meetingattendance_list",
                    link_text=_("Attendance"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetingattendance_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:vote_list",
                    link_text=_("Votes"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:vote_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:voteweightstyle_list",
                    link_text=_("Vote weight styles"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:voteweightstyle_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
            ),
        ),
        (
            _("Records"),
            (
                PluginMenuItem(
                    link="plugins:solomon_meetings:meetingminutes_list",
                    link_text=_("Minutes"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetingminutes_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:meetinginvitation_list",
                    link_text=_("Invitations"),
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetinginvitation_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                        ),
                    ),
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-account-group",
)
