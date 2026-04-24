"""Solomon Property - Unit tests for model business logic."""

import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from solomon_property.models import (
    Building,
    Flat,
    FlatOwner,
    Person,
    PropertyOwner,
    PropertyTenant,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_building(**kwargs):
    defaults = dict(
        name="Test Building",
        street="Testovací",
        house_number="1",
        city="Praha",
        postal_code="10000",
    )
    defaults.update(kwargs)
    return Building.objects.create(**defaults)


def make_flat(building, **kwargs):
    defaults = dict(flat_number="1A", floor=1, area_m2=Decimal("55.00"))
    defaults.update(kwargs)
    return Flat.objects.create(building=building, **defaults)


def make_person(**kwargs):
    defaults = dict(first_name="Jan", last_name="Novák")
    defaults.update(kwargs)
    return Person.objects.create(**defaults)


def make_owner(**kwargs):
    defaults = dict(display_name="Novák Jan", person_type="natural")
    defaults.update(kwargs)
    return PropertyOwner.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Building tests
# ---------------------------------------------------------------------------

class BuildingModelTest(TestCase):
    def test_str_returns_name_and_address(self):
        b = make_building(name="Dům Na Kopci", street="Kopecká", house_number="5")
        # __str__ returns "name (street house_number)"
        self.assertIn("Dům Na Kopci", str(b))
        self.assertIn("Kopecká", str(b))
        self.assertIn("5", str(b))

    def test_get_absolute_url_contains_pk(self):
        b = make_building()
        url = b.get_absolute_url()
        self.assertIn(str(b.pk), url)
        self.assertIn("buildings", url)

    def test_defaults(self):
        b = make_building()
        self.assertFalse(b.elevator)
        self.assertIsNone(b.year_built)
        # total_units is nullable - default is None (not set)
        self.assertIsNone(b.total_units)


# ---------------------------------------------------------------------------
# Flat tests
# ---------------------------------------------------------------------------

class FlatModelTest(TestCase):
    def setUp(self):
        self.building = make_building()

    def test_str_includes_flat_number_and_building(self):
        flat = make_flat(self.building, flat_number="2B")
        self.assertIn("2B", str(flat))
        self.assertIn(self.building.name, str(flat))

    def test_get_absolute_url_contains_pk(self):
        flat = make_flat(self.building)
        url = flat.get_absolute_url()
        self.assertIn(str(flat.pk), url)

    def test_cuzk_share_defaults_to_none(self):
        flat = make_flat(self.building)
        self.assertIsNone(flat.cuzk_share_numerator)
        self.assertIsNone(flat.cuzk_share_denominator)

    def test_clean_requires_both_cuzk_share_values(self):
        flat = make_flat(self.building, cuzk_share_numerator=3, cuzk_share_denominator=None)
        with self.assertRaises(ValidationError):
            flat.full_clean()

    def test_clean_rejects_cuzk_share_numerator_greater_than_denominator(self):
        flat = make_flat(self.building, cuzk_share_numerator=5, cuzk_share_denominator=4)
        with self.assertRaises(ValidationError):
            flat.full_clean()

    def test_has_complete_current_ownership_true_when_sum_is_one(self):
        flat = make_flat(self.building, flat_number="10A")
        owner1 = make_owner(display_name="Owner 1")
        owner2 = make_owner(display_name="Owner 2")
        FlatOwner.objects.create(
            flat=flat,
            owner=owner1,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2024, 1, 1),
        )
        FlatOwner.objects.create(
            flat=flat,
            owner=owner2,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2024, 1, 1),
        )
        self.assertTrue(flat.has_complete_current_ownership)

    def test_has_complete_current_ownership_false_when_sum_not_one(self):
        flat = make_flat(self.building, flat_number="11A")
        owner1 = make_owner(display_name="Owner A")
        FlatOwner.objects.create(
            flat=flat,
            owner=owner1,
            share_numerator=1,
            share_denominator=3,
            effective_from=datetime.date(2024, 1, 1),
        )
        self.assertFalse(flat.has_complete_current_ownership)


# ---------------------------------------------------------------------------
# Person tests
# ---------------------------------------------------------------------------

