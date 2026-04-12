from netbox.views import generic

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


class MeetingEditView(generic.ObjectEditView):
    queryset = models.Meeting.objects.all()
    form = forms.MeetingForm


class MeetingDeleteView(generic.ObjectDeleteView):
    queryset = models.Meeting.objects.all()


class MeetingBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Meeting.objects.all()
    table = tables.MeetingTable


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
