import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from netbox.filtersets import NetBoxModelFilterSet

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
        return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))

    class Meta:
        model = AgendaItem
        fields = ["meeting", "voting_required", "voting_method", "result"]


class MeetingAttendanceFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingAttendance
        fields = ["meeting", "owner", "representation"]


class VoteFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Vote
        fields = ["agenda_item", "attendance", "vote"]


class VoteWeightStyleFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = VoteWeightStyle
        fields = ["voting_method", "weight_value", "label"]


class MeetingMinutesFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingMinutes
        fields = ["meeting", "cms_published", "approved_by"]


class MeetingInvitationFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = MeetingInvitation
        fields = ["meeting", "owner", "delivery_method", "confirmed"]
