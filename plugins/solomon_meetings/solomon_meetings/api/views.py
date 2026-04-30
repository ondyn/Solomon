from netbox.api.viewsets import NetBoxModelViewSet

from solomon_meetings import filtersets, models

from .serializers import (
    AgendaItemSerializer,
    AgendaVoteBallotSerializer,
    AgendaVoteSessionSerializer,
    MeetingAttendanceSerializer,
    MeetingAttendanceEventSerializer,
    MeetingInvitationSerializer,
    MeetingMinutesSerializer,
    MeetingOwnerSnapshotSerializer,
    MeetingSerializer,
    MeetingTypeSerializer,
    VoteSerializer,
    VoteWeightStyleSerializer,
)


class MeetingTypeViewSet(NetBoxModelViewSet):
    queryset = models.MeetingType.objects.all()
    serializer_class = MeetingTypeSerializer
    filterset_class = filtersets.MeetingTypeFilterSet


class MeetingViewSet(NetBoxModelViewSet):
    queryset = models.Meeting.objects.select_related("meeting_type", "moderator")
    serializer_class = MeetingSerializer
    filterset_class = filtersets.MeetingFilterSet


class AgendaItemViewSet(NetBoxModelViewSet):
    queryset = models.AgendaItem.objects.select_related("meeting")
    serializer_class = AgendaItemSerializer
    filterset_class = filtersets.AgendaItemFilterSet


class MeetingAttendanceViewSet(NetBoxModelViewSet):
    queryset = models.MeetingAttendance.objects.select_related("meeting", "owner", "flat_owner")
    serializer_class = MeetingAttendanceSerializer
    filterset_class = filtersets.MeetingAttendanceFilterSet


class MeetingOwnerSnapshotViewSet(NetBoxModelViewSet):
    queryset = models.MeetingOwnerSnapshot.objects.select_related("meeting", "owner", "flat_owner")
    serializer_class = MeetingOwnerSnapshotSerializer
    filterset_class = filtersets.MeetingOwnerSnapshotFilterSet


class MeetingAttendanceEventViewSet(NetBoxModelViewSet):
    queryset = models.MeetingAttendanceEvent.objects.select_related("owner_snapshot", "owner_snapshot__meeting")
    serializer_class = MeetingAttendanceEventSerializer
    filterset_class = filtersets.MeetingAttendanceEventFilterSet


class VoteViewSet(NetBoxModelViewSet):
    queryset = models.Vote.objects.select_related("agenda_item", "attendance")
    serializer_class = VoteSerializer
    filterset_class = filtersets.VoteFilterSet


class VoteWeightStyleViewSet(NetBoxModelViewSet):
    queryset = models.VoteWeightStyle.objects.all()
    serializer_class = VoteWeightStyleSerializer
    filterset_class = filtersets.VoteWeightStyleFilterSet


class AgendaVoteSessionViewSet(NetBoxModelViewSet):
    queryset = models.AgendaVoteSession.objects.select_related("agenda_item", "agenda_item__meeting")
    serializer_class = AgendaVoteSessionSerializer
    filterset_class = filtersets.AgendaVoteSessionFilterSet


class AgendaVoteBallotViewSet(NetBoxModelViewSet):
    queryset = models.AgendaVoteBallot.objects.select_related("session", "session__agenda_item")
    serializer_class = AgendaVoteBallotSerializer
    filterset_class = filtersets.AgendaVoteBallotFilterSet


class MeetingMinutesViewSet(NetBoxModelViewSet):
    queryset = models.MeetingMinutes.objects.select_related("meeting", "approved_by")
    serializer_class = MeetingMinutesSerializer
    filterset_class = filtersets.MeetingMinutesFilterSet


class MeetingInvitationViewSet(NetBoxModelViewSet):
    queryset = models.MeetingInvitation.objects.select_related("meeting", "owner")
    serializer_class = MeetingInvitationSerializer
    filterset_class = filtersets.MeetingInvitationFilterSet
