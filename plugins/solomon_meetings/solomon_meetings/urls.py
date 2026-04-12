from django.urls import path

from netbox.views.generic import ObjectChangeLogView

from . import models, views

urlpatterns = [
    path("meeting-types/", views.MeetingTypeListView.as_view(), name="meetingtype_list"),
    path("meeting-types/add/", views.MeetingTypeEditView.as_view(), name="meetingtype_add"),
    path("meeting-types/delete/", views.MeetingTypeBulkDeleteView.as_view(), name="meetingtype_bulk_delete"),
    path("meeting-types/<int:pk>/", views.MeetingTypeView.as_view(), name="meetingtype"),
    path("meeting-types/<int:pk>/edit/", views.MeetingTypeEditView.as_view(), name="meetingtype_edit"),
    path("meeting-types/<int:pk>/delete/", views.MeetingTypeDeleteView.as_view(), name="meetingtype_delete"),
    path(
        "meeting-types/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="meetingtype_changelog",
        kwargs={"model": models.MeetingType},
    ),

    path("meetings/", views.MeetingListView.as_view(), name="meeting_list"),
    path("meetings/add/", views.MeetingEditView.as_view(), name="meeting_add"),
    path("meetings/delete/", views.MeetingBulkDeleteView.as_view(), name="meeting_bulk_delete"),
    path("meetings/<int:pk>/", views.MeetingView.as_view(), name="meeting"),
    path("meetings/<int:pk>/edit/", views.MeetingEditView.as_view(), name="meeting_edit"),
    path("meetings/<int:pk>/delete/", views.MeetingDeleteView.as_view(), name="meeting_delete"),
    path(
        "meetings/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="meeting_changelog",
        kwargs={"model": models.Meeting},
    ),

    path("agenda-items/", views.AgendaItemListView.as_view(), name="agendaitem_list"),
    path("agenda-items/add/", views.AgendaItemEditView.as_view(), name="agendaitem_add"),
    path("agenda-items/delete/", views.AgendaItemBulkDeleteView.as_view(), name="agendaitem_bulk_delete"),
    path("agenda-items/<int:pk>/", views.AgendaItemView.as_view(), name="agendaitem"),
    path("agenda-items/<int:pk>/edit/", views.AgendaItemEditView.as_view(), name="agendaitem_edit"),
    path("agenda-items/<int:pk>/delete/", views.AgendaItemDeleteView.as_view(), name="agendaitem_delete"),
    path(
        "agenda-items/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="agendaitem_changelog",
        kwargs={"model": models.AgendaItem},
    ),

    path("attendance/", views.MeetingAttendanceListView.as_view(), name="meetingattendance_list"),
    path("attendance/add/", views.MeetingAttendanceEditView.as_view(), name="meetingattendance_add"),
    path("attendance/delete/", views.MeetingAttendanceBulkDeleteView.as_view(), name="meetingattendance_bulk_delete"),
    path("attendance/<int:pk>/", views.MeetingAttendanceView.as_view(), name="meetingattendance"),
    path("attendance/<int:pk>/edit/", views.MeetingAttendanceEditView.as_view(), name="meetingattendance_edit"),
    path("attendance/<int:pk>/delete/", views.MeetingAttendanceDeleteView.as_view(), name="meetingattendance_delete"),
    path(
        "attendance/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="meetingattendance_changelog",
        kwargs={"model": models.MeetingAttendance},
    ),

    path("votes/", views.VoteListView.as_view(), name="vote_list"),
    path("votes/add/", views.VoteEditView.as_view(), name="vote_add"),
    path("votes/delete/", views.VoteBulkDeleteView.as_view(), name="vote_bulk_delete"),
    path("votes/<int:pk>/", views.VoteView.as_view(), name="vote"),
    path("votes/<int:pk>/edit/", views.VoteEditView.as_view(), name="vote_edit"),
    path("votes/<int:pk>/delete/", views.VoteDeleteView.as_view(), name="vote_delete"),
    path(
        "votes/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="vote_changelog",
        kwargs={"model": models.Vote},
    ),

    path("vote-weight-styles/", views.VoteWeightStyleListView.as_view(), name="voteweightstyle_list"),
    path("vote-weight-styles/add/", views.VoteWeightStyleEditView.as_view(), name="voteweightstyle_add"),
    path("vote-weight-styles/delete/", views.VoteWeightStyleBulkDeleteView.as_view(), name="voteweightstyle_bulk_delete"),
    path("vote-weight-styles/<int:pk>/", views.VoteWeightStyleView.as_view(), name="voteweightstyle"),
    path("vote-weight-styles/<int:pk>/edit/", views.VoteWeightStyleEditView.as_view(), name="voteweightstyle_edit"),
    path("vote-weight-styles/<int:pk>/delete/", views.VoteWeightStyleDeleteView.as_view(), name="voteweightstyle_delete"),
    path(
        "vote-weight-styles/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="voteweightstyle_changelog",
        kwargs={"model": models.VoteWeightStyle},
    ),

    path("minutes/", views.MeetingMinutesListView.as_view(), name="meetingminutes_list"),
    path("minutes/add/", views.MeetingMinutesEditView.as_view(), name="meetingminutes_add"),
    path("minutes/delete/", views.MeetingMinutesBulkDeleteView.as_view(), name="meetingminutes_bulk_delete"),
    path("minutes/<int:pk>/", views.MeetingMinutesView.as_view(), name="meetingminutes"),
    path("minutes/<int:pk>/edit/", views.MeetingMinutesEditView.as_view(), name="meetingminutes_edit"),
    path("minutes/<int:pk>/delete/", views.MeetingMinutesDeleteView.as_view(), name="meetingminutes_delete"),
    path(
        "minutes/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="meetingminutes_changelog",
        kwargs={"model": models.MeetingMinutes},
    ),

    path("invitations/", views.MeetingInvitationListView.as_view(), name="meetinginvitation_list"),
    path("invitations/add/", views.MeetingInvitationEditView.as_view(), name="meetinginvitation_add"),
    path("invitations/delete/", views.MeetingInvitationBulkDeleteView.as_view(), name="meetinginvitation_bulk_delete"),
    path("invitations/<int:pk>/", views.MeetingInvitationView.as_view(), name="meetinginvitation"),
    path("invitations/<int:pk>/edit/", views.MeetingInvitationEditView.as_view(), name="meetinginvitation_edit"),
    path("invitations/<int:pk>/delete/", views.MeetingInvitationDeleteView.as_view(), name="meetinginvitation_delete"),
    path(
        "invitations/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="meetinginvitation_changelog",
        kwargs={"model": models.MeetingInvitation},
    ),
]
