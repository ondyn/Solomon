from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from netbox.views import generic

from solomon_property.models import FlatOwner

from . import filterforms, filtersets, forms, models, tables


class MeetingTypeListView(generic.ObjectListView):
    queryset = models.MeetingType.objects.all()
    table = tables.MeetingTypeTable
    filterset = filtersets.MeetingTypeFilterSet
    filterset_form = filterforms.MeetingTypeFilterForm


class MeetingTypeView(generic.ObjectView):
    queryset = models.MeetingType.objects.all()


class MeetingTypeEditView(generic.ObjectEditView):
    queryset = models.MeetingType.objects.all()
    form = forms.MeetingTypeForm


class MeetingTypeDeleteView(generic.ObjectDeleteView):
    queryset = models.MeetingType.objects.all()


class MeetingTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MeetingType.objects.all()
    table = tables.MeetingTypeTable


class MeetingListView(generic.ObjectListView):
    queryset = models.Meeting.objects.select_related("meeting_type", "moderator")
    table = tables.MeetingTable
    filterset = filtersets.MeetingFilterSet
    filterset_form = filterforms.MeetingFilterForm


class MeetingView(generic.ObjectView):
    queryset = models.Meeting.objects.select_related("meeting_type", "moderator").prefetch_related("buildings")

    @staticmethod
    def _fraction_from_pairs(pairs):
        valid_pairs = [(num, den) for num, den in pairs if den]
        if not valid_pairs:
            return 0, 1

        common_denominator = valid_pairs[0][1]
        for _, denominator in valid_pairs[1:]:
            common_denominator = models.lcm(common_denominator, denominator)

        numerator = sum(num * common_denominator // den for num, den in valid_pairs)
        return numerator, common_denominator

    @staticmethod
    def _format_fraction_pair(numerator, denominator):
        return f"{numerator}/{denominator}"

    @staticmethod
    def _fraction_to_decimal(numerator, denominator):
        if not denominator:
            return Decimal("0")
        return Decimal(numerator) / Decimal(denominator)

    @staticmethod
    def _build_attendance_rows(snapshots):
        style_map = {
            style.weight_value: (style.label, style.color)
            for style in models.VoteWeightStyle.objects.filter(
                voting_method=models.QUORUM_TYPE_BY_SHARE,
                weight_value__in={snapshot.share_value for snapshot in snapshots},
            )
        }
        snapshots_by_owner = defaultdict(list)
        for snapshot in snapshots:
            snapshots_by_owner[snapshot.owner_id].append(snapshot)

        rows = []
        for owner_snapshots in snapshots_by_owner.values():
            owner_snapshots.sort(key=lambda snapshot: snapshot.flat_label)
            share_numerator, share_denominator = MeetingView._fraction_from_pairs(
                [
                    (snapshot.share_numerator, snapshot.share_denominator)
                    for snapshot in owner_snapshots
                ]
            )

            first_arrivals = [snapshot.first_arrived_at for snapshot in owner_snapshots if snapshot.first_arrived_at]
            last_departures = [snapshot.last_left_at for snapshot in owner_snapshots if snapshot.last_left_at]
            flat_labels = [snapshot.flat_label for snapshot in owner_snapshots if snapshot.flat_label]
            ballot_options = {
                style_map.get(
                    snapshot.share_value,
                    (snapshot.ballot_label or "-", snapshot.ballot_color or ""),
                )
                for snapshot in owner_snapshots
            }
            ballot_label, ballot_color = next(iter(ballot_options))
            if len(ballot_options) > 1:
                ballot_label = _("Multiple")
                ballot_color = ""

            rows.append(
                {
                    "owner_id": owner_snapshots[0].owner_id,
                    "owner_display_name": owner_snapshots[0].owner_display_name,
                    "flat_label": ", ".join(flat_labels),
                    "share_fraction": MeetingView._format_fraction_pair(
                        share_numerator,
                        share_denominator,
                    ),
                    "share_fraction_numerator": share_numerator,
                    "share_fraction_denominator": share_denominator,
                    "share_value": sum((snapshot.share_value for snapshot in owner_snapshots), Decimal("0")),
                    "ballot_label": ballot_label,
                    "ballot_color": ballot_color,
                    "is_currently_present": any(snapshot.is_currently_present for snapshot in owner_snapshots),
                    "first_arrived_at": min(first_arrivals) if first_arrivals else None,
                    "last_left_at": max(last_departures) if last_departures else None,
                    "event_snapshot_id": owner_snapshots[0].pk,
                }
            )

        rows.sort(key=lambda row: row["owner_display_name"].lower())
        return rows

    def get_extra_context(self, request, instance):
        snapshots = list(instance.owner_snapshots.select_related("owner", "flat_owner").prefetch_related("events"))
        attendance_rows = self._build_attendance_rows(snapshots)
        agenda_items = list(instance.agenda_items.all().order_by("order", "title"))

        present_count = sum(1 for row in attendance_rows if row["is_currently_present"])
        total_count = len(attendance_rows)
        present_share_numerator, present_share_denominator = self._fraction_from_pairs(
            [
                (row["share_fraction_numerator"], row["share_fraction_denominator"])
                for row in attendance_rows
                if row["is_currently_present"]
            ]
        )
        total_share_numerator, total_share_denominator = self._fraction_from_pairs(
            [
                (row["share_fraction_numerator"], row["share_fraction_denominator"])
                for row in attendance_rows
            ]
        )
        present_share_ratio = self._fraction_to_decimal(present_share_numerator, present_share_denominator)
        attendance_threshold_checks = [
            {
                "label": _("50% of shares present"),
                "threshold": instance.meeting_type.attendance_threshold_50,
                "threshold_percent": instance.meeting_type.attendance_threshold_50 * Decimal("100"),
                "is_met": present_share_ratio >= instance.meeting_type.attendance_threshold_50,
            },
            {
                "label": _("2/3 of shares present"),
                "threshold": instance.meeting_type.attendance_threshold_two_thirds,
                "threshold_percent": instance.meeting_type.attendance_threshold_two_thirds * Decimal("100"),
                "is_met": present_share_ratio >= instance.meeting_type.attendance_threshold_two_thirds,
            },
        ]

        for agenda_item in agenda_items:
            agenda_item.latest_vote_session = agenda_item.vote_sessions.order_by("-created").first()
            agenda_item.latest_vote_percentages = None
            if agenda_item.latest_vote_session and agenda_item.latest_vote_session.present_weight > 0:
                totals = agenda_item.latest_vote_session.totals_by_role()
                present_weight = agenda_item.latest_vote_session.present_weight
                agenda_item.latest_vote_percentages = {
                    "for": (totals[models.BALLOT_ROLE_FOR] / present_weight) * Decimal("100"),
                    "against": (totals[models.BALLOT_ROLE_AGAINST] / present_weight) * Decimal("100"),
                    "abstain": (totals[models.BALLOT_ROLE_ABSTAIN] / present_weight) * Decimal("100"),
                }

        quorum_ratio = instance.calculate_quorum_ratio()
        ballot_type_summary = instance.get_ballot_type_summary()
        return {
            "active_tab": request.GET.get("tab", "meeting"),
            "agenda_items": agenda_items,
            "attendance_rows": attendance_rows,
            "present_count": present_count,
            "total_count": total_count,
            "present_share": self._format_fraction_pair(
                present_share_numerator,
                present_share_denominator,
            ),
            "present_share_ratio": present_share_ratio,
            "present_share_ratio_percent": present_share_ratio * Decimal("100"),
            "total_share": self._format_fraction_pair(
                total_share_numerator,
                total_share_denominator,
            ),
            "attendance_threshold_checks": attendance_threshold_checks,
            "quorum_ratio": quorum_ratio,
            "quorum_ratio_percent": quorum_ratio * Decimal("100"),
            "agenda_form": forms.MeetingAgendaInlineForm(),
            "export_form": forms.MeetingExportForm(),
            "ballot_type_summary": ballot_type_summary,
        }


class MeetingEditView(generic.ObjectEditView):
    queryset = models.Meeting.objects.all()
    form = forms.MeetingForm


class MeetingDeleteView(generic.ObjectDeleteView):
    queryset = models.Meeting.objects.all()


class MeetingBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Meeting.objects.all()
    table = tables.MeetingTable


class MeetingStartView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_meeting_workflow"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        try:
            meeting.start_meeting()
            messages.success(request, _("Meeting has been started."))
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingFinishView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_meeting_workflow"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        try:
            meeting.finish_meeting()
            messages.success(request, _("Meeting has been finished."))
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingGenerateInvitationView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_meeting_workflow"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        meeting.invitation_pdf_generated_at = timezone.now()
        meeting.save(update_fields=["invitation_pdf_generated_at", "last_updated"])
        messages.success(request, _("Invitation PDF generation was recorded."))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingPublishInvitationView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_meeting_workflow"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        meeting.invitation_published_at = timezone.now()
        meeting.save(update_fields=["invitation_published_at", "last_updated"])
        messages.success(request, _("Invitation publication was recorded."))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingAttendanceToggleView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_attendance_live"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)

        if meeting.phase != models.MEETING_PHASE_IN_PROGRESS:
            messages.error(request, _("Attendance can be changed only while the meeting is in progress."))
            return redirect(f"{meeting.get_absolute_url()}?tab=attendance")

        snapshots = models.MeetingOwnerSnapshot.objects.filter(meeting=meeting)
        owner_id = request.POST.get("owner_id")
        if owner_id:
            snapshots = snapshots.filter(owner_id=owner_id)
        else:
            snapshots = snapshots.filter(pk=request.POST.get("snapshot_id"))

        if not snapshots.exists():
            messages.error(request, _("Owner snapshot was not found."))
            return redirect(f"{meeting.get_absolute_url()}?tab=attendance")

        is_currently_present = snapshots.filter(is_currently_present=True).exists()

        event_type = (
            models.ATTENDANCE_EVENT_DEPARTURE
            if is_currently_present
            else models.ATTENDANCE_EVENT_ARRIVAL
        )
        event_time = timezone.now()
        for snapshot in snapshots:
            models.MeetingAttendanceEvent.objects.create(
                owner_snapshot=snapshot,
                event_type=event_type,
                event_time=event_time,
                source="workflow",
            )
        messages.success(request, _("Attendance status has been updated."))
        return redirect(f"{meeting.get_absolute_url()}?tab=attendance")


class MeetingAgendaAddView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_meeting_workflow"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        form = forms.MeetingAgendaInlineForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Agenda point could not be created. Check input values."))
            return redirect(f"{meeting.get_absolute_url()}?tab=agenda")

        next_order = (meeting.agenda_items.order_by("-order").values_list("order", flat=True).first() or 0) + 1
        models.AgendaItem.objects.create(
            meeting=meeting,
            order=next_order,
            title=form.cleaned_data["title"],
            description=form.cleaned_data["description"],
            presenter=form.cleaned_data["presenter"],
            voting_required=form.cleaned_data["voting_required"],
            voting_method=form.cleaned_data["voting_method"],
            quorum_threshold=form.cleaned_data["quorum_threshold"],
            minimum_pass_percentage=form.cleaned_data["minimum_pass_percentage"],
        )
        messages.success(request, _("Agenda point added."))
        return redirect(f"{meeting.get_absolute_url()}?tab=agenda")


