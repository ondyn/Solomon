import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from solomon_meetings.models import (
    ATTENDANCE_EVENT_ARRIVAL,
    ATTENDANCE_EVENT_DEPARTURE,
    AGENDA_RESULT_APPROVED,
    AGENDA_RESULT_REJECTED,
    MEETING_PHASE_IN_PROGRESS,
    QUORUM_TYPE_BY_SHARE,
    QUORUM_TYPE_BY_UNITS,
    VOTE_AGAINST,
    VOTE_FOR,
    AgendaItem,
    AgendaVoteBallot,
    AgendaVoteSession,
    Meeting,
    MeetingAttendance,
    MeetingAttendanceEvent,
    MeetingOwnerSnapshot,
    MeetingType,
    Vote,
    VoteWeightStyle,
)
from solomon_property.models import Building, BuildingObject, Flat, FlatOwner, PropertyOwner


class MeetingModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="moderator")
        self.building_object = BuildingObject.objects.create(name="SO Test")
        self.building = Building.objects.create(
            building_object=self.building_object,
            name="Test Building",
            street="Test",
            house_number="1",
            city="Praha",
            postal_code="10000",
        )
        self.flat = Flat.objects.create(building=self.building, flat_number="1A")
        self.owner = PropertyOwner.objects.create(display_name="Owner A")
        self.flat_owner = FlatOwner.objects.create(
            flat=self.flat,
            owner=self.owner,
            share_numerator=1,
            share_denominator=1,
            effective_from=datetime.date(2020, 1, 1),
        )

    def _meeting(self, quorum_type=QUORUM_TYPE_BY_SHARE, threshold=Decimal("0.5")):
        meeting_type = MeetingType.objects.create(
            name=f"Type {quorum_type}",
            quorum_type=quorum_type,
            default_quorum_threshold=Decimal("0.5"),
        )
        meeting = Meeting.objects.create(
            meeting_type=meeting_type,
            title="Annual Meeting",
            date_time=timezone.now(),
            location="Hall",
            moderator=self.user,
            quorum_threshold=threshold,
        )
        meeting.buildings.add(self.building)
        return meeting

    def test_calculate_quorum_ratio_by_share(self):
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE)
        MeetingAttendance.objects.create(
            meeting=meeting,
            owner=self.owner,
            flat_owner=self.flat_owner,
        )
        ratio = meeting.calculate_quorum_ratio()
        self.assertEqual(ratio, Decimal("1"))

    def test_calculate_quorum_ratio_by_units(self):
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_UNITS)
        MeetingAttendance.objects.create(
            meeting=meeting,
            owner=self.owner,
            flat_owner=self.flat_owner,
        )
        ratio = meeting.calculate_quorum_ratio()
        self.assertEqual(ratio, Decimal("1"))

    def test_refresh_quorum_sets_fields(self):
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE, threshold=Decimal("0.75"))
        MeetingAttendance.objects.create(
            meeting=meeting,
            owner=self.owner,
            flat_owner=self.flat_owner,
        )
        ratio = meeting.refresh_quorum()
        meeting.refresh_from_db()
        self.assertEqual(ratio, Decimal("1"))
        self.assertTrue(meeting.quorum_achieved)
        self.assertIsNotNone(meeting.quorum_updated_at)

    def test_closed_meeting_without_quorum_fails_validation(self):
        meeting = self._meeting()
        meeting.status = "CLOSED"
        with self.assertRaises(ValidationError):
            meeting.full_clean()

    def test_start_meeting_creates_owner_snapshots(self):
        VoteWeightStyle.objects.update_or_create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("1.0"),
            defaults={
                "label": "A",
                "color": "#0055AA",
                "is_current": True,
            },
        )
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE)
        started_at = timezone.now()

        meeting.start_meeting(started_at=started_at)

        meeting.refresh_from_db()
        snapshot = MeetingOwnerSnapshot.objects.get(meeting=meeting, flat_owner=self.flat_owner)
        self.assertEqual(meeting.phase, MEETING_PHASE_IN_PROGRESS)
        self.assertEqual(snapshot.ballot_label, "A")
        self.assertEqual(snapshot.ballot_color, "#0055AA")
        self.assertEqual(snapshot.share_value, Decimal("1"))
        self.assertEqual(snapshot.snapshot_taken_at, started_at)

    def test_attendance_events_support_multiple_arrivals_and_departures(self):
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE)
        start_time = timezone.now()
        meeting.start_meeting(started_at=start_time)
        snapshot = MeetingOwnerSnapshot.objects.get(meeting=meeting, flat_owner=self.flat_owner)

        first_arrival = start_time + datetime.timedelta(minutes=5)
        first_departure = start_time + datetime.timedelta(minutes=20)
        second_arrival = start_time + datetime.timedelta(minutes=35)

        MeetingAttendanceEvent.objects.create(
            owner_snapshot=snapshot,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=first_arrival,
        )
        MeetingAttendanceEvent.objects.create(
            owner_snapshot=snapshot,
            event_type=ATTENDANCE_EVENT_DEPARTURE,
            event_time=first_departure,
        )
        MeetingAttendanceEvent.objects.create(
            owner_snapshot=snapshot,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=second_arrival,
        )

        snapshot.refresh_from_db()
        self.assertTrue(snapshot.is_present_at(first_arrival + datetime.timedelta(minutes=1)))
        self.assertFalse(snapshot.is_present_at(first_departure + datetime.timedelta(minutes=1)))
        self.assertTrue(snapshot.is_present_at(second_arrival + datetime.timedelta(minutes=1)))

    def test_arrival_event_updates_quorum_even_if_representation_is_absent(self):
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE)
        start_time = timezone.now()
        meeting.start_meeting(started_at=start_time)
        snapshot = MeetingOwnerSnapshot.objects.get(meeting=meeting, flat_owner=self.flat_owner)

        self.assertEqual(snapshot.representation, "ABSENT")
        self.assertEqual(meeting.calculate_quorum_ratio(), Decimal("0"))

        MeetingAttendanceEvent.objects.create(
            owner_snapshot=snapshot,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=start_time + datetime.timedelta(minutes=1),
        )

        meeting.refresh_from_db()
        self.assertEqual(meeting.calculate_quorum_ratio(), Decimal("1"))

    def test_ballot_summary_aggregates_multi_flat_owner_into_single_holder_share(self):
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE)

        owner_multi = PropertyOwner.objects.create(display_name="Owner Multi")
        owner_single = PropertyOwner.objects.create(display_name="Owner Single")

        flat_multi_a = Flat.objects.create(building=self.building, flat_number="2A")
        flat_multi_b = Flat.objects.create(building=self.building, flat_number="2B")
        flat_single = Flat.objects.create(building=self.building, flat_number="3A")

        FlatOwner.objects.create(
            flat=flat_multi_a,
            owner=owner_multi,
            share_numerator=1,
            share_denominator=4,
            effective_from=datetime.date(2020, 1, 1),
        )
        FlatOwner.objects.create(
            flat=flat_multi_b,
            owner=owner_multi,
            share_numerator=1,
            share_denominator=5,
            effective_from=datetime.date(2020, 1, 1),
        )
        FlatOwner.objects.create(
            flat=flat_single,
            owner=owner_single,
            share_numerator=9,
            share_denominator=20,
            effective_from=datetime.date(2020, 1, 1),
        )

        meeting.snapshot_owners(started_at=timezone.now())
        meeting.owner_snapshots.update(
            is_currently_present=True,
            first_arrived_at=timezone.now(),
            last_left_at=None,
        )

        summary = meeting.get_ballot_type_summary()
        rows_by_fraction = {row["share_fraction"]: row for row in summary}

        # 1/4 + 1/5 == 9/20, so both holders must collapse under one share row.
        self.assertIn("9/20", rows_by_fraction)
        self.assertEqual(rows_by_fraction["9/20"]["owner_count"], 2)
        self.assertEqual(rows_by_fraction["9/20"]["issued_count"], 2)

        # Component shares must not appear as separate holder rows.
        self.assertNotIn("1/4", rows_by_fraction)
        self.assertNotIn("1/5", rows_by_fraction)

    def test_ballot_summary_and_quorum_remain_stable_after_ownership_change(self):
        VoteWeightStyle.objects.update_or_create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("1.0"),
            defaults={
                "label": "A",
                "color": "#0055AA",
                "is_current": True,
            },
        )
        meeting = self._meeting(quorum_type=QUORUM_TYPE_BY_SHARE)
        started_at = timezone.now()
        meeting.start_meeting(started_at=started_at)

        snapshot = MeetingOwnerSnapshot.objects.get(meeting=meeting, flat_owner=self.flat_owner)
        MeetingAttendanceEvent.objects.create(
            owner_snapshot=snapshot,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=started_at + datetime.timedelta(minutes=1),
            source="test",
        )

        # Simulate ownership/style changes after voting history already exists.
        self.flat_owner.share_numerator = 1
        self.flat_owner.share_denominator = 2
        self.flat_owner.save(update_fields=["share_numerator", "share_denominator", "last_updated"])
        VoteWeightStyle.objects.filter(voting_method=QUORUM_TYPE_BY_SHARE, weight_value=Decimal("1.0")).update(
            label="Changed",
            color="#AA0000",
        )
        VoteWeightStyle.objects.update_or_create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.5"),
            defaults={
                "label": "B",
                "color": "#00AA55",
                "is_current": True,
            },
        )

        summary = meeting.get_ballot_type_summary()
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["share_fraction"], "1/1")
        self.assertEqual(summary[0]["label"], "A")
        self.assertEqual(summary[0]["color"], "#0055AA")
        self.assertEqual(meeting.calculate_quorum_ratio(), Decimal("1"))

    def test_sync_current_share_styles_marks_missing_shares_as_historical(self):
        stale_style = VoteWeightStyle.objects.create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.750000"),
            label="Stale",
            color="#333333",
            is_current=True,
        )

        created, current_count = VoteWeightStyle.sync_current_share_styles()

        stale_style.refresh_from_db()
        self.assertFalse(stale_style.is_current)
        self.assertEqual(current_count, 1)
        self.assertGreaterEqual(created, 0)
        self.assertTrue(
            VoteWeightStyle.objects.filter(
                voting_method=QUORUM_TYPE_BY_SHARE,
                weight_value=Decimal("1.000000"),
                is_current=True,
            ).exists()
        )

    def test_flat_owner_change_triggers_automatic_vote_style_sync(self):
        stale_style = VoteWeightStyle.objects.create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.750000"),
            label="Old",
            color="#333333",
            is_current=True,
        )

        self.flat_owner.share_numerator = 1
        self.flat_owner.share_denominator = 2
        self.flat_owner.save(update_fields=["share_numerator", "share_denominator", "last_updated"])

        stale_style.refresh_from_db()
        self.assertFalse(stale_style.is_current)
        self.assertTrue(
            VoteWeightStyle.objects.filter(
                voting_method=QUORUM_TYPE_BY_SHARE,
                weight_value=Decimal("0.500000"),
                is_current=True,
            ).exists()
        )

    def test_historical_vote_style_is_not_editable(self):
        historical_style = VoteWeightStyle.objects.create(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.250000"),
            label="H1",
            color="#111111",
            is_current=False,
        )

        historical_style.label = "H2"
        with self.assertRaises(ValidationError):
            historical_style.save()


