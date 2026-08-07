import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from solomon_meetings.forms import AgendaVoteSessionForm
from solomon_meetings.models import (
    AGENDA_RESULT_APPROVED,
    QUORUM_TYPE_BY_SHARE,
    QUORUM_TYPE_BY_UNITS,
    AgendaItem,
    AgendaVoteBallot,
    AgendaVoteSession,
    Meeting,
    MeetingAttendance,
    MeetingType,
    Vote,
    VoteWeightStyle,
    VOTE_FOR,
)
from solomon_meetings.views import MeetingView
from solomon_property.models import (
    Building,
    BuildingObject,
    Flat,
    FlatOwner,
    PropertyOwner,
)


REPORT_BALLOTS = [
    ("Červená", "#d32f2f", Decimal("0.945"), 6, 5),
    ("Modrá", "#1976d2", Decimal("0.880"), 5, 5),
    ("Sv. modrá", "#64b5f6", Decimal("0.820"), 2, 2),
    ("Sv. zelená", "#81c784", Decimal("0.793"), 2, 1),
    ("Bílá", "#f5f5f5", Decimal("0.779"), 29, 20),
    ("Fialová", "#7b1fa2", Decimal("0.776"), 6, 3),
    ("Růžová", "#ec407a", Decimal("0.467"), 1, 1),
    ("Zelená", "#388e3c", Decimal("0.438"), 14, 7),
    ("Oranžová", "#f57c00", Decimal("0.330"), 2, 2),
    ("Žlutá", "#fbc02d", Decimal("0.309"), 13, 9),
    ("Šedá", "#616161", Decimal("1.318"), 1, 1),
    ("Sv. Žlutá", "#fff176", Decimal("1.397"), 1, 1),
]


class MeetingReportSpreadsheetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="moderator")
        self.building_object = BuildingObject.objects.create(
            name="Report Building Object"
        )
        self.building = Building.objects.create(
            building_object=self.building_object,
            name="Report Building",
            street="Report",
            house_number="1",
            city="Praha",
            postal_code="10000",
        )
        self.meeting_type = MeetingType.objects.create(
            name="Report Type",
            quorum_type=QUORUM_TYPE_BY_SHARE,
            default_quorum_threshold=Decimal("0.5"),
        )
        self.meeting = Meeting.objects.create(
            meeting_type=self.meeting_type,
            title="Report Meeting",
            date_time=timezone.now(),
            location="Hall",
            moderator=self.user,
            quorum_threshold=Decimal("0.5"),
        )
        self.meeting.buildings.add(self.building)

        self.groups = self._create_report_fixtures()

    def _create_report_fixtures(self):
        groups = {}
        for index, (label, color, share_value, total_count, present_count) in enumerate(
            REPORT_BALLOTS, start=1
        ):
            VoteWeightStyle.objects.create(
                voting_method=QUORUM_TYPE_BY_SHARE,
                weight_value=share_value,
                label=label,
                color=color,
            )

            holders = []
            for holder_index in range(1, total_count + 1):
                owner = PropertyOwner.objects.create(
                    display_name=f"{label} owner {holder_index}",
                )
                flat = Flat.objects.create(
                    building=self.building,
                    flat_number=f"{index:02d}-{holder_index:02d}",
                )
                flat_owner = FlatOwner.objects.create(
                    flat=flat,
                    owner=owner,
                    share_numerator=int(share_value * 1000),
                    share_denominator=1000,
                    effective_from=datetime.date(2020, 1, 1),
                )
                holders.append((owner, flat_owner))

            groups[label] = {
                "label": label,
                "color": color,
                "share_value": share_value,
                "total_count": total_count,
                "present_count": present_count,
                "holders": holders,
            }

        self.meeting.start_meeting(started_at=timezone.now())

        for group in groups.values():
            for owner, flat_owner in group["holders"][: group["present_count"]]:
                MeetingAttendance.objects.create(
                    meeting=self.meeting,
                    owner=owner,
                    flat_owner=flat_owner,
                )

        return groups

    def _ballot_rows_from_counts(self, overrides=None):
        overrides = overrides or {}
        rows = []
        for label, color, share_value, total_count, present_count in REPORT_BALLOTS:
            issued_count = overrides.get(label, present_count)
            rows.append(
                {
                    "label": label,
                    "color": color,
                    "share_value": share_value,
                    "issued_count": issued_count,
                    "for_count": issued_count,
                }
            )
        return rows

    def _record_vote_session(self, agenda_item, rows, negative_form=False):
        data = {
            "rows": str(len(rows)),
        }
        if negative_form:
            data["negative_form"] = "on"

        for index, row in enumerate(rows):
            data[f"row-{index}-label"] = row.get("label", "")
            data[f"row-{index}-color"] = row.get("color", "")
            data[f"row-{index}-share_value"] = str(row["share_value"])
            data[f"row-{index}-issued_count"] = str(row["issued_count"])
            if row.get("for_count") is not None:
                data[f"row-{index}-for_count"] = str(row["for_count"])
            if row.get("against_count") is not None:
                data[f"row-{index}-against_count"] = str(row["against_count"])
            if row.get("abstain_count") is not None:
                data[f"row-{index}-abstain_count"] = str(row["abstain_count"])

        form = AgendaVoteSessionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

        session = AgendaVoteSession.objects.create(
            agenda_item=agenda_item,
            negative_form=negative_form,
        )
        for row in form.cleaned_data["parsed_rows"]:
            AgendaVoteBallot.objects.create(
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
        return session

    def _meeting_context(self):
        request = RequestFactory().get(f"{self.meeting.get_absolute_url()}agenda/")
        return MeetingView().get_extra_context(request, self.meeting)

    def _agenda_item(self, title):
        return AgendaItem.objects.create(
            meeting=self.meeting,
            order=1,
            title=title,
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_SHARE,
            minimum_pass_percentage=Decimal("0.6667"),
            quorum_threshold=Decimal("0.5"),
        )

    def test_report_fixture_matches_share_summary_and_recomputes_after_extra_attendance(
        self,
    ):
        agenda_item = self._agenda_item("Report resolution")

        first_session = self._record_vote_session(
            agenda_item, self._ballot_rows_from_counts()
        )
        context = self._meeting_context()
        rows_by_label = {row["label"]: row for row in context["ballot_type_summary"]}

        self.assertEqual(context["present_count"], 57)
        self.assertEqual(context["total_count"], 82)
        self.assertEqual(context["present_share"], "39155/1000")
        self.assertEqual(context["total_share"], "54534/1000")
        self.assertEqual(
            context["quorum_ratio_percent"].quantize(Decimal("0.01")), Decimal("71.80")
        )
        self.assertEqual(rows_by_label["Bílá"]["owner_count"], 29)
        self.assertEqual(rows_by_label["Bílá"]["issued_count"], 20)
        self.assertEqual(rows_by_label["Červená"]["owner_count"], 6)
        self.assertEqual(rows_by_label["Červená"]["issued_count"], 5)

        self.assertEqual(first_session.present_weight, Decimal("39.155000"))
        self.assertTrue(first_session.quorum_met)
        self.assertEqual(first_session.result, AGENDA_RESULT_APPROVED)

        latest_session = context["agenda_items"][0].latest_vote_session
        self.assertIsNotNone(latest_session)
        self.assertEqual(latest_session.present_weight, Decimal("39.155000"))
        self.assertEqual(
            context["agenda_items"][0]
            .latest_vote_percentages["for"]
            .quantize(Decimal("0.01")),
            Decimal("100.00"),
        )

        white_group = self.groups["Bílá"]
        extra_owner, extra_flat_owner = white_group["holders"][
            white_group["present_count"]
        ]
        MeetingAttendance.objects.create(
            meeting=self.meeting,
            owner=extra_owner,
            flat_owner=extra_flat_owner,
        )

        second_session = self._record_vote_session(
            agenda_item,
            self._ballot_rows_from_counts(overrides={"Bílá": 21}),
        )
        context = self._meeting_context()
        rows_by_label = {row["label"]: row for row in context["ballot_type_summary"]}

        self.assertEqual(context["present_count"], 58)
        self.assertEqual(context["total_count"], 82)
        self.assertEqual(context["present_share"], "39934/1000")
        self.assertEqual(context["total_share"], "54534/1000")
        self.assertEqual(
            context["quorum_ratio_percent"].quantize(Decimal("0.01")), Decimal("73.23")
        )
        self.assertEqual(rows_by_label["Bílá"]["issued_count"], 21)

        self.assertEqual(second_session.present_weight, Decimal("39.934000"))
        self.assertTrue(second_session.quorum_met)
        self.assertEqual(second_session.result, AGENDA_RESULT_APPROVED)

        latest_session = context["agenda_items"][0].latest_vote_session
        self.assertIsNotNone(latest_session)
        self.assertEqual(latest_session.present_weight, Decimal("39.934000"))
        self.assertEqual(
            context["agenda_items"][0]
            .latest_vote_percentages["for"]
            .quantize(Decimal("0.01")),
            Decimal("100.00"),
        )

    def test_negative_form_session_reconstructs_for_votes_from_remainder(self):
        agenda_item = self._agenda_item("Negative form resolution")
        session = self._record_vote_session(
            agenda_item,
            [
                {
                    "label": "A",
                    "color": "#0055AA",
                    "share_value": Decimal("1.000000"),
                    "issued_count": 4,
                    "against_count": 1,
                    "abstain_count": 0,
                }
            ],
            negative_form=True,
        )

        self.assertEqual(session.present_weight, Decimal("4.000000"))
        self.assertEqual(session.totals_by_role()["FOR"], Decimal("3.000000"))
        self.assertEqual(session.result, AGENDA_RESULT_APPROVED)
        self.assertEqual(session.agenda_item.result, AGENDA_RESULT_APPROVED)

    def test_vote_weight_by_units_uses_one_ballot_weight(self):
        meeting_type = MeetingType.objects.create(
            name="Units Type",
            quorum_type=QUORUM_TYPE_BY_UNITS,
            default_quorum_threshold=Decimal("0.5"),
        )
        meeting = Meeting.objects.create(
            meeting_type=meeting_type,
            title="Units Meeting",
            date_time=timezone.now(),
            quorum_threshold=Decimal("0.5"),
        )
        meeting.buildings.add(self.building)

        owner = PropertyOwner.objects.create(display_name="Units Owner")
        flat = Flat.objects.create(building=self.building, flat_number="99A")
        flat_owner = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2020, 1, 1),
        )
        attendance = MeetingAttendance.objects.create(
            meeting=meeting,
            owner=owner,
            flat_owner=flat_owner,
        )

        agenda_item = AgendaItem.objects.create(
            meeting=meeting,
            order=1,
            title="Units vote",
            voting_required=True,
            voting_method=QUORUM_TYPE_BY_UNITS,
            minimum_pass_percentage=Decimal("0.5"),
            quorum_threshold=Decimal("0.5"),
        )

        vote = Vote.objects.create(
            agenda_item=agenda_item, attendance=attendance, vote=VOTE_FOR
        )

        self.assertEqual(vote.vote_weight, Decimal("1"))