class MeetingAgendaMoveView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.manage_meeting_workflow"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        agenda_item = get_object_or_404(models.AgendaItem, pk=request.POST.get("agenda_item_id"), meeting=meeting)
        direction = request.POST.get("direction")

        if direction == "up":
            swap_with = (
                meeting.agenda_items.filter(order__lt=agenda_item.order)
                .order_by("-order")
                .first()
            )
        else:
            swap_with = (
                meeting.agenda_items.filter(order__gt=agenda_item.order)
                .order_by("order")
                .first()
            )

        if swap_with:
            old_order = agenda_item.order
            agenda_item.order = swap_with.order
            swap_with.order = old_order
            agenda_item.save(update_fields=["order", "last_updated"])
            swap_with.save(update_fields=["order", "last_updated"])

        return redirect(f"{meeting.get_absolute_url()}?tab=agenda")


class AgendaItemStartVotingView(PermissionRequiredMixin, View):
    queryset = models.AgendaItem.objects.select_related("meeting")
    permission_required = "solomon_meetings.run_voting_session"
    raise_exception = True

    @staticmethod
    def _share_fraction_from_decimal(share_value):
        style = models.VoteWeightStyle.objects.filter(
            voting_method=models.QUORUM_TYPE_BY_SHARE,
            weight_value=share_value,
        ).first()
        if style:
            return style.weight_fraction

        fraction = Fraction(str(share_value)).limit_denominator(1000000)
        return f"{fraction.numerator}/{fraction.denominator}"

    def _rows_from_existing_session(self, session):
        rows = []
        for row in session.ballot_rows.order_by("share_value", "label"):
            rows.append(
                {
                    "label": row.label,
                    "color": row.color,
                    "share_value": row.share_value,
                    "share_fraction": self._share_fraction_from_decimal(row.share_value),
                    "issued_count": row.issued_count,
                    "for_count": row.for_count,
                    "against_count": row.against_count,
                    "abstain_count": row.abstain_count,
                }
            )
        return rows

    def get(self, request, pk):
        agenda_item = get_object_or_404(self.queryset, pk=pk)
        meeting = agenda_item.meeting
        selected_session = None
        session_id = request.GET.get("session")
        if session_id:
            selected_session = agenda_item.vote_sessions.filter(pk=session_id).first()
        if selected_session is None:
            selected_session = agenda_item.vote_sessions.order_by("-created").first()

        if selected_session:
            summary_rows = self._rows_from_existing_session(selected_session)
        else:
            summary_rows = [
                {
                    **row,
                    "for_count": None,
                    "against_count": None,
                    "abstain_count": None,
                }
                for row in meeting.get_ballot_type_summary()
                if row["issued_count"] > 0
            ]

        return render(
            request,
            "solomon_meetings/agenda_vote_form.html",
            {
                "object": agenda_item,
                "meeting": meeting,
                "summary_rows": summary_rows,
                "rows": len(summary_rows),
                "editing_session": selected_session,
            },
        )

    def post(self, request, pk):
        agenda_item = get_object_or_404(self.queryset, pk=pk)
        meeting = agenda_item.meeting
        form = forms.AgendaVoteSessionForm(request.POST)

        if not form.is_valid():
            messages.error(request, _("Voting form contains invalid values."))
            return redirect(f"{meeting.get_absolute_url()}?tab=agenda")

        session_id = request.POST.get("session_id")
        if session_id:
            session = get_object_or_404(models.AgendaVoteSession, pk=session_id, agenda_item=agenda_item)
            session.negative_form = False
            session.save(update_fields=["negative_form", "last_updated"])
            session.ballot_rows.all().delete()
            created_new_session = False
        else:
            session = models.AgendaVoteSession.objects.create(
                agenda_item=agenda_item,
                negative_form=False,
            )
            created_new_session = True

        for row in form.cleaned_data["parsed_rows"]:
            models.AgendaVoteBallot.objects.create(
                session=session,
                label=row["label"],
                color=row["color"],
                share_value=row["share_value"],
                issued_count=row["issued_count"],
                for_count=row["for_count"],
                against_count=row["against_count"],
                abstain_count=row["abstain_count"],
            )

        session.finalize()
        if created_new_session:
            messages.success(request, _("Voting has been recorded for this agenda point."))
        else:
            messages.success(request, _("Voting has been updated for this agenda point."))
        return redirect(f"{meeting.get_absolute_url()}?tab=agenda")


