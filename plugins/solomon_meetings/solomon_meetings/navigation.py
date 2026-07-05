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
                    permissions=["solomon_meetings.view_meeting"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meeting_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_meeting"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:meetingtype_list",
                    link_text=_("Meeting types"),
                    permissions=["solomon_meetings.view_meetingtype"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetingtype_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_meetingtype"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:agendaitem_list",
                    link_text=_("Agenda items"),
                    permissions=["solomon_meetings.view_agendaitem"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:agendaitem_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_agendaitem"],
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
                    permissions=["solomon_meetings.view_meetingattendance"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetingattendance_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_meetingattendance"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:vote_list",
                    link_text=_("Votes"),
                    permissions=["solomon_meetings.view_vote"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:vote_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_vote"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:voteweightstyle_list",
                    link_text=_("Vote weight styles"),
                    permissions=["solomon_meetings.view_voteweightstyle"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:voteweightstyle_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_voteweightstyle"],
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
                    permissions=["solomon_meetings.view_meetingminutes"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetingminutes_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_meetingminutes"],
                        ),
                    ),
                ),
                PluginMenuItem(
                    link="plugins:solomon_meetings:meetinginvitation_list",
                    link_text=_("Invitations"),
                    permissions=["solomon_meetings.view_meetinginvitation"],
                    buttons=(
                        PluginMenuButton(
                            link="plugins:solomon_meetings:meetinginvitation_add",
                            title=_("Add"),
                            icon_class="mdi mdi-plus-thick",
                            permissions=["solomon_meetings.add_meetinginvitation"],
                        ),
                    ),
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-account-group",
)