class VotingModelTests(TestCase):
    def setUp(self):
        self.building_object = BuildingObject.objects.create(name="SO Vote")
        self.building = Building.objects.create(
            building_object=self.building_object,
            name="Vote Building",
            street="Vote",
            house_number="10",
            city="Praha",
            postal_code="10000",
        )
        self.flat = Flat.objects.create(building=self.building, flat_number="2A")
        self.owner = PropertyOwner.objects.create(display_name="Owner Vote")
        self.flat_owner = FlatOwner.objects.create(
            flat=self.flat,
            owner=self.owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2020, 1, 1),
        )
        self.meeting_type = MeetingType.objects.create(
            name="Vote Type",
            quorum_type=QUORUM_TYPE_BY_SHARE,
            default_quorum_threshold=Decimal("0.5"),
        )
        self.meeting = Meeting.objects.create(
            meeting_type=self.meeting_type,
            title="Vote Meeting",
            date_time=timezone.now(),
            quorum_threshold=Decimal("0.5"),
        )
        self.meeting.buildings.add(self.building)
        self.attendance = MeetingAttendance.objects.create(
            meeting=self.meeting,
            owner=self.owner,
            flat_owner=self.flat_owner,
        )

    def test_vote_sets_weight_from_share(self):
        agenda = AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title="Resolution",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.5"),
        )
        vote = Vote.objects.create(agenda_item=agenda, attendance=self.attendance, vote=VOTE_FOR)
        self.assertEqual(vote.vote_weight, Decimal("0.5"))

    def test_vote_attendance_must_match_meeting(self):
        other_type = MeetingType.objects.create(
            name="Other",
            quorum_type=QUORUM_TYPE_BY_SHARE,
            default_quorum_threshold=Decimal("0.5"),
        )
        other_meeting = Meeting.objects.create(
            meeting_type=other_type,
            title="Other meeting",
            date_time=timezone.now(),
            quorum_threshold=Decimal("0.5"),
        )
        other_meeting.buildings.add(self.building)

        agenda = AgendaItem.objects.create(
            meeting=other_meeting,
            order=1,
            title="Other resolution",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.5"),
        )
        vote = Vote(agenda_item=agenda, attendance=self.attendance, vote=VOTE_FOR)
        with self.assertRaises(ValidationError):
            vote.full_clean()

    def test_agenda_resolve_result(self):
        agenda = AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title="Resolution",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.5"),
        )
        Vote.objects.create(agenda_item=agenda, attendance=self.attendance, vote=VOTE_FOR)
        result = agenda.resolve_result()
        self.assertEqual(result, AGENDA_RESULT_APPROVED)

    def test_agenda_resolve_result_negative_form(self):
        agenda = AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title="Resolution",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.75"),
        )
        Vote.objects.create(agenda_item=agenda, attendance=self.attendance, vote=VOTE_AGAINST)
        result = agenda.resolve_result(negative_form=True)
        self.assertEqual(result, AGENDA_RESULT_REJECTED)

    def test_ballot_row_completes_third_value(self):
        agenda = AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title="Ballot completion",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.5"),
            quorum_threshold=Decimal("0.5"),
        )
        session = AgendaVoteSession.objects.create(agenda_item=agenda)
        row = AgendaVoteBallot(
            session=session,
            label="A",
            color="#0055AA",
            share_value=Decimal("0.5"),
            issued_count=4,
            against_count=1,
            abstain_count=1,
        )

        row.full_clean()

        self.assertEqual(row.for_count, 2)

    def test_vote_session_finalize_uses_ballot_rows(self):
        self.meeting.start_meeting(started_at=timezone.now())
        snapshot = MeetingOwnerSnapshot.objects.get(meeting=self.meeting, flat_owner=self.flat_owner)
        MeetingAttendanceEvent.objects.create(
            owner_snapshot=snapshot,
            event_type=ATTENDANCE_EVENT_ARRIVAL,
            event_time=timezone.now(),
        )

        agenda = AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title="Resolution",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.5"),
            quorum_threshold=Decimal("0.5"),
        )
        session = AgendaVoteSession.objects.create(agenda_item=agenda)
        AgendaVoteBallot.objects.create(
            session=session,
            label="A",
            color="#0055AA",
            share_value=Decimal("0.5"),
            issued_count=1,
            for_count=1,
        )

        result = session.finalize()

        self.assertEqual(result, AGENDA_RESULT_APPROVED)
        agenda.refresh_from_db()
        self.assertEqual(agenda.result, AGENDA_RESULT_APPROVED)