class MeetingSyncBallotStylesView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.sync_ballot_styles"
    raise_exception = True

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        ownerships = FlatOwner.objects.filter(
            flat__building__in=meeting.buildings.all(),
            effective_to__isnull=True,
        ).select_related("flat")

        # Group by flat: co-owned flats use flat CUZK share; sole-owned use FlatOwner share
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
                share_fraction = Fraction(ownership.share_numerator, ownership.share_denominator)
            else:
                flat = flat_ownerships[0].flat
                holder_key = ("flat", flat_id)
                if flat.cuzk_share_numerator and flat.cuzk_share_denominator:
                    share_fraction = Fraction(flat.cuzk_share_numerator, flat.cuzk_share_denominator)
                else:
                    share_fraction = sum(
                        (Fraction(o.share_numerator, o.share_denominator) for o in flat_ownerships),
                        Fraction(0, 1),
                    )

            holder_totals[holder_key] += share_fraction

        unique_shares = sorted(set(holder_totals.values()))

        created = 0
        for share_fraction in unique_shares:
            numerator = share_fraction.numerator
            denominator = share_fraction.denominator
            share = models.quantize_weight_fraction(numerator, denominator)
            exists = models.VoteWeightStyle.objects.filter(
                voting_method=models.QUORUM_TYPE_BY_SHARE,
                weight_value=share,
            ).exists()
            if exists:
                continue

            label = f"S{created + 1}"
            while models.VoteWeightStyle.objects.filter(
                voting_method=models.QUORUM_TYPE_BY_SHARE,
                label=label,
            ).exists():
                created += 1
                label = f"S{created + 1}"

            models.VoteWeightStyle.objects.create(
                voting_method=models.QUORUM_TYPE_BY_SHARE,
                weight_value=share,
                weight_numerator=numerator,
                weight_denominator=denominator,
                label=label,
                color="#1976D2",
            )
            created += 1

        meeting.snapshot_owners(refresh_existing=True)
        messages.success(request, _("Ballot types synchronized from ownership shares."))
        return redirect(f"{meeting.get_absolute_url()}?tab=ballots")


