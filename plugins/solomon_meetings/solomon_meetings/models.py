from collections import defaultdict
from functools import reduce
from math import lcm
from decimal import Decimal
from fractions import Fraction

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from netbox.models import NetBoxModel
from solomon_property.models import Building, FlatOwner, PropertyOwner


QUORUM_TYPE_BY_UNITS = "BY_UNITS"
QUORUM_TYPE_BY_SHARE = "BY_SHARE"
QUORUM_TYPE_CHOICES = [
    (QUORUM_TYPE_BY_UNITS, _("By units")),
    (QUORUM_TYPE_BY_SHARE, _("By ownership share")),
]

MEETING_STATUS_PLANNED = "PLANNED"
MEETING_STATUS_IN_PROGRESS = "IN_PROGRESS"
MEETING_STATUS_ADJOURNED = "ADJOURNED"
MEETING_STATUS_CLOSED = "CLOSED"
MEETING_STATUS_CHOICES = [
    (MEETING_STATUS_PLANNED, _("Planned")),
    (MEETING_STATUS_IN_PROGRESS, _("In progress")),
    (MEETING_STATUS_ADJOURNED, _("Adjourned")),
    (MEETING_STATUS_CLOSED, _("Closed")),
]

REPRESENTATION_PRESENT = "PRESENT"
REPRESENTATION_PROXY = "PROXY"
REPRESENTATION_ABSENT = "ABSENT"
REPRESENTATION_CHOICES = [
    (REPRESENTATION_PRESENT, _("Present")),
    (REPRESENTATION_PROXY, _("Proxy")),
    (REPRESENTATION_ABSENT, _("Absent")),
]

VOTE_FOR = "FOR"
VOTE_AGAINST = "AGAINST"
VOTE_ABSTAIN = "ABSTAIN"
VOTE_CHOICES = [
    (VOTE_FOR, _("For")),
    (VOTE_AGAINST, _("Against")),
    (VOTE_ABSTAIN, _("Abstain")),
]

AGENDA_RESULT_APPROVED = "APPROVED"
AGENDA_RESULT_REJECTED = "REJECTED"
AGENDA_RESULT_DEFERRED = "DEFERRED"
AGENDA_RESULT_NOT_APPLICABLE = "N/A"
AGENDA_RESULT_CHOICES = [
    (AGENDA_RESULT_APPROVED, _("Approved")),
    (AGENDA_RESULT_REJECTED, _("Rejected")),
    (AGENDA_RESULT_DEFERRED, _("Deferred")),
    (AGENDA_RESULT_NOT_APPLICABLE, _("N/A")),
]

MEETING_PHASE_PLANNING = "PLANNING"
MEETING_PHASE_IN_PROGRESS = "IN_PROGRESS"
MEETING_PHASE_FINISHED = "FINISHED"
MEETING_PHASE_CHOICES = [
    (MEETING_PHASE_PLANNING, _("Planning")),
    (MEETING_PHASE_IN_PROGRESS, _("In progress")),
    (MEETING_PHASE_FINISHED, _("Finished")),
]

ATTENDANCE_EVENT_ARRIVAL = "ARRIVAL"
ATTENDANCE_EVENT_DEPARTURE = "DEPARTURE"
ATTENDANCE_EVENT_CHOICES = [
    (ATTENDANCE_EVENT_ARRIVAL, _("Arrival")),
    (ATTENDANCE_EVENT_DEPARTURE, _("Departure")),
]


