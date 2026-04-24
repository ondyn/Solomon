from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

from django.contrib import messages
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

    def get_extra_context(self, request, instance):
        snapshots = instance.owner_snapshots.select_related("owner", "flat_owner").prefetch_related("events")
        agenda_items = instance.agenda_items.all().order_by("order", "title")
        present_snapshots = snapshots.filter(
            representation__in=[models.REPRESENTATION_PRESENT, models.REPRESENTATION_PROXY],
            is_currently_present=True,
        )

        present_count = present_snapshots.count()
        total_count = snapshots.count()
        present_share = sum((snapshot.share_value for snapshot in present_snapshots), Decimal("0"))
        total_share = sum((snapshot.share_value for snapshot in snapshots), Decimal("0"))

        latest_vote_sessions = {}
        for agenda_item in agenda_items:
            latest_vote_sessions[agenda_item.pk] = agenda_item.vote_sessions.order_by("-created").first()

        ballot_type_summary = instance.get_ballot_type_summary()
        summary_fraction_by_value = {
            row["share_value"]: row["share_fraction"]
            for row in ballot_type_summary
        }
        vote_styles = list(models.VoteWeightStyle.objects.order_by("voting_method", "weight_value"))
        for style in vote_styles:
            style.share_fraction_display = summary_fraction_by_value.get(
                style.weight_value,
                style.weight_fraction,
            )

        return {
            "active_tab": request.GET.get("tab", "meeting"),
            "agenda_items": agenda_items,
            "snapshots": snapshots,
            "present_count": present_count,
            "total_count": total_count,
            "present_share": present_share,
            "total_share": total_share,
            "quorum_ratio": instance.calculate_quorum_ratio(),
            "latest_vote_sessions": latest_vote_sessions,
            "agenda_form": forms.MeetingAgendaInlineForm(),
            "export_form": forms.MeetingExportForm(),
            "ballot_type_summary": ballot_type_summary,
            "vote_styles": vote_styles,
        }


class MeetingEditView(generic.ObjectEditView):
    queryset = models.Meeting.objects.all()
    form = forms.MeetingForm


class MeetingDeleteView(generic.ObjectDeleteView):
    queryset = models.Meeting.objects.all()


class MeetingBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Meeting.objects.all()
    table = tables.MeetingTable


class MeetingStartView(View):
    queryset = models.Meeting.objects.all()

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        try:
            meeting.start_meeting()
            messages.success(request, _("Meeting has been started."))
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingFinishView(View):
    queryset = models.Meeting.objects.all()

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        try:
            meeting.finish_meeting()
            messages.success(request, _("Meeting has been finished."))
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingGenerateInvitationView(View):
    queryset = models.Meeting.objects.all()

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        meeting.invitation_pdf_generated_at = timezone.now()
        meeting.save(update_fields=["invitation_pdf_generated_at", "last_updated"])
        messages.success(request, _("Invitation PDF generation was recorded."))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingPublishInvitationView(View):
    queryset = models.Meeting.objects.all()

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        meeting.invitation_published_at = timezone.now()
        meeting.save(update_fields=["invitation_published_at", "last_updated"])
        messages.success(request, _("Invitation publication was recorded."))
        return redirect(f"{meeting.get_absolute_url()}?tab=meeting")


class MeetingAttendanceToggleView(View):
    queryset = models.Meeting.objects.all()

    def post(self, request, pk):
        meeting = get_object_or_404(self.queryset, pk=pk)
        snapshot = get_object_or_404(models.MeetingOwnerSnapshot, pk=request.POST.get("snapshot_id"), meeting=meeting)

        if meeting.phase != models.MEETING_PHASE_IN_PROGRESS:
            messages.error(request, _("Attendance can be changed only while the meeting is in progress."))
            return redirect(f"{meeting.get_absolute_url()}?tab=attendance")

        event_type = (
            models.ATTENDANCE_EVENT_DEPARTURE
            if snapshot.is_currently_present
            else models.ATTENDANCE_EVENT_ARRIVAL
        )
        models.MeetingAttendanceEvent.objects.create(
            snapshot=snapshot,
            event_type=event_type,
            event_time=timezone.now(),
            source="workflow",
        )
        messages.success(request, _("Attendance status has been updated."))
        return redirect(f"{meeting.get_absolute_url()}?tab=attendance")


class MeetingAgendaAddView(View):
    queryset = models.Meeting.objects.all()

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


