import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from solomon_meetings.models import (
    ATTENDANCE_EVENT_ARRIVAL,
    MEETING_PHASE_IN_PROGRESS,
    Meeting,
    MeetingAttendanceEvent,
    MeetingOwnerSnapshot,
    MeetingType,
)
from solomon_meetings.views import MeetingView
from solomon_property.models import Building, Flat, FlatOwner, PropertyOwner


class MeetingViewAttendanceRowsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="moderator")
        self.building = Building.objects.create(
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
            snapshot=self.snapshot_a,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=timezone.now(),
            source="test",
        )

        request = RequestFactory().get("/plugins/meetings/meetings/1/?tab=attendance")
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