def quantize_weight_fraction(numerator, denominator):
    return (Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.000001"))

BALLOT_ROLE_FOR = "FOR"
BALLOT_ROLE_AGAINST = "AGAINST"
BALLOT_ROLE_ABSTAIN = "ABSTAIN"
BALLOT_ROLE_CHOICES = [
    (BALLOT_ROLE_FOR, _("For")),
    (BALLOT_ROLE_AGAINST, _("Against")),
    (BALLOT_ROLE_ABSTAIN, _("Abstain")),
]

INVITATION_DELIVERY_EMAIL = "EMAIL"
INVITATION_DELIVERY_POST = "POST"
INVITATION_DELIVERY_PERSONAL = "PERSONAL"
INVITATION_DELIVERY_CHOICES = [
    (INVITATION_DELIVERY_EMAIL, _("Email")),
    (INVITATION_DELIVERY_POST, _("Post")),
    (INVITATION_DELIVERY_PERSONAL, _("Personal delivery")),
]


class MeetingType(NetBoxModel):
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Name"))
    quorum_type = models.CharField(
        max_length=20,
        choices=QUORUM_TYPE_CHOICES,
        default=QUORUM_TYPE_BY_SHARE,
        verbose_name=_("Quorum type"),
    )
    default_quorum_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.5000"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        verbose_name=_("Default quorum threshold"),
        help_text=_("Decimal value from 0 to 1, e.g. 0.5 for 50%."),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Meeting type")
        verbose_name_plural = _("Meeting types")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:meetingtype", kwargs={"pk": self.pk})


class Meeting(NetBoxModel):
    meeting_type = models.ForeignKey(
        MeetingType,
        on_delete=models.PROTECT,
        related_name="meetings",
        verbose_name=_("Meeting type"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    buildings = models.ManyToManyField(
        Building,
        related_name="meetings",
        verbose_name=_("Buildings"),
        help_text=_("Buildings summoned to this meeting."),
    )
    date_time = models.DateTimeField(verbose_name=_("Date and time"))
    location = models.CharField(max_length=255, blank=True, verbose_name=_("Location"))
    status = models.CharField(
        max_length=20,
        choices=MEETING_STATUS_CHOICES,
        default=MEETING_STATUS_PLANNED,
        verbose_name=_("Status"),
    )
    quorum_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.5000"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        verbose_name=_("Quorum threshold"),
        help_text=_("Decimal value from 0 to 1, e.g. 0.5 for 50%."),
    )
    quorum_achieved = models.BooleanField(default=False, verbose_name=_("Quorum achieved"))
    quorum_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Quorum updated at"),
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_meetings",
        verbose_name=_("Moderator"),
    )
    note = models.TextField(blank=True, verbose_name=_("Note"))
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Started at"))
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Ended at"))
    phase = models.CharField(
        max_length=20,
        choices=MEETING_PHASE_CHOICES,
        default=MEETING_PHASE_PLANNING,
        verbose_name=_("Workflow phase"),
    )
    invitation_published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Invitation published at"),
    )
    invitation_pdf_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Invitation PDF generated at"),
    )
    owner_snapshot_taken_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Owner snapshot taken at"),
    )

    class Meta:
        ordering = ["-date_time", "title"]
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")

    def __str__(self):
        return f"{self.title} ({self.date_time:%Y-%m-%d %H:%M})"

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:meeting", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()
        if self.status == MEETING_STATUS_CLOSED and not self.quorum_achieved:
            raise ValidationError({"status": _("Meeting cannot be closed before quorum is achieved.")})
        if self.started_at and self.ended_at and self.ended_at <= self.started_at:
            raise ValidationError({"ended_at": _("Meeting end must be after meeting start.")})
        if self.phase == MEETING_PHASE_PLANNING and self.started_at:
            raise ValidationError({"phase": _("Planning meetings cannot already be started.")})
        if self.phase == MEETING_PHASE_FINISHED and not self.ended_at:
            raise ValidationError({"phase": _("Finished meetings must have an end time.")})

    def _active_attendance(self, at_time=None):
        if self.owner_snapshots.exists():
            queryset = self.owner_snapshots.all()
            if at_time is None:
                return queryset.filter(is_currently_present=True)
            return [snapshot for snapshot in queryset if snapshot.is_present_at(at_time)]

        queryset = self.attendances.filter(
            representation__in=[REPRESENTATION_PRESENT, REPRESENTATION_PROXY]
        )
        if at_time is None:
            return queryset
        return queryset.filter(
            Q(arrived_at__isnull=True) | Q(arrived_at__lte=at_time),
            Q(left_at__isnull=True) | Q(left_at__gt=at_time),
        )

    def _total_weight(self, quorum_type):
        buildings = self.buildings.all()
        active_ownerships = FlatOwner.objects.filter(
            flat__building__in=buildings,
            effective_to__isnull=True,
        ).select_related("flat")
        if quorum_type == QUORUM_TYPE_BY_UNITS:
            return Decimal(str(active_ownerships.values("flat_id").distinct().count()))

        # Match meeting voting-unit semantics:
        # sole-owner flat -> owner share, co-owned flat -> one flat-level share.
        flat_to_ownerships = defaultdict(list)
        for ownership in active_ownerships:
            flat_to_ownerships[ownership.flat_id].append(ownership)

        total_fraction = Fraction(0, 1)
        for flat_ownerships in flat_to_ownerships.values():
            if len(flat_ownerships) == 1:
                ownership = flat_ownerships[0]
                if not ownership.share_denominator:
                    continue
                total_fraction += Fraction(ownership.share_numerator, ownership.share_denominator)
                continue

            flat = flat_ownerships[0].flat
            if flat.cuzk_share_numerator and flat.cuzk_share_denominator:
                total_fraction += Fraction(flat.cuzk_share_numerator, flat.cuzk_share_denominator)
            else:
                total_fraction += sum(
                    (Fraction(o.share_numerator, o.share_denominator) for o in flat_ownerships),
                    Fraction(0, 1),
                )

        return Decimal(total_fraction.numerator) / Decimal(total_fraction.denominator)

    def _present_weight(self, quorum_type, at_time=None):
        attendance = self._active_attendance(at_time=at_time)
        if quorum_type == QUORUM_TYPE_BY_UNITS:
            if hasattr(attendance, "values"):
                return Decimal(str(attendance.values("flat_owner__flat_id").distinct().count()))
            return Decimal(str(sum(snapshot.unit_count for snapshot in attendance)))

        # If attendance is built from owner snapshots, each row already carries
        # the effective voting-unit share (including co-ownership normalization).
        if hasattr(attendance, "model") and attendance.model is MeetingOwnerSnapshot:
            total_fraction = Fraction(0, 1)
            for snapshot in attendance:
                if snapshot.share_denominator:
                    total_fraction += Fraction(snapshot.share_numerator, snapshot.share_denominator)
            return Decimal(total_fraction.numerator) / Decimal(total_fraction.denominator)

        total = Decimal("0")
        if hasattr(attendance, "select_related"):
            for record in attendance.select_related("flat_owner"):
                total += Decimal(record.flat_owner.share_numerator) / Decimal(record.flat_owner.share_denominator)
            return total

        for snapshot in attendance:
            total += snapshot.share_value
        return total

    def calculate_quorum_ratio(self, at_time=None):
        quorum_type = self.meeting_type.quorum_type
        total = self._total_weight(quorum_type)
        if total <= 0:
            return Decimal("0")
        present = self._present_weight(quorum_type, at_time=at_time)
        return present / total

    def refresh_quorum(self, at_time=None):
        ratio = self.calculate_quorum_ratio(at_time=at_time)
        self.quorum_achieved = ratio >= self.quorum_threshold
        self.quorum_updated_at = timezone.now()
        self.save(update_fields=["quorum_achieved", "quorum_updated_at", "last_updated"])
        return ratio

    def get_present_weight(self, voting_method):
        return self._present_weight(voting_method)

    def start_meeting(self, started_at=None):
        if self.phase != MEETING_PHASE_PLANNING:
            raise ValidationError({"phase": _("Only planned meetings can be started.")})

        started_at = started_at or timezone.now()
        self.started_at = started_at
        self.phase = MEETING_PHASE_IN_PROGRESS
        self.status = MEETING_STATUS_IN_PROGRESS
        self.snapshot_owners(started_at=started_at)
        self.refresh_quorum(at_time=started_at)
        self.save(
            update_fields=[
                "started_at",
                "phase",
                "status",
                "quorum_achieved",
                "quorum_updated_at",
                "last_updated",
            ]
        )

    def finish_meeting(self, ended_at=None):
        ended_at = ended_at or timezone.now()
        if self.phase != MEETING_PHASE_IN_PROGRESS:
            raise ValidationError({"phase": _("Only meetings in progress can be finished.")})
        if not self.quorum_achieved:
            raise ValidationError({"quorum_achieved": _("Meeting cannot be finished without quorum.")})

        self.ended_at = ended_at
        self.phase = MEETING_PHASE_FINISHED
        self.status = MEETING_STATUS_CLOSED
        self.save(update_fields=["ended_at", "phase", "status", "last_updated"])

    def snapshot_owners(self, started_at=None, refresh_existing=False):
        started_at = started_at or timezone.now()
        if self.owner_snapshots.exists() and not refresh_existing:
            return

        active_ownerships = (
            FlatOwner.objects.filter(
                flat__building__in=self.buildings.all(),
                effective_to__isnull=True,
            )
            .select_related("owner", "flat")
            .order_by("flat__building__house_number", "flat__flat_number", "owner__display_name")
        )

        # Group by flat: co-owners of the same flat become ONE voting unit
        flat_to_ownerships = defaultdict(list)
        for ownership in active_ownerships:
            flat_to_ownerships[ownership.flat_id].append(ownership)

        processed_snapshot_ids = set()

        for flat_id, ownerships in flat_to_ownerships.items():
            flat = ownerships[0].flat
            if len(ownerships) == 1:
                # Sole owner: snapshot uses their individual FlatOwner share
                ownership = ownerships[0]
                share_num = ownership.share_numerator
                share_den = ownership.share_denominator
                primary = ownership
                owner_display_name = str(ownership.owner)
            else:
                # Co-owners: one snapshot for the flat using the flat's CUZK share
                primary = ownerships[0]  # already sorted by display_name
                owner_display_name = " & ".join(str(o.owner) for o in ownerships)
                if flat.cuzk_share_numerator and flat.cuzk_share_denominator:
                    share_num = flat.cuzk_share_numerator
                    share_den = flat.cuzk_share_denominator
                else:
                    total = sum(
                        (Fraction(o.share_numerator, o.share_denominator) for o in ownerships),
                        Fraction(0, 1),
                    )
                    share_num = total.numerator
                    share_den = total.denominator

            share_value = quantize_weight_fraction(share_num, share_den)
            style = VoteWeightStyle.objects.filter(
                voting_method=QUORUM_TYPE_BY_SHARE,
                weight_value=share_value,
            ).first()
            snapshot_defaults = {
                "owner": primary.owner,
                "owner_display_name": owner_display_name,
                "flat_label": str(flat),
                "representation": REPRESENTATION_ABSENT,
                "share_numerator": share_num,
                "share_denominator": share_den,
                "share_value": share_value,
                "unit_count": len(ownerships),
                "ballot_label": style.label if style else "",
                "ballot_color": style.color if style else "",
                "snapshot_taken_at": started_at,
            }

            snapshot = None
            if refresh_existing:
                snapshot = self.owner_snapshots.filter(flat_owner__flat_id=flat_id).first()

            if snapshot is None:
                snapshot, _ = MeetingOwnerSnapshot.objects.get_or_create(
                    meeting=self,
                    flat_owner=primary,
                    defaults=snapshot_defaults,
                )
            elif refresh_existing:
                snapshot.flat_owner = primary
                snapshot.owner = primary.owner
                snapshot.owner_display_name = owner_display_name
                snapshot.flat_label = str(flat)
                snapshot.share_numerator = share_num
                snapshot.share_denominator = share_den
                snapshot.share_value = share_value
                snapshot.unit_count = len(ownerships)
                snapshot.ballot_label = style.label if style else ""
                snapshot.ballot_color = style.color if style else ""
                snapshot.save(
                    update_fields=[
                        "flat_owner",
                        "owner",
                        "owner_display_name",
                        "flat_label",
                        "share_numerator",
                        "share_denominator",
                        "share_value",
                        "unit_count",
                        "ballot_label",
                        "ballot_color",
                        "last_updated",
                    ]
                )

            processed_snapshot_ids.add(snapshot.pk)

        if refresh_existing:
            self.owner_snapshots.exclude(pk__in=processed_snapshot_ids).delete()

        self.owner_snapshot_taken_at = started_at
        self.save(update_fields=["owner_snapshot_taken_at", "last_updated"])

    def get_ballot_type_summary(self):
        active_ownerships = list(
            FlatOwner.objects.filter(
                flat__building__in=self.buildings.all(),
                effective_to__isnull=True,
            ).select_related("flat", "owner")
        )

        flat_to_ownerships = defaultdict(list)
        for ownership in active_ownerships:
            flat_to_ownerships[ownership.flat_id].append(ownership)

        holder_totals = defaultdict(lambda: Fraction(0, 1))
        for flat_id, ownerships in flat_to_ownerships.items():
            if len(ownerships) == 1:
                ownership = ownerships[0]
                if not ownership.share_denominator:
                    continue
                holder_key = ("owner", ownership.owner_id)
                share_fraction = Fraction(ownership.share_numerator, ownership.share_denominator)
            else:
                flat = ownerships[0].flat
                holder_key = ("flat", flat_id)
                if flat.cuzk_share_numerator and flat.cuzk_share_denominator:
                    share_fraction = Fraction(flat.cuzk_share_numerator, flat.cuzk_share_denominator)
                else:
                    share_fraction = sum(
                        (Fraction(o.share_numerator, o.share_denominator) for o in ownerships),
                        Fraction(0, 1),
                    )

            holder_totals[holder_key] += share_fraction

        denominators = [fraction.denominator for fraction in holder_totals.values()]
        common_denom = reduce(lcm, denominators, 1) if denominators else 1

        reference_time = timezone.now()
        holder_presence = defaultdict(bool)
        for snapshot in self.owner_snapshots.select_related("flat_owner"):
            if not snapshot.is_present_at(reference_time):
                continue

            if snapshot.unit_count > 1 and snapshot.flat_owner_id:
                holder_key = ("flat", snapshot.flat_owner.flat_id)
            else:
                holder_key = ("owner", snapshot.owner_id)

            holder_presence[holder_key] = True

        summaries = {}
        for holder_key, share_fraction in holder_totals.items():
            share_value = quantize_weight_fraction(share_fraction.numerator, share_fraction.denominator)
            style = VoteWeightStyle.objects.filter(
                voting_method=QUORUM_TYPE_BY_SHARE,
                weight_value=share_value,
            ).first()
            label = style.label if style else ""
            color = style.color if style else ""

            key = f"{share_value}:{label}:{color}"
            if key not in summaries:
                scaled_num = share_fraction.numerator * common_denom // share_fraction.denominator
                summaries[key] = {
                    "label": label,
                    "color": color,
                    "share_value": share_value,
                    "share_fraction": f"{scaled_num}/{common_denom}",
                    "owner_count": 0,
                    "issued_count": 0,
                }

            summaries[key]["owner_count"] += 1
            if holder_presence.get(holder_key, False):
                summaries[key]["issued_count"] += 1

        return list(summaries.values())


