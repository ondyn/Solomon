import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns

from .models import (
    AgendaItem,
    Meeting,
    MeetingAttendance,
    MeetingInvitation,
    MeetingMinutes,
    MeetingType,
    Vote,
    VoteWeightStyle,
)


class MeetingTypeTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = MeetingType
        fields = ("pk", "name", "quorum_type", "default_quorum_threshold", "actions")
        default_columns = ("name", "quorum_type", "default_quorum_threshold", "actions")


class MeetingTable(NetBoxTable):
    title = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = Meeting
        fields = (
            "pk",
            "title",
            "meeting_type",
            "date_time",
            "status",
            "phase",
            "quorum_threshold",
            "quorum_achieved",
            "actions",
        )
        default_columns = (
            "title",
            "meeting_type",
            "date_time",
            "status",
            "phase",
            "quorum_threshold",
            "quorum_achieved",
            "actions",
        )


class AgendaItemTable(NetBoxTable):
    title = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = AgendaItem
        fields = (
            "pk",
            "meeting",
            "order",
            "title",
            "presenter",
            "voting_required",
            "voting_method",
            "quorum_threshold",
            "minimum_pass_percentage",
            "result",
            "actions",
        )
        default_columns = (
            "meeting",
            "order",
            "title",
            "presenter",
            "voting_required",
            "voting_method",
            "quorum_threshold",
            "minimum_pass_percentage",
            "result",
            "actions",
        )


class MeetingAttendanceTable(NetBoxTable):
    owner = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = MeetingAttendance
        fields = (
            "pk",
            "meeting",
            "owner",
            "flat_owner",
            "representation",
            "arrived_at",
            "left_at",
            "actions",
        )
        default_columns = (
            "meeting",
            "owner",
            "flat_owner",
            "representation",
            "arrived_at",
            "left_at",
            "actions",
        )


class VoteTable(NetBoxTable):
    vote_weight = tables.Column(verbose_name=_("Weight"))

    class Meta(NetBoxTable.Meta):
        model = Vote
        fields = ("pk", "agenda_item", "attendance", "vote", "vote_weight", "actions")
        default_columns = ("agenda_item", "attendance", "vote", "vote_weight", "actions")


class VoteWeightStyleTable(NetBoxTable):
    label = tables.Column(linkify=True)
    color = columns.ColorColumn()

    class Meta(NetBoxTable.Meta):
        model = VoteWeightStyle
        fields = ("pk", "voting_method", "weight_value", "label", "color", "actions")
        default_columns = ("voting_method", "weight_value", "label", "color", "actions")


class MeetingMinutesTable(NetBoxTable):
    meeting = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = MeetingMinutes
        fields = (
            "pk",
            "meeting",
            "approved_by",
            "approved_at",
            "cms_published",
            "cms_published_at",
            "actions",
        )
        default_columns = (
            "meeting",
            "approved_by",
            "approved_at",
            "cms_published",
            "cms_published_at",
            "actions",
        )


class MeetingInvitationTable(NetBoxTable):
    owner = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = MeetingInvitation
        fields = ("pk", "meeting", "owner", "sent_at", "delivery_method", "confirmed", "actions")
        default_columns = ("meeting", "owner", "sent_at", "delivery_method", "confirmed", "actions")