class PersonModelTest(TestCase):
    def test_str_returns_full_name(self):
        p = make_person(first_name="Jana", last_name="Nováková")
        self.assertEqual(str(p), "Jana Nováková")

    def test_str_includes_title_before(self):
        p = make_person(title_before="Ing.", first_name="Petr", last_name="Zelený")
        self.assertIn("Ing.", str(p))
        self.assertIn("Petr", str(p))

    def test_str_includes_title_after(self):
        p = make_person(first_name="Pavel", last_name="Modrý", title_after="PhD.")
        self.assertIn("PhD.", str(p))

    def test_get_absolute_url_contains_pk(self):
        p = make_person()
        url = p.get_absolute_url()
        self.assertIn(str(p.pk), url)


# ---------------------------------------------------------------------------
# PropertyOwner tests
# ---------------------------------------------------------------------------

class PropertyOwnerModelTest(TestCase):
    def test_str_returns_display_name(self):
        owner = make_owner(display_name="Bytové družstvo ABC")
        self.assertEqual(str(owner), "Bytové družstvo ABC")

    def test_get_absolute_url_contains_pk(self):
        owner = make_owner()
        url = owner.get_absolute_url()
        self.assertIn(str(owner.pk), url)
        self.assertIn("owners", url)

    def test_person_type_choices(self):
        for ptype in ("natural", "legal", "sjm"):
            owner = make_owner(person_type=ptype)
            self.assertEqual(owner.person_type, ptype)

    def test_persons_m2m(self):
        owner = make_owner()
        p1 = make_person(first_name="Anna", last_name="Dvořák")
        p2 = make_person(first_name="Karel", last_name="Dvořák")
        owner.persons.add(p1, p2)
        self.assertEqual(owner.persons.count(), 2)
        self.assertIn(p1, owner.persons.all())

    def test_current_total_share_sums_active_flat_shares(self):
        building = make_building(name="Share House")
        flat1 = make_flat(building, flat_number="1")
        flat2 = make_flat(building, flat_number="2")
        owner = make_owner(display_name="Share Owner")

        FlatOwner.objects.create(
            flat=flat1,
            owner=owner,
            share_numerator=1,
            share_denominator=4,
            effective_from=datetime.date(2024, 1, 1),
        )
        FlatOwner.objects.create(
            flat=flat2,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2024, 1, 1),
        )

        self.assertEqual(owner.current_total_share, "3/4")

    def test_current_total_share_ignores_inactive_records(self):
        building = make_building(name="Inactive House")
        flat1 = make_flat(building, flat_number="1")
        flat2 = make_flat(building, flat_number="2")
        owner = make_owner(display_name="Inactive Owner")

        FlatOwner.objects.create(
            flat=flat1,
            owner=owner,
            share_numerator=1,
            share_denominator=3,
            effective_from=datetime.date(2024, 1, 1),
            effective_to=datetime.date(2024, 12, 31),
        )
        FlatOwner.objects.create(
            flat=flat2,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2025, 1, 1),
        )

        self.assertEqual(owner.current_total_share, "1/2")


# ---------------------------------------------------------------------------
# FlatOwner tests
# ---------------------------------------------------------------------------