class AgendaItem(NetBoxModel):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="agenda_items",
        verbose_name=_("Meeting"),
    )
    order = models.PositiveIntegerField(default=1, verbose_name=_("Order"))
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    presenter = models.CharField(max_length=255, blank=True, verbose_name=_("Presenter"))
    voting_required = models.BooleanField(default=True, verbose_name=_("Voting required"))
    voting_method = models.CharField(
        max_length=20,
        choices=QUORUM_TYPE_CHOICES,
        default=QUORUM_TYPE_BY_SHARE,
        verbose_name=_("Voting method"),
    )
    minimum_pass_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.5000"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        verbose_name=_("Minimum pass percentage"),
    )
    quorum_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.5000"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        verbose_name=_("Quorum threshold"),
        help_text=_("Required meeting quorum before this agenda item can be adopted."),
    )
    result = models.CharField(
        max_length=20,
        choices=AGENDA_RESULT_CHOICES,
        default=AGENDA_RESULT_NOT_APPLICABLE,
        verbose_name=_("Result"),
    )

    class Meta:
        ordering = ["meeting", "order", "title"]
        unique_together = [("meeting", "order")]
        verbose_name = _("Agenda item")
        verbose_name_plural = _("Agenda items")

    def __str__(self):
        return f"{self.meeting.title} - {self.order}. {self.title}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:agendaitem", kwargs={"pk": self.pk})

    def tally_votes(self):
        if self.vote_sessions.exists():
            latest_session = self.vote_sessions.order_by("-created").first()
            return latest_session.totals_by_role()

        totals = {
            VOTE_FOR: Decimal("0"),
            VOTE_AGAINST: Decimal("0"),
            VOTE_ABSTAIN: Decimal("0"),
        }
        for vote in self.votes.all():
            totals[vote.vote] += vote.vote_weight
        return totals

    def resolve_result(self, negative_form=False):
        if not self.voting_required:
            self.result = AGENDA_RESULT_NOT_APPLICABLE
            self.save(update_fields=["result", "last_updated"])
            return self.result

        if self.meeting.calculate_quorum_ratio() < self.quorum_threshold:
            self.result = AGENDA_RESULT_REJECTED
            self.save(update_fields=["result", "last_updated"])
            return self.result

        totals = self.tally_votes()
        present_weight = self.meeting.get_present_weight(self.voting_method)

        if negative_form:
            totals[VOTE_FOR] = max(Decimal("0"), present_weight - totals[VOTE_AGAINST] - totals[VOTE_ABSTAIN])

        if present_weight <= 0:
            self.result = AGENDA_RESULT_REJECTED
        else:
            ratio = totals[VOTE_FOR] / present_weight
            self.result = (
                AGENDA_RESULT_APPROVED
                if ratio >= self.minimum_pass_percentage
                else AGENDA_RESULT_REJECTED
            )

        self.save(update_fields=["result", "last_updated"])
        return self.result