class MeetingAgendaMoveView(View):
    queryset = models.Meeting.objects.all()

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


class AgendaItemStartVotingView(View):
    queryset = models.AgendaItem.objects.select_related("meeting")

    def get(self, request, pk):
        agenda_item = get_object_or_404(self.queryset, pk=pk)
        meeting = agenda_item.meeting
        summary_rows = [row for row in meeting.get_ballot_type_summary() if row["issued_count"] > 0]
        return render(
            request,
            "solomon_meetings/agenda_vote_form.html",
            {
                "object": agenda_item,
                "meeting": meeting,
                "summary_rows": summary_rows,
                "rows": len(summary_rows),
            },
        )

    def post(self, request, pk):
        agenda_item = get_object_or_404(self.queryset, pk=pk)
        meeting = agenda_item.meeting
        form = forms.AgendaVoteSessionForm(request.POST)

        if not form.is_valid():
            messages.error(request, _("Voting form contains invalid values."))
            return redirect(f"{meeting.get_absolute_url()}?tab=agenda")

        session = models.AgendaVoteSession.objects.create(
            agenda_item=agenda_item,
            negative_form=form.cleaned_data["negative_form"],
        )

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
        messages.success(request, _("Voting has been recorded for this agenda point."))
        return redirect(f"{meeting.get_absolute_url()}?tab=agenda")


class MeetingSyncBallotStylesView(View):
    queryset = models.Meeting.objects.all()

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

        unique_shares = set()
        for flat_id, flat_ownerships in flat_to_ownerships.items():
            flat = flat_ownerships[0].flat
            if len(flat_ownerships) == 1:
                o = flat_ownerships[0]
                if o.share_denominator:
                    unique_shares.add(Decimal(o.share_numerator) / Decimal(o.share_denominator))
            else:
                if flat.cuzk_share_numerator and flat.cuzk_share_denominator:
                    unique_shares.add(
                        Decimal(flat.cuzk_share_numerator) / Decimal(flat.cuzk_share_denominator)
                    )
                else:
                    total = sum(
                        (Fraction(o.share_numerator, o.share_denominator) for o in flat_ownerships),
                        Fraction(0, 1),
                    )
                    if total.denominator:
                        unique_shares.add(Decimal(total.numerator) / Decimal(total.denominator))

        unique_shares = sorted(unique_shares)
        created = 0
        for share in unique_shares:
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
                label=label,
                color="#1976D2",
            )
            created += 1

        meeting.snapshot_owners()
        messages.success(request, _("Ballot types synchronized from ownership shares."))
        return redirect(f"{meeting.get_absolute_url()}?tab=ballots")


class MeetingExportView(View):
    queryset = models.Meeting.objects.all()

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
            lines.append("Attendance")
            for snapshot in meeting.owner_snapshots.all().order_by("owner_display_name"):
                lines.append(
                    f"- {snapshot.owner_display_name}: {'present' if snapshot.is_currently_present else 'absent'}"
                )
            lines.append("")

        if form.cleaned_data["include_voting"]:
            lines.append("Voting")
            for agenda_item in meeting.agenda_items.all().order_by("order"):
                latest_session = agenda_item.vote_sessions.order_by("-created").first()
                if latest_session:
                    lines.append(f"- {agenda_item.order}. {agenda_item.title}: {latest_session.get_result_display()}")
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
    queryset = models.MeetingAttendanceEvent.objects.select_related("snapshot", "snapshot__meeting")
    table = tables.MeetingAttendanceEventTable

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        snapshot_id = request.GET.get("snapshot_id")
        if snapshot_id:
            queryset = queryset.filter(snapshot_id=snapshot_id)
        return queryset


class MeetingAttendanceEventView(generic.ObjectView):
    queryset = models.MeetingAttendanceEvent.objects.select_related("snapshot", "snapshot__meeting")


class MeetingAttendanceEventEditView(generic.ObjectEditView):
    queryset = models.MeetingAttendanceEvent.objects.all()
    form = forms.MeetingAttendanceEventForm


class MeetingAttendanceEventDeleteView(generic.ObjectDeleteView):
    queryset = models.MeetingAttendanceEvent.objects.all()


class MeetingAttendanceEventBulkDeleteView(generic.BulkDeleteView):
    queryset = models.MeetingAttendanceEvent.objects.select_related("snapshot", "snapshot__meeting")
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
