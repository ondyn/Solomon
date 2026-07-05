import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from solomon_meetings.models import (
    AGENDA_RESULT_APPROVED,
    ATTENDANCE_EVENT_ARRIVAL,
    ATTENDANCE_EVENT_DEPARTURE,
    MEETING_PHASE_IN_PROGRESS,
    QUORUM_TYPE_BY_SHARE,
    AgendaItem,
    AgendaVoteBallot,
    AgendaVoteSession,
    Meeting,
    MeetingAttendanceEvent,
    MeetingOwnerSnapshot,
    MeetingType,
    VoteWeightStyle,
)
from solomon_meetings.views import MeetingExportView, MeetingView
from solomon_property.models import Building, BuildingObject, Flat, FlatOwner, PropertyOwner


class MeetingViewAttendanceRowsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="moderator")
        self.building_object = BuildingObject.objects.create(name="View Building Object")
        self.building = Building.objects.create(
            building_object=self.building_object,
            name="View Building",
            street="View",
            house_number="11",
            city="Praha",
            postal_code="10000",
        )
        self.owner = PropertyOwner.objects.create(display_name="Owner Grouped")
        self.flat_a = Flat.objects.create(building=self.building, flat_number="1A")
        self.flat_b = Flat.objects.create(building=self.building, flat_number="1B")
        self.flat_owner_a = FlatOwner.objects.create(
            flat=self.flat_a,
            owner=self.owner,
            share_numerator=1,
            share_denominator=3,
            effective_from=datetime.date(2020, 1, 1),
        )
        self.flat_owner_b = FlatOwner.objects.create(
            flat=self.flat_b,
            owner=self.owner,
            share_numerator=1,
            share_denominator=6,
            effective_from=datetime.date(2020, 1, 1),
        )
        self.meeting_type = MeetingType.objects.create(
            name="View Type",
            quorum_type="BY_SHARE",
            default_quorum_threshold=Decimal("0.5"),
        )
        self.meeting = Meeting.objects.create(
            meeting_type=self.meeting_type,
            title="View Meeting",
            date_time=timezone.now(),
            location="Hall",
            moderator=self.user,
            phase=MEETING_PHASE_IN_PROGRESS,
            quorum_threshold=Decimal("0.5"),
        )
        self.meeting.buildings.add(self.building)

        snapshot_time = timezone.now()
        self.snapshot_a = MeetingOwnerSnapshot.objects.create(
            meeting=self.meeting,
            owner=self.owner,
            flat_owner=self.flat_owner_a,
            owner_display_name=self.owner.display_name,
            flat_label=str(self.flat_a),
            share_numerator=1,
            share_denominator=3,
            share_value=Decimal("0.333333"),
            unit_count=1,
            snapshot_taken_at=snapshot_time,
        )
        self.snapshot_b = MeetingOwnerSnapshot.objects.create(
            meeting=self.meeting,
            owner=self.owner,
            flat_owner=self.flat_owner_b,
            owner_display_name=self.owner.display_name,
            flat_label=str(self.flat_b),
            share_numerator=1,
            share_denominator=6,
            share_value=Decimal("0.166667"),
            unit_count=1,
            snapshot_taken_at=snapshot_time,
        )

    def test_attendance_rows_group_by_owner_and_show_fraction_share(self):
        MeetingAttendanceEvent.objects.create(
            owner_snapshot=self.snapshot_a,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=timezone.now(),
            source="test",
        )

        request = RequestFactory().get("/plugins/meetings/meetings/1/attendance/")
        context = MeetingView().get_extra_context(request, self.meeting)

        self.assertEqual(len(context["attendance_rows"]), 1)
        row = context["attendance_rows"][0]
        self.assertEqual(row["owner_display_name"], "Owner Grouped")
        self.assertIn("1A", row["flat_label"])
        self.assertIn("1B", row["flat_label"])
        self.assertEqual(row["share_fraction"], "3/6")
        self.assertTrue(row["is_currently_present"])
        self.assertEqual(context["present_count"], 1)
        self.assertEqual(context["total_count"], 1)
        self.assertEqual(context["present_share"], "3/6")
        self.assertEqual(context["total_share"], "3/6")
        self.assertEqual(context["present_share_ratio_percent"], Decimal("50"))
        self.assertEqual(len(context["attendance_threshold_checks"]), 2)
        self.assertTrue(context["attendance_threshold_checks"][0]["is_met"])
        self.assertFalse(context["attendance_threshold_checks"][1]["is_met"])

    def test_attendance_rows_use_current_vote_weight_style_colors(self):
        VoteWeightStyle.objects.create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.333333"),
            label="Blue",
            color="#1976d2",
        )
        VoteWeightStyle.objects.create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.166667"),
            label="Green",
            color="#2e7d32",
        )

        request = RequestFactory().get("/plugins/meetings/meetings/1/attendance/")
        context = MeetingView().get_extra_context(request, self.meeting)

        self.assertEqual(len(context["attendance_rows"]), 1)
        row = context["attendance_rows"][0]
        self.assertEqual(row["ballot_label"], "Multiple")
        self.assertEqual(row["ballot_color"], "")


class MeetingExportViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="export-user")
        self.building_object = BuildingObject.objects.create(name="Export Building Object")
        self.building = Building.objects.create(
            building_object=self.building_object,
            name="Export Building",
            street="Export",
            house_number="22",
            city="Praha",
            postal_code="10000",
        )
        self.owner = PropertyOwner.objects.create(display_name="Export Owner")
        self.flat = Flat.objects.create(building=self.building, flat_number="2A")
        self.flat_owner = FlatOwner.objects.create(
            flat=self.flat,
            owner=self.owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2020, 1, 1),
        )
        self.meeting_type = MeetingType.objects.create(
            name="Export Type",
            quorum_type=QUORUM_TYPE_BY_SHARE,
            default_quorum_threshold=Decimal("0.5"),
        )
        self.meeting = Meeting.objects.create(
            meeting_type=self.meeting_type,
            title="Export Meeting",
            date_time=timezone.now(),
            location="Main Hall",
            moderator=self.user,
            phase=MEETING_PHASE_IN_PROGRESS,
            quorum_threshold=Decimal("0.5"),
        )
        self.meeting.buildings.add(self.building)

        snapshot_time = timezone.now()
        self.snapshot = MeetingOwnerSnapshot.objects.create(
            meeting=self.meeting,
            owner=self.owner,
            flat_owner=self.flat_owner,
            owner_display_name=self.owner.display_name,
            flat_label=str(self.flat),
            share_numerator=1,
            share_denominator=2,
            share_value=Decimal("0.500000"),
            unit_count=1,
            snapshot_taken_at=snapshot_time,
        )

    def test_export_contains_percentages_and_attendance_timing_and_shares(self):
        arrived_at = timezone.now()
        left_at = arrived_at + datetime.timedelta(minutes=30)
        session_started_at = arrived_at + datetime.timedelta(minutes=5)

        MeetingAttendanceEvent.objects.create(
            owner_snapshot=self.snapshot,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=arrived_at,
            source="test",
        )
        MeetingAttendanceEvent.objects.create(
            owner_snapshot=self.snapshot,
            event_type=ATTENDANCE_EVENT_DEPARTURE,
            event_time=left_at,
            source="test",
        )

        agenda_item = AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title="Export Resolution",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.5"),
            quorum_threshold=Decimal("0.5"),
        )
        session = AgendaVoteSession.objects.create(agenda_item=agenda_item, started_at=session_started_at)
        AgendaVoteBallot.objects.create(
            session=session,
            label="A",
            color="#0055AA",
            share_value=Decimal("0.500000"),
            issued_count=1,
            for_count=1,
            against_count=0,
            abstain_count=0,
        )
        result = session.finalize()
        self.assertEqual(result, AGENDA_RESULT_APPROVED)

        request = RequestFactory().post(
            "/plugins/meetings/meetings/1/export/",
            data={
                "include_attendance": "on",
                "include_voting": "on",
                "include_agenda_texts": "on",
            },
        )

        response = MeetingExportView.as_view()(request, pk=self.meeting.pk)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn("Attendance snapshots", content)
        self.assertIn("First arrived:", content)
        self.assertIn("Last left:", content)
        self.assertIn("Attendance event timeline", content)
        self.assertIn("Share: 1/2 (0.500000)", content)
        self.assertIn("Attendance share at vote start:", content)
        self.assertIn("Totals (weighted share): For 0.500000 (100.00%)", content)
        self.assertIn("Against 0.000000 (0.00%)", content)
        self.assertIn("Abstain 0.000000 (0.00%)", content)