class MeetingExportView(PermissionRequiredMixin, View):
    queryset = models.Meeting.objects.all()
    permission_required = "solomon_meetings.export_meeting_data"
    raise_exception = True

    @staticmethod
    def _format_datetime(value):
        if not value:
            return "-"
        return timezone.localtime(value).isoformat(timespec="minutes")

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        form = forms.MeetingExportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please select valid export options."))
            return redirect(f"{meeting.get_absolute_url()}?tab=meeting")

        lines = [
            f"Meeting: {meeting.title}",
            f"Date: {meeting.date_time}",
            f"Location: {meeting.location}",
            f"Status: {meeting.get_status_display()}",
            "",
        ]

        if form.cleaned_data["include_attendance"]:
            lines.append("Attendance snapshots")
            snapshots = meeting.owner_snapshots.prefetch_related("events").order_by("owner_display_name", "flat_label")
            for snapshot in snapshots:
                share_fraction = f"{snapshot.share_numerator}/{snapshot.share_denominator}"
                current_status = "present" if snapshot.is_currently_present else "absent"
                lines.append(
                    f"- {snapshot.owner_display_name} | Flat: {snapshot.flat_label or '-'} | "
                    f"Share: {share_fraction} ({snapshot.share_value:.6f}) | "
                    f"Current status: {current_status} | "
                    f"First arrived: {self._format_datetime(snapshot.first_arrived_at)} | "
                    f"Last left: {self._format_datetime(snapshot.last_left_at)}"
                )

                events = list(snapshot.events.all().order_by("event_time", "created"))
                if events:
                    for event in events:
                        lines.append(
                            f"  - {self._format_datetime(event.event_time)} | {event.get_event_type_display()} "
                            f"| Source: {event.source}{f' | Note: {event.note}' if event.note else ''}"
                        )
                else:
                    lines.append("  - No attendance events recorded.")

            lines.append("")
            lines.append("Attendance event timeline")
            timeline_events = (
                models.MeetingAttendanceEvent.objects.filter(owner_snapshot__meeting=meeting)
                .select_related("owner_snapshot")
                .order_by("event_time", "created")
            )
            if timeline_events.exists():
                for event in timeline_events:
                    snapshot = event.owner_snapshot
                    lines.append(
                        f"- {self._format_datetime(event.event_time)} | {snapshot.owner_display_name} "
                        f"({snapshot.flat_label or '-'}) | {event.get_event_type_display()} | "
                        f"Share: {snapshot.share_numerator}/{snapshot.share_denominator} ({snapshot.share_value:.6f})"
                    )
            else:
                lines.append("- No attendance events recorded.")
            lines.append("")

        if form.cleaned_data["include_voting"]:
            lines.append("Voting sessions")
            agenda_items = meeting.agenda_items.prefetch_related("vote_sessions__ballot_rows").order_by("order", "title")
            for agenda_item in agenda_items:
                lines.append(f"- {agenda_item.order}. {agenda_item.title}")
                lines.append(
                    f"  Thresholds: quorum >= {agenda_item.quorum_threshold * Decimal('100'):.2f}% | "
                    f"pass >= {agenda_item.minimum_pass_percentage * Decimal('100'):.2f}%"
                )
                sessions = list(agenda_item.vote_sessions.all().order_by("started_at", "created"))
                if not sessions:
                    lines.append("  No vote sessions recorded.")
                    continue

                for session in sessions:
                    totals = session.totals_by_role()
                    present_weight = session.present_weight
                    attendance_share_percent = (
                        meeting.calculate_quorum_ratio(at_time=session.started_at) * Decimal("100")
                    )
                    if present_weight > 0:
                        for_percent = (totals[models.BALLOT_ROLE_FOR] / present_weight) * Decimal("100")
                        against_percent = (totals[models.BALLOT_ROLE_AGAINST] / present_weight) * Decimal("100")
                        abstain_percent = (totals[models.BALLOT_ROLE_ABSTAIN] / present_weight) * Decimal("100")
                    else:
                        for_percent = Decimal("0")
                        against_percent = Decimal("0")
                        abstain_percent = Decimal("0")

                    lines.append(
                        f"  Session: started {self._format_datetime(session.started_at)} | "
                        f"completed {self._format_datetime(session.completed_at)}"
                    )
                    lines.append(
                        f"  Result: {session.get_result_display()} | Quorum met: {'yes' if session.quorum_met else 'no'}"
                    )
                    lines.append(f"  Attendance share at vote start: {attendance_share_percent:.2f}%")
                    lines.append(f"  Present weighted share in session: {present_weight:.6f}")
                    lines.append(
                        f"  Totals (weighted share): For {totals[models.BALLOT_ROLE_FOR]:.6f} ({for_percent:.2f}%), "
                        f"Against {totals[models.BALLOT_ROLE_AGAINST]:.6f} ({against_percent:.2f}%), "
                        f"Abstain {totals[models.BALLOT_ROLE_ABSTAIN]:.6f} ({abstain_percent:.2f}%)"
                    )

                    lines.append("  Ballot rows:")
                    for row in session.ballot_rows.all().order_by("share_value", "label"):
                        weighted = row.weight_totals()
                        lines.append(
                            f"    - Label: {row.label or '-'} | Color: {row.color or '-'} | "
                            f"Share value: {row.share_value:.6f} | Issued: {row.issued_count} | "
                            f"For: {row.for_count} | Against: {row.against_count} | Abstain: {row.abstain_count} | "
                            f"Weighted For: {weighted[models.BALLOT_ROLE_FOR]:.6f} | "
                            f"Weighted Against: {weighted[models.BALLOT_ROLE_AGAINST]:.6f} | "
                            f"Weighted Abstain: {weighted[models.BALLOT_ROLE_ABSTAIN]:.6f}"
                        )
            lines.append("")

        if form.cleaned_data["include_agenda_texts"]:
            lines.append("Agenda")
            for agenda_item in meeting.agenda_items.all().order_by("order"):
                lines.append(f"- {agenda_item.order}. {agenda_item.title}")
                if agenda_item.description:
                    lines.append(f"  {agenda_item.description}")

        response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="meeting-{meeting.pk}-export.txt"'
        return response


