import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from netbox.filtersets import NetBoxModelFilterSet

from .models import (
    AgendaItem,
    AgendaVoteBallot,
    AgendaVoteSession,
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


class MeetingTypeFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))

    def search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)

    class Meta:
        model = MeetingType
        fields = ["name", "quorum_type"]


class MeetingFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))

    def search(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(location__icontains=value))

    class Meta:
        model = Meeting
        fields = ["meeting_type", "status", "phase", "date_time"]


class AgendaItemFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )

    class Meta:
        model = AgendaItem
        fields = ["meeting", "voting_required", "voting_method", "result"]


class MeetingAttendanceFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingAttendance
        fields = ["meeting", "owner", "representation"]


class MeetingOwnerSnapshotFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingOwnerSnapshot
        fields = [
            "meeting",
            "owner",
            "flat_owner",
            "representation",
            "is_currently_present",
        ]


class MeetingAttendanceEventFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingAttendanceEvent
        fields = ["owner_snapshot", "event_type", "event_time", "source"]


class VoteFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Vote
        fields = ["agenda_item", "attendance", "vote"]


class VoteWeightStyleFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = VoteWeightStyle
        fields = ["voting_method", "weight_value", "label", "is_current"]


class AgendaVoteSessionFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = AgendaVoteSession
        fields = ["agenda_item", "started_at", "completed_at", "quorum_met", "result"]


class AgendaVoteBallotFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = AgendaVoteBallot
        fields = ["session", "label", "share_value"]


class MeetingMinutesFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingMinutes
        fields = ["meeting", "cms_published", "approved_by"]


class MeetingInvitationFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingInvitation
        fields = ["meeting", "owner", "delivery_method", "confirmed"]
