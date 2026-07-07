"""Solomon Property - Unit tests for view behavior."""

import datetime

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from solomon_property.models import FlatOwner
from solomon_property.views import FlatView
from solomon_property.views import PersonView

from .test_models import make_building, make_flat, make_owner, make_person


class PersonViewTest(TestCase):
    def test_person_ownership_table_orders_by_effective_from_desc(self):
        person = make_person(first_name="Ondrej", last_name="Hnyk")
        building = make_building(name="Salounova 1")
        flat = make_flat(building, flat_number="101")
        owner = make_owner(display_name="Ondrej Hnyk")
        owner.persons.add(person)

        older = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2023, 1, 1),
        )
        newer = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2024, 1, 1),
        )

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        context = PersonView().get_extra_context(request, person)

        ownership_table = context["ownership_table"]
        ownership_ids = [row.record.pk for row in ownership_table.rows]

        self.assertEqual(ownership_ids, [newer.pk, older.pk])


class FlatViewTest(TestCase):
    def test_ownership_history_orders_by_effective_from_desc(self):
        building = make_building(name="Salounova 1")
        flat = make_flat(building, flat_number="101")
        owner = make_owner(display_name="Ondrej Hnyk")

        older = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2026, 7, 3),
            effective_to=datetime.date(2026, 7, 5),
        )
        middle = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2026, 7, 5),
            effective_to=datetime.date(2026, 7, 6),
        )
        newest = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2026, 7, 7),
        )

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        context = FlatView().get_extra_context(request, flat)

        owner_table = context["owner_table"]
        ownership_ids = [row.record.pk for row in owner_table.rows]

        self.assertEqual(ownership_ids, [newest.pk, middle.pk, older.pk])