class AgendaItemListView(generic.ObjectListView):
    queryset = models.AgendaItem.objects.select_related("meeting")
    table = tables.AgendaItemTable
    filterset = filtersets.AgendaItemFilterSet
    filterset_form = filterforms.AgendaItemFilterForm


class AgendaItemView(generic.ObjectView):
    queryset = models.AgendaItem.objects.select_related("meeting")

    def get_extra_context(self, request, instance):
        vote_sessions = list(instance.vote_sessions.prefetch_related("ballot_rows").order_by("-started_at", "-created"))
        latest_session = vote_sessions[0] if vote_sessions else None
        latest_totals = latest_session.totals_by_role() if latest_session else None
        latest_vote_percentages = None
        latest_attendance_share_percent = None
        if latest_session and latest_session.present_weight > 0:
            latest_vote_percentages = {
                "for": (latest_totals[models.BALLOT_ROLE_FOR] / latest_session.present_weight) * Decimal("100"),
                "against": (latest_totals[models.BALLOT_ROLE_AGAINST] / latest_session.present_weight) * Decimal("100"),
                "abstain": (latest_totals[models.BALLOT_ROLE_ABSTAIN] / latest_session.present_weight)
                * Decimal("100"),
            }
            latest_attendance_share_percent = (
                instance.meeting.calculate_quorum_ratio(at_time=latest_session.started_at) * Decimal("100")
            )
        return {
            "vote_sessions": vote_sessions,
            "latest_vote_session": latest_session,
            "latest_vote_totals": latest_totals,
            "latest_vote_percentages": latest_vote_percentages,
            "latest_attendance_share_percent": latest_attendance_share_percent,
        }