class FlatOwnerModelTest(TestCase):
    def setUp(self):
        self.building = make_building()
        self.flat = make_flat(self.building)
        self.owner = make_owner()

    def _make_flat_owner(self, **kwargs):
        defaults = dict(
            flat=self.flat,
            owner=self.owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2020, 1, 1),
        )
        defaults.update(kwargs)
        return FlatOwner.objects.create(**defaults)

    def test_share_property(self):
        fo = self._make_flat_owner(share_numerator=1, share_denominator=4)
        self.assertEqual(fo.share, "1/4")

    def test_is_current_true_when_no_end_date(self):
        fo = self._make_flat_owner(effective_from=datetime.date(2020, 1, 1))
        self.assertTrue(fo.is_current)

    def test_is_current_false_when_end_date_in_past(self):
        fo = self._make_flat_owner(
            effective_from=datetime.date(2020, 1, 1),
            effective_to=datetime.date(2021, 12, 31),
        )
        self.assertFalse(fo.is_current)

    def test_is_current_false_when_end_date_today(self):
        fo = self._make_flat_owner(
            effective_from=datetime.date(2020, 1, 1),
            effective_to=datetime.date.today(),
        )
        self.assertFalse(fo.is_current)

    def test_str_includes_flat_and_owner(self):
        fo = self._make_flat_owner()
        result = str(fo)
        self.assertIn(self.owner.display_name, result)
        self.assertIn(self.flat.flat_number, result)

    def test_multiple_owners_per_flat(self):
        owner2 = make_owner(display_name="Druhý vlastník")
        fo1 = self._make_flat_owner(share_numerator=1, share_denominator=2)
        fo2 = FlatOwner.objects.create(
            flat=self.flat,
            owner=owner2,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2020, 1, 1),
        )
        self.assertEqual(self.flat.flat_owners.count(), 2)

    def test_clean_rejects_effective_to_before_effective_from(self):
        fo = FlatOwner(
            flat=self.flat,
            owner=self.owner,
            share_numerator=1,
            share_denominator=1,
            effective_from=datetime.date(2024, 1, 2),
            effective_to=datetime.date(2024, 1, 1),
        )
        with self.assertRaises(ValidationError):
            fo.full_clean()

    def test_clean_rejects_share_numerator_above_denominator(self):
        fo = FlatOwner(
            flat=self.flat,
            owner=self.owner,
            share_numerator=3,
            share_denominator=2,
            effective_from=datetime.date(2024, 1, 1),
        )
        with self.assertRaises(ValidationError):
            fo.full_clean()

    def test_clean_rejects_overlapping_ownership_periods_for_same_owner(self):
        self._make_flat_owner(
            share_numerator=1,
            share_denominator=1,
            effective_from=datetime.date(2024, 1, 1),
            effective_to=datetime.date(2024, 6, 30),
        )
        overlapping = FlatOwner(
            flat=self.flat,
            owner=self.owner,
            share_numerator=1,
            share_denominator=1,
            effective_from=datetime.date(2024, 6, 1),
            effective_to=datetime.date(2024, 12, 31),
        )
        with self.assertRaises(ValidationError):
            overlapping.full_clean()


# ---------------------------------------------------------------------------
# PropertyTenant tests
# ---------------------------------------------------------------------------

class PropertyTenantModelTest(TestCase):
    def setUp(self):
        self.building = make_building()
        self.flat = make_flat(self.building)
        self.person = make_person(first_name="Marie", last_name="Horáková")

    def _make_tenant(self, **kwargs):
        defaults = dict(
            flat=self.flat,
            person=self.person,
            effective_from=datetime.date(2022, 1, 1),
        )
        defaults.update(kwargs)
        return PropertyTenant.objects.create(**defaults)

    def test_str_includes_person_and_flat(self):
        t = self._make_tenant()
        result = str(t)
        self.assertIn(str(self.person), result)
        self.assertIn(self.flat.flat_number, result)

    def test_get_absolute_url_contains_pk(self):
        t = self._make_tenant()
        url = t.get_absolute_url()
        self.assertIn(str(t.pk), url)
        self.assertIn("tenants", url)

    def test_is_current_true_when_no_end_date(self):
        t = self._make_tenant(effective_from=datetime.date(2023, 1, 1))
        self.assertTrue(t.is_current)

    def test_is_current_false_when_past_end_date(self):
        t = self._make_tenant(
            effective_from=datetime.date(2022, 1, 1),
            effective_to=datetime.date(2022, 12, 31),
        )
        self.assertFalse(t.is_current)

    def test_is_current_false_when_end_date_today(self):
        t = self._make_tenant(
            effective_from=datetime.date(2020, 1, 1),
            effective_to=datetime.date.today(),
        )
        self.assertFalse(t.is_current)

    def test_person_can_have_multiple_tenancies(self):
        flat2 = make_flat(self.building, flat_number="2A")
        t1 = self._make_tenant(effective_from=datetime.date(2021, 1, 1))
        t2 = PropertyTenant.objects.create(
            flat=flat2,
            person=self.person,
            effective_from=datetime.date(2021, 6, 1),
        )
        self.assertEqual(self.person.tenancies.count(), 2)

    def test_clean_rejects_effective_to_before_effective_from(self):
        tenant = PropertyTenant(
            flat=self.flat,
            person=self.person,
            effective_from=datetime.date(2024, 1, 10),
            effective_to=datetime.date(2024, 1, 9),
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    def test_clean_rejects_overlapping_tenancy_periods_for_same_flat_person(self):
        self._make_tenant(
            effective_from=datetime.date(2024, 1, 1),
            effective_to=datetime.date(2024, 4, 30),
        )
        overlapping = PropertyTenant(
            flat=self.flat,
            person=self.person,
            effective_from=datetime.date(2024, 4, 15),
            effective_to=datetime.date(2024, 12, 31),
        )
        with self.assertRaises(ValidationError):
            overlapping.full_clean()