class MeetingAttendance(NetBoxModel):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Meeting"),
    )
    owner = models.ForeignKey(
        PropertyOwner,
        on_delete=models.PROTECT,
        related_name="meeting_attendances",
        verbose_name=_("Owner"),
    )
    flat_owner = models.ForeignKey(
        FlatOwner,
        on_delete=models.PROTECT,
        related_name="meeting_attendances",
        verbose_name=_("Flat ownership"),
    )
    representation = models.CharField(
        max_length=10,
        choices=REPRESENTATION_CHOICES,
        default=REPRESENTATION_PRESENT,
        verbose_name=_("Representation"),
    )
    proxy_name = models.CharField(max_length=255, blank=True, verbose_name=_("Proxy name"))
    arrived_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Arrived at"))
    left_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Left at"))

    class Meta:
        ordering = ["meeting", "owner"]
        unique_together = [("meeting", "flat_owner")]
        verbose_name = _("Meeting attendance")
        verbose_name_plural = _("Meeting attendances")

    def __str__(self):
        return f"{self.owner} @ {self.meeting}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:meetingattendance", kwargs={"pk": self.pk})

    @property
    def vote_weight_by_units(self):
        return Decimal("1")

    @property
    def vote_weight_by_share(self):
        return Decimal(self.flat_owner.share_numerator) / Decimal(self.flat_owner.share_denominator)

    def clean(self):
        super().clean()
        if self.flat_owner.owner_id != self.owner_id:
            raise ValidationError({"flat_owner": _("Flat ownership must belong to the selected owner.")})
        if self.representation == REPRESENTATION_PROXY and not self.proxy_name:
            raise ValidationError({"proxy_name": _("Proxy name is required for proxy representation.")})
        if self.left_at and self.arrived_at and self.left_at <= self.arrived_at:
            raise ValidationError({"left_at": _("Left at must be after arrived at.")})

    def sync_snapshot(self):
        snapshot = self.meeting.owner_snapshots.filter(flat_owner=self.flat_owner).first()
        if not snapshot:
            return

        snapshot.representation = self.representation
        snapshot.proxy_name = self.proxy_name
        snapshot.first_arrived_at = self.arrived_at
        snapshot.last_left_at = self.left_at
        snapshot.is_currently_present = (
            self.representation in [REPRESENTATION_PRESENT, REPRESENTATION_PROXY]
            and self.left_at is None
        )
        snapshot.save(
            update_fields=[
                "representation",
                "proxy_name",
                "first_arrived_at",
                "last_left_at",
                "is_currently_present",
                "last_updated",
            ]
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_snapshot()


class VoteWeightStyle(NetBoxModel):
    voting_method = models.CharField(
        max_length=20,
        choices=QUORUM_TYPE_CHOICES,
        default=QUORUM_TYPE_BY_SHARE,
        verbose_name=_("Voting method"),
    )
    weight_value = models.DecimalField(max_digits=12, decimal_places=6, verbose_name=_("Weight value"))
    weight_numerator = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Weight numerator"),
    )
    weight_denominator = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Weight denominator"),
    )
    label = models.CharField(max_length=16, verbose_name=_("Label"), help_text=_("Display marker, e.g. 1, A, B."))
    color = models.CharField(
        max_length=7,
        default="#1976D2",
        verbose_name=_("Color"),
        help_text=_("Hex color, e.g. #1976D2."),
    )

    class Meta:
        ordering = ["voting_method", "weight_value"]
        unique_together = [("voting_method", "weight_value"), ("voting_method", "label")]
        verbose_name = _("Vote weight style")
        verbose_name_plural = _("Vote weight styles")

    @property
    def weight_fraction_pair(self):
        if self.weight_numerator and self.weight_denominator:
            return self.weight_numerator, self.weight_denominator

        frac = Fraction(self.weight_value).limit_denominator(200000)
        return frac.numerator, frac.denominator

    @property
    def weight_fraction(self):
        numerator, denominator = self.weight_fraction_pair
        return f"{numerator}/{denominator}"

    def __str__(self):
        return f"{self.voting_method}: {self.weight_fraction} ({self.label})"

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:voteweightstyle", kwargs={"pk": self.pk})