class AgendaItemEditView(generic.ObjectEditView):
    queryset = models.AgendaItem.objects.all()
    form = forms.AgendaItemForm


class AgendaItemDeleteView(generic.ObjectDeleteView):
    queryset = models.AgendaItem.objects.all()


class AgendaItemBulkDeleteView(generic.BulkDeleteView):
    queryset = models.AgendaItem.objects.all()
    table = tables.AgendaItemTable


class MeetingAttendanceListView(generic.ObjectListView):
    queryset = models.MeetingAttendance.objects.select_related("meeting", "owner", "flat_owner")
    table = tables.MeetingAttendanceTable
    filterset = filtersets.MeetingAttendanceFilterSet
    filterset_form = filterforms.MeetingAttendanceFilterForm


class MeetingAttendanceView(generic.ObjectView):
    queryset = models.MeetingAttendance.objects.select_related("meeting", "owner", "flat_owner")


class MeetingAttendanceEditView(generic.ObjectEditView):
    queryset = models.MeetingAttendance.objects.all()
    form = forms.MeetingAttendanceForm


class MeetingAttendanceDeleteView(generic.ObjectDeleteView):
    queryset = models.MeetingAttendance.objects.all()


class MeetingAttendanceBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MeetingAttendance.objects.all()
    table = tables.MeetingAttendanceTable


