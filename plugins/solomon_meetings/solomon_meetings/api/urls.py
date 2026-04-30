from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("meeting-types", views.MeetingTypeViewSet)
router.register("meetings", views.MeetingViewSet)
router.register("agenda-items", views.AgendaItemViewSet)
router.register("attendance", views.MeetingAttendanceViewSet)
router.register("owner-snapshots", views.MeetingOwnerSnapshotViewSet)
router.register("attendance-events", views.MeetingAttendanceEventViewSet)
router.register("votes", views.VoteViewSet)
router.register("vote-weight-styles", views.VoteWeightStyleViewSet)
router.register("vote-sessions", views.AgendaVoteSessionViewSet)
router.register("vote-ballots", views.AgendaVoteBallotViewSet)
router.register("minutes", views.MeetingMinutesViewSet)
router.register("invitations", views.MeetingInvitationViewSet)

urlpatterns = router.urls