class MeetingOwnerSnapshot(NetBoxModel):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="owner_snapshots",
        verbose_name=_("Meeting"),
    )
    owner = models.ForeignKey(
        PropertyOwner,
        on_delete=models.PROTECT,
        related_name="meeting_owner_snapshots",
        verbose_name=_("Owner"),
    )
    flat_owner = models.ForeignKey(
        FlatOwner,
        on_delete=models.PROTECT,
        related_name="meeting_owner_snapshots",
        verbose_name=_("Flat ownership"),
    )
    owner_display_name = models.CharField(max_length=255, verbose_name=_("Owner display name"))
    flat_label = models.CharField(max_length=255, blank=True, verbose_name=_("Flat label"))
    representation = models.CharField(
        max_length=10,
        choices=REPRESENTATION_CHOICES,
        default=REPRESENTATION_ABSENT,
        verbose_name=_("Representation"),
    )
    proxy_name = models.CharField(max_length=255, blank=True, verbose_name=_("Proxy name"))
    share_numerator = models.PositiveIntegerField(verbose_name=_("Share numerator"))
    share_denominator = models.PositiveIntegerField(verbose_name=_("Share denominator"))
    share_value = models.DecimalField(max_digits=12, decimal_places=6, verbose_name=_("Share value"))
    unit_count = models.PositiveIntegerField(default=1, verbose_name=_("Unit count"))
    ballot_label = models.CharField(max_length=32, blank=True, verbose_name=_("Ballot label"))
    ballot_color = models.CharField(max_length=7, blank=True, verbose_name=_("Ballot color"))
    snapshot_taken_at = models.DateTimeField(verbose_name=_("Snapshot taken at"))
    first_arrived_at = models.DateTimeField(null=True, blank=True, verbose_name=_("First arrived at"))
    last_left_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Last left at"))
    is_currently_present = models.BooleanField(default=False, verbose_name=_("Currently present"))

    class Meta:
        ordering = ["meeting", "owner_display_name", "flat_label"]
        unique_together = [("meeting", "flat_owner")]
        verbose_name = _("Meeting owner snapshot")
        verbose_name_plural = _("Meeting owner snapshots")

    def __str__(self):
        return f"{self.owner_display_name} ({self.flat_label})"

    @property
    def ballot_key(self):
        return f"{self.share_value}:{self.ballot_label}:{self.ballot_color}"

    def is_present_at(self, at_time):
        events = list(self.events.order_by("event_time", "created"))
        if not events:
            if self.first_arrived_at and at_time < self.first_arrived_at:
                return False
            if self.last_left_at and at_time >= self.last_left_at:
                return False
            return self.is_currently_present

        present = False
        for event in events:
            if event.event_time > at_time:
                break
            present = event.event_type == ATTENDANCE_EVENT_ARRIVAL
        return present