class MeetingOwnerSnapshotListView(generic.ObjectListView):
    queryset = models.MeetingOwnerSnapshot.objects.select_related("meeting", "owner", "flat_owner")
    table = tables.MeetingOwnerSnapshotTable


class MeetingOwnerSnapshotView(generic.ObjectView):
    queryset = models.MeetingOwnerSnapshot.objects.select_related("meeting", "owner", "flat_owner")


class MeetingAttendanceEventListView(generic.ObjectListView):
    queryset = models.MeetingAttendanceEvent.objects.select_related("owner_snapshot", "owner_snapshot__meeting")
    table = tables.MeetingAttendanceEventTable

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        snapshot_id = request.GET.get("snapshot_id")
        if snapshot_id:
            queryset = queryset.filter(owner_snapshot_id=snapshot_id)
        owner_id = request.GET.get("owner_id")
        meeting_id = request.GET.get("meeting_id")
        if owner_id:
            queryset = queryset.filter(owner_snapshot__owner_id=owner_id)
        if meeting_id:
            queryset = queryset.filter(owner_snapshot__meeting_id=meeting_id)
        return queryset


class MeetingAttendanceEventView(generic.ObjectView):
    queryset = models.MeetingAttendanceEvent.objects.select_related("owner_snapshot", "owner_snapshot__meeting")


class MeetingAttendanceEventEditView(generic.ObjectEditView):
    queryset = models.MeetingAttendanceEvent.objects.all()
    form = forms.MeetingAttendanceEventForm


class MeetingAttendanceEventDeleteView(generic.ObjectDeleteView):
    queryset = models.MeetingAttendanceEvent.objects.all()


class MeetingAttendanceEventBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MeetingAttendanceEvent.objects.select_related("owner_snapshot", "owner_snapshot__meeting")
    table = tables.MeetingAttendanceEventTable


class VoteListView(generic.ObjectListView):
    queryset = models.Vote.objects.select_related("agenda_item", "attendance")
    table = tables.VoteTable
    filterset = filtersets.VoteFilterSet


class VoteView(generic.ObjectView):
    queryset = models.Vote.objects.select_related("agenda_item", "attendance")


class VoteEditView(generic.ObjectEditView):
    queryset = models.Vote.objects.all()
    form = forms.VoteForm


class VoteDeleteView(generic.ObjectDeleteView):
    queryset = models.Vote.objects.all()


class VoteBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Vote.objects.all()
    table = tables.VoteTable


class VoteWeightStyleListView(generic.ObjectListView):
    queryset = models.VoteWeightStyle.objects.all()
    table = tables.VoteWeightStyleTable
    filterset = filtersets.VoteWeightStyleFilterSet


class VoteWeightStyleView(generic.ObjectView):
    queryset = models.VoteWeightStyle.objects.all()


class VoteWeightStyleEditView(generic.ObjectEditView):
    queryset = models.VoteWeightStyle.objects.all()
    form = forms.VoteWeightStyleForm


class VoteWeightStyleDeleteView(generic.ObjectDeleteView):
    queryset = models.VoteWeightStyle.objects.all()


class VoteWeightStyleBulkDeleteView(generic.BulkDeleteView):
    queryset = models.VoteWeightStyle.objects.all()
    table = tables.VoteWeightStyleTable


class AgendaVoteSessionListView(generic.ObjectListView):
    queryset = models.AgendaVoteSession.objects.select_related("agenda_item", "agenda_item__meeting")
    table = tables.AgendaVoteSessionTable


class AgendaVoteSessionView(generic.ObjectView):
    queryset = models.AgendaVoteSession.objects.select_related("agenda_item", "agenda_item__meeting")


class AgendaVoteSessionDeleteView(generic.ObjectDeleteView):
    queryset = models.AgendaVoteSession.objects.all()


class AgendaVoteBallotListView(generic.ObjectListView):
    queryset = models.AgendaVoteBallot.objects.select_related("session", "session__agenda_item")
    table = tables.AgendaVoteBallotTable


class AgendaVoteBallotView(generic.ObjectView):
    queryset = models.AgendaVoteBallot.objects.select_related("session", "session__agenda_item")


class AgendaVoteBallotDeleteView(generic.ObjectDeleteView):
    queryset = models.AgendaVoteBallot.objects.all()


class MeetingMinutesListView(generic.ObjectListView):
    queryset = models.MeetingMinutes.objects.select_related("meeting", "approved_by")
    table = tables.MeetingMinutesTable
    filterset = filtersets.MeetingMinutesFilterSet


class MeetingMinutesView(generic.ObjectView):
    queryset = models.MeetingMinutes.objects.select_related("meeting", "approved_by")


class MeetingMinutesEditView(generic.ObjectEditView):
    queryset = models.MeetingMinutes.objects.all()
    form = forms.MeetingMinutesForm


class MeetingMinutesDeleteView(generic.ObjectDeleteView):
    queryset = models.MeetingMinutes.objects.all()


class MeetingMinutesBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MeetingMinutes.objects.all()
    table = tables.MeetingMinutesTable


class MeetingInvitationListView(generic.ObjectListView):
    queryset = models.MeetingInvitation.objects.select_related("meeting", "owner")
    table = tables.MeetingInvitationTable
    filterset = filtersets.MeetingInvitationFilterSet


class MeetingInvitationView(generic.ObjectView):
    queryset = models.MeetingInvitation.objects.select_related("meeting", "owner")


class MeetingInvitationEditView(generic.ObjectEditView):
    queryset = models.MeetingInvitation.objects.all()
    form = forms.MeetingInvitationForm


class MeetingInvitationDeleteView(generic.ObjectDeleteView):
    queryset = models.MeetingInvitation.objects.all()


class MeetingInvitationBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MeetingInvitation.objects.all()
    table = tables.MeetingInvitationTable
