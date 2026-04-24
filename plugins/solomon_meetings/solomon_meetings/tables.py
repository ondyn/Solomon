import django_tables2 as tables
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns

from .models import (
    AgendaVoteBallot,
    AgendaVoteSession,
    AgendaItem,
    Meeting,
    MeetingAttendance,
    MeetingAttendanceEvent,
    MeetingInvitation,
    MeetingMinutes,
    MeetingOwnerSnapshot,
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
    color = tables.Column(verbose_name=_("Color"))

    def render_color(self, value):
        color = (value or "").strip() or "#000000"
        return format_html(
            '<span style="display:inline-block;width:1rem;height:1rem;border:1px solid #6c757d;'
            'border-radius:0.2rem;background-color:{};vertical-align:middle;margin-right:0.4rem;"></span>{}',
            color,
            color,
        )

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


class MeetingOwnerSnapshotTable(NetBoxTable):
    owner_display_name = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = MeetingOwnerSnapshot
        fields = (
            "pk",
            "meeting",
            "owner_display_name",
            "representation",
            "share_value",
            "ballot_label",
            "is_currently_present",
        )
        default_columns = (
            "meeting",
            "owner_display_name",
            "representation",
            "share_value",
            "ballot_label",
            "is_currently_present",
        )


class MeetingAttendanceEventTable(NetBoxTable):
    snapshot = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = MeetingAttendanceEvent
        fields = ("pk", "snapshot", "event_type", "event_time", "source", "note", "actions")
        default_columns = ("snapshot", "event_type", "event_time", "source", "note", "actions")


class AgendaVoteSessionTable(NetBoxTable):
    agenda_item = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = AgendaVoteSession
        fields = (
            "pk",
            "agenda_item",
            "started_at",
            "completed_at",
            "present_weight",
            "quorum_met",
            "result",
        )
        default_columns = (
            "agenda_item",
            "started_at",
            "completed_at",
            "present_weight",
            "quorum_met",
            "result",
        )


class AgendaVoteBallotTable(NetBoxTable):
    session = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = AgendaVoteBallot
        fields = (
            "pk",
            "session",
            "label",
            "share_value",
            "issued_count",
            "for_count",
            "against_count",
            "abstain_count",
        )
        default_columns = (
            "session",
            "label",
            "share_value",
            "issued_count",
            "for_count",
            "against_count",
            "abstain_count",
        )