class MeetingAttendanceEvent(NetBoxModel):
    owner_snapshot = models.ForeignKey(
        MeetingOwnerSnapshot,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Owner snapshot"),
    )
    event_type = models.CharField(
        max_length=10,
        choices=ATTENDANCE_EVENT_CHOICES,
        verbose_name=_("Event type"),
    )
    event_time = models.DateTimeField(verbose_name=_("Event time"))
    source = models.CharField(max_length=32, default="manual", verbose_name=_("Source"))
    note = models.CharField(max_length=255, blank=True, verbose_name=_("Note"))

    class Meta:
        ordering = ["owner_snapshot", "event_time", "created"]
        verbose_name = _("Meeting attendance event")
        verbose_name_plural = _("Meeting attendance events")

    def __str__(self):
        return f"{self.get_event_type_display()} at {self.event_time}"

    def clean(self):
        super().clean()
        previous = (
            self.owner_snapshot.events.exclude(pk=self.pk)
            .filter(event_time__lte=self.event_time)
            .order_by("-event_time", "-created")
            .first()
        )
        if previous and previous.event_type == self.event_type:
            raise ValidationError({"event_type": _("Attendance events must alternate arrival and departure.")})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ordered = list(self.owner_snapshot.events.order_by("event_time", "created"))
        arrivals = [event.event_time for event in ordered if event.event_type == ATTENDANCE_EVENT_ARRIVAL]
        departures = [event.event_time for event in ordered if event.event_type == ATTENDANCE_EVENT_DEPARTURE]
        self.owner_snapshot.first_arrived_at = arrivals[0] if arrivals else None
        self.owner_snapshot.last_left_at = departures[-1] if departures else None
        self.owner_snapshot.is_currently_present = bool(ordered and ordered[-1].event_type == ATTENDANCE_EVENT_ARRIVAL)
        self.owner_snapshot.save(
            update_fields=["first_arrived_at", "last_left_at", "is_currently_present", "last_updated"]
        )
        self.owner_snapshot.meeting.refresh_quorum(at_time=self.event_time)


