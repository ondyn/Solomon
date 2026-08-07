import django_tables2 as tables
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from functools import reduce
from math import gcd
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable

from solomon_property.models import FlatOwner

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


def _lcm(a, b):
    return abs(a * b) // gcd(a, b) if a and b else max(a, b)


def _build_current_share_stats():
    ownerships = FlatOwner.objects.filter(effective_to__isnull=True).select_related(
        "flat"
    )

    flat_to_ownerships = defaultdict(list)
    for ownership in ownerships:
        flat_to_ownerships[ownership.flat_id].append(ownership)

    holder_totals = defaultdict(lambda: Fraction(0, 1))

    for flat_id, flat_ownerships in flat_to_ownerships.items():
        if len(flat_ownerships) == 1:
            ownership = flat_ownerships[0]
            if not ownership.share_denominator:
                continue

            holder_key = ("owner", ownership.owner_id)
            share_fraction = Fraction(
                ownership.share_numerator, ownership.share_denominator
            )
        else:
            flat = flat_ownerships[0].flat
            holder_key = ("flat", flat_id)
            if flat.cuzk_share_numerator and flat.cuzk_share_denominator:
                share_fraction = Fraction(
                    flat.cuzk_share_numerator, flat.cuzk_share_denominator
                )
            else:
                share_fraction = sum(
                    (
                        Fraction(o.share_numerator, o.share_denominator)
                        for o in flat_ownerships
                    ),
                    Fraction(0, 1),
                )

        holder_totals[holder_key] += share_fraction

    share_counts = defaultdict(int)
    denominators = []

    for share_fraction in holder_totals.values():
        share_counts[share_fraction] += 1
        denominators.append(share_fraction.denominator)

    common_denominator = reduce(_lcm, denominators, 1) if denominators else 1
    return share_counts, common_denominator


class MeetingTypeTable(NetBoxTable):
    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = MeetingType
        fields = (
            "pk",
            "name",
            "quorum_type",
            "default_quorum_threshold",
            "attendance_threshold_50",
            "attendance_threshold_two_thirds",
            "actions",
        )
        default_columns = (
            "name",
            "quorum_type",
            "default_quorum_threshold",
            "attendance_threshold_50",
            "attendance_threshold_two_thirds",
            "actions",
        )


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
        default_columns = (
            "agenda_item",
            "attendance",
            "vote",
            "vote_weight",
            "actions",
        )


class VoteWeightStyleTable(NetBoxTable):
    label = tables.Column(linkify=True)
    is_current = tables.BooleanColumn(verbose_name=_("Current"))
    color = tables.Column(verbose_name=_("Color"))
    share_count = tables.Column(
        verbose_name=_("Count"), orderable=False, empty_values=()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._share_counts, self._common_share_denominator = (
            _build_current_share_stats()
        )

    def render_weight_value(self, record):
        if record.voting_method != "BY_SHARE":
            return record.weight_fraction

        numerator, denominator = record.weight_fraction_pair
        share_fraction = Fraction(numerator, denominator)
        common_denominator = share_fraction.denominator
        if self is not None:
            common_denominator = (
                self._common_share_denominator or share_fraction.denominator
            )
        if common_denominator % share_fraction.denominator:
            common_denominator = _lcm(common_denominator, share_fraction.denominator)

        common_numerator = (
            share_fraction.numerator * common_denominator // share_fraction.denominator
        )
        return f"{common_numerator}/{common_denominator}"

    def render_color(self, value):
        color = (value or "").strip() or "#000000"
        return format_html(
            '<span style="display:inline-block;width:1rem;height:1rem;border:1px solid #6c757d;'
            'border-radius:0.2rem;background-color:{};vertical-align:middle;"></span>',
            color,
        )

    def render_share_count(self, value, record):
        if record.voting_method == "BY_UNITS":
            if Decimal(str(record.weight_value)) == Decimal("1"):
                count = (
                    FlatOwner.objects.filter(effective_to__isnull=True)
                    .values("owner_id")
                    .distinct()
                    .count()
                )
            else:
                count = 0
        else:
            numerator, denominator = record.weight_fraction_pair
            count = self._share_counts.get(Fraction(numerator, denominator), 0)
        return count

    class Meta(NetBoxTable.Meta):
        model = VoteWeightStyle
        fields = (
            "pk",
            "voting_method",
            "weight_value",
            "label",
            "color",
            "is_current",
            "share_count",
            "actions",
        )
        default_columns = (
            "voting_method",
            "weight_value",
            "label",
            "color",
            "is_current",
            "share_count",
            "actions",
        )


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
        fields = (
            "pk",
            "meeting",
            "owner",
            "sent_at",
            "delivery_method",
            "confirmed",
            "actions",
        )
        default_columns = (
            "meeting",
            "owner",
            "sent_at",
            "delivery_method",
            "confirmed",
            "actions",
        )


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
    owner_snapshot = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = MeetingAttendanceEvent
        fields = (
            "pk",
            "owner_snapshot",
            "event_type",
            "event_time",
            "source",
            "note",
            "actions",
        )
        default_columns = (
            "owner_snapshot",
            "event_type",
            "event_time",
            "source",
            "note",
            "actions",
        )


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