class AgendaVoteSession(NetBoxModel):
    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.CASCADE,
        related_name="vote_sessions",
        verbose_name=_("Agenda item"),
    )
    started_at = models.DateTimeField(default=timezone.now, verbose_name=_("Started at"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed at"))
    negative_form = models.BooleanField(default=False, verbose_name=_("Negative form voting"))
    present_weight = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("0"),
        verbose_name=_("Present weight"),
    )
    quorum_met = models.BooleanField(default=False, verbose_name=_("Quorum met"))
    result = models.CharField(
        max_length=20,
        choices=AGENDA_RESULT_CHOICES,
        default=AGENDA_RESULT_NOT_APPLICABLE,
        verbose_name=_("Result"),
    )

    class Meta:
        ordering = ["agenda_item", "-started_at"]
        verbose_name = _("Agenda vote session")
        verbose_name_plural = _("Agenda vote sessions")

    def __str__(self):
        return _("Vote session for {agenda}").format(agenda=self.agenda_item)

    def totals_by_role(self):
        totals = {
            BALLOT_ROLE_FOR: Decimal("0"),
            BALLOT_ROLE_AGAINST: Decimal("0"),
            BALLOT_ROLE_ABSTAIN: Decimal("0"),
        }
        for row in self.ballot_rows.all():
            for role, value in row.weight_totals().items():
                totals[role] += value
        return totals

    def issued_weight_total(self):
        total = Decimal("0")
        for row in self.ballot_rows.all():
            total += Decimal(row.issued_count) * row.share_value
        return total

    def finalize(self):
        self.present_weight = self.issued_weight_total()
        self.quorum_met = (
            self.agenda_item.meeting.calculate_quorum_ratio(at_time=self.started_at)
            >= self.agenda_item.quorum_threshold
        )
        totals = self.totals_by_role()
        if self.negative_form:
            totals[BALLOT_ROLE_FOR] = max(
                Decimal("0"),
                self.present_weight - totals[BALLOT_ROLE_AGAINST] - totals[BALLOT_ROLE_ABSTAIN],
            )

        if not self.quorum_met or self.present_weight <= 0:
            self.result = AGENDA_RESULT_REJECTED
        else:
            approval_ratio = totals[BALLOT_ROLE_FOR] / self.present_weight
            self.result = (
                AGENDA_RESULT_APPROVED
                if approval_ratio >= self.agenda_item.minimum_pass_percentage
                else AGENDA_RESULT_REJECTED
            )
        self.completed_at = timezone.now()
        self.save(
            update_fields=[
                "present_weight",
                "quorum_met",
                "result",
                "completed_at",
                "last_updated",
            ]
        )
        self.agenda_item.result = self.result
        self.agenda_item.save(update_fields=["result", "last_updated"])
        return self.result


class AgendaVoteBallot(NetBoxModel):
    session = models.ForeignKey(
        AgendaVoteSession,
        on_delete=models.CASCADE,
        related_name="ballot_rows",
        verbose_name=_("Vote session"),
    )
    label = models.CharField(max_length=32, blank=True, verbose_name=_("Ballot label"))
    color = models.CharField(max_length=7, blank=True, verbose_name=_("Ballot color"))
    share_value = models.DecimalField(max_digits=12, decimal_places=6, verbose_name=_("Share value"))
    issued_count = models.PositiveIntegerField(default=0, verbose_name=_("Issued count"))
    for_count = models.PositiveIntegerField(default=0, verbose_name=_("For count"))
    against_count = models.PositiveIntegerField(default=0, verbose_name=_("Against count"))
    abstain_count = models.PositiveIntegerField(default=0, verbose_name=_("Abstain count"))

    class Meta:
        ordering = ["session", "share_value", "label"]
        verbose_name = _("Agenda vote ballot row")
        verbose_name_plural = _("Agenda vote ballot rows")

    def __str__(self):
        return _("{label} ({share})").format(label=self.label or _("Unlabeled"), share=self.share_value)

    def clean(self):
        super().clean()
        values = [self.for_count, self.against_count, self.abstain_count]
        populated = sum(1 for value in values if value)
        total_used = self.for_count + self.against_count + self.abstain_count
        if total_used > self.issued_count:
            raise ValidationError(_("Vote counts cannot exceed issued ballots."))
        if populated >= 2 and total_used < self.issued_count:
            missing = self.issued_count - total_used
            if self.for_count == 0:
                self.for_count = missing
            elif self.against_count == 0:
                self.against_count = missing
            elif self.abstain_count == 0:
                self.abstain_count = missing

    def weight_totals(self):
        return {
            BALLOT_ROLE_FOR: Decimal(self.for_count) * self.share_value,
            BALLOT_ROLE_AGAINST: Decimal(self.against_count) * self.share_value,
            BALLOT_ROLE_ABSTAIN: Decimal(self.abstain_count) * self.share_value,
        }

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Vote(NetBoxModel):
    agenda_item = models.ForeignKey(
        AgendaItem,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("Agenda item"),
    )
    attendance = models.ForeignKey(
        MeetingAttendance,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("Attendance"),
    )
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES, verbose_name=_("Vote"))
    vote_weight = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal("0"),
        verbose_name=_("Vote weight"),
        editable=False,
    )

    class Meta:
        ordering = ["agenda_item", "attendance"]
        unique_together = [("agenda_item", "attendance")]
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")

    def __str__(self):
        return f"{self.agenda_item} / {self.attendance.owner}: {self.vote}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:vote", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()
        if self.attendance.meeting_id != self.agenda_item.meeting_id:
            raise ValidationError(
                {"attendance": _("Attendance must belong to the same meeting as agenda item.")}
            )

    def save(self, *args, **kwargs):
        method = self.agenda_item.voting_method
        if method == QUORUM_TYPE_BY_UNITS:
            self.vote_weight = self.attendance.vote_weight_by_units
        else:
            self.vote_weight = self.attendance.vote_weight_by_share
        super().save(*args, **kwargs)


class MeetingMinutes(NetBoxModel):
    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name="minutes",
        verbose_name=_("Meeting"),
    )
    content = models.TextField(verbose_name=_("Content"))
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_minutes",
        verbose_name=_("Approved by"),
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Approved at"))
    cms_published = models.BooleanField(default=False, verbose_name=_("CMS published"))
    cms_published_at = models.DateTimeField(null=True, blank=True, verbose_name=_("CMS published at"))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Meeting minutes")
        verbose_name_plural = _("Meeting minutes")

    def __str__(self):
        return _("Minutes for {meeting}").format(meeting=self.meeting)

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:meetingminutes", kwargs={"pk": self.pk})


class MeetingInvitation(NetBoxModel):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("Meeting"),
    )
    owner = models.ForeignKey(
        PropertyOwner,
        on_delete=models.PROTECT,
        related_name="meeting_invitations",
        verbose_name=_("Owner"),
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Sent at"))
    delivery_method = models.CharField(
        max_length=20,
        choices=INVITATION_DELIVERY_CHOICES,
        default=INVITATION_DELIVERY_EMAIL,
        verbose_name=_("Delivery method"),
    )
    confirmed = models.BooleanField(default=False, verbose_name=_("Confirmed"))

    class Meta:
        ordering = ["meeting", "owner"]
        unique_together = [("meeting", "owner")]
        verbose_name = _("Meeting invitation")
        verbose_name_plural = _("Meeting invitations")

    def __str__(self):
        return _("Invitation for {owner} ({meeting})").format(owner=self.owner, meeting=self.meeting)

    def get_absolute_url(self):
        return reverse("plugins:solomon_meetings:meetinginvitation", kwargs={"pk": self.pk})
