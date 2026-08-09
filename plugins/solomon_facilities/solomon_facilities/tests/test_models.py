from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from solomon_property.models import Building, BuildingObject, Flat, Person

from solomon_facilities.models import (
    BuildingLevel,
    Door,
    FloorPlan,
    KeyCopy,
    KeyIssue,
    KeyProfile,
    KeyProfileLock,
    LockCylinder,
    PlanElement,
    PlanRevision,
    Space,
    SpaceFlatAssignment,
    SpaceUsage,
    TechnicalAsset,
    TechnicalConnection,
    TechnicalSystem,
)


class FacilitiesModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.building_object = BuildingObject.objects.create(name="Salounova 1937-1941")
        cls.other_building_object = BuildingObject.objects.create(name="Other object")
        cls.building = Building.objects.create(
            building_object=cls.building_object,
            name="Salounova 1937",
            street="Salounova",
            house_number="1937",
        )
        cls.other_building = Building.objects.create(
            building_object=cls.other_building_object,
            name="Other building",
            street="Other",
            house_number="1",
        )
        cls.flat = Flat.objects.create(
            building=cls.building,
            flat_number="1937/4",
            floor=1,
        )
        cls.level = BuildingLevel.objects.create(
            building_object=cls.building_object,
            number=1,
            reference="2NP",
        )
        cls.basement = BuildingLevel.objects.create(
            building_object=cls.building_object,
            number=-1,
            reference="1PP",
        )

    def test_space_rejects_building_from_another_building_object(self):
        space = Space(
            level=self.level,
            building=self.other_building,
            reference="X1",
            name="Invalid room",
            kind="room",
        )

        with self.assertRaises(ValidationError):
            space.full_clean()

    def test_cellar_assignment_can_link_to_flat_on_another_level(self):
        cellar = Space.objects.create(
            level=self.basement,
            building=self.building,
            reference="1937-S4",
            name="Cellar S4",
            kind="cellar",
        )
        assignment = SpaceFlatAssignment(
            space=cellar,
            flat=self.flat,
            role="cellar",
        )

        assignment.full_clean()

    def test_flat_cellar_space_returns_current_cellar_assignment(self):
        cellar = Space.objects.create(
            level=self.basement,
            building=self.building,
            reference="1937-S4",
            name="Cellar S4",
            kind="cellar",
        )
        SpaceFlatAssignment.objects.create(
            space=cellar,
            flat=self.flat,
            role="cellar",
        )

        self.assertEqual(self.flat.cellar_space, cellar)
        self.assertEqual(
            self.flat.cellar_space.get_absolute_url(), cellar.get_absolute_url()
        )

    def test_primary_assignment_rejects_flat_on_another_level(self):
        space = Space.objects.create(
            level=self.basement,
            building=self.building,
            reference="1937-B1",
            name="Basement room",
            kind="room",
        )
        assignment = SpaceFlatAssignment(
            space=space,
            flat=self.flat,
            role="primary",
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_space_usage_requires_exactly_one_holder(self):
        space = Space.objects.create(
            level=self.basement,
            reference="COMMON-1",
            name="Workshop",
            kind="common_room",
        )
        usage = SpaceUsage(
            space=space,
            usage_type="rental",
            effective_from=timezone.localdate(),
        )

        with self.assertRaises(ValidationError):
            usage.full_clean()

    def test_door_requires_a_connected_space(self):
        door = Door(
            level=self.level,
            reference="D1",
            name="Unconnected door",
        )

        with self.assertRaises(ValidationError):
            door.full_clean()

    def test_plan_element_validates_geometry_and_level(self):
        plan = FloorPlan.objects.create(level=self.level, name="Second floor")
        revision = PlanRevision.objects.create(plan=plan, revision=1)
        space = Space.objects.create(
            level=self.level,
            building=self.building,
            reference="1937-4",
            name="Flat 1937/4",
            kind="flat",
        )
        element = PlanElement(
            revision=revision,
            element_type="space",
            space=space,
            geometry={
                "type": "polygon",
                "points": [{"x": 1, "y": 2}, {"x": 5, "y": 6}],
            },
        )

        element.full_clean()
        element.geometry = {"type": "polygon", "points": [{"x": float("inf"), "y": 2}]}

        with self.assertRaises(ValidationError):
            element.full_clean()

    def test_only_one_active_issue_is_allowed_per_physical_key(self):
        profile = KeyProfile.objects.create(
            building_object=self.building_object,
            code="MASTER",
            name="Master key",
        )
        key_copy = KeyCopy.objects.create(profile=profile, inventory_code="KEY-001")
        person = Person.objects.create(first_name="Test", last_name="Holder")
        KeyIssue.objects.create(key_copy=key_copy, person=person)

        with self.assertRaises(IntegrityError), transaction.atomic():
            KeyIssue.objects.create(key_copy=key_copy, external_holder="Contractor")

    def test_key_issue_and_return_synchronize_physical_key_status(self):
        profile = KeyProfile.objects.create(
            building_object=self.building_object,
            code="SERVICE",
            name="Service key",
        )
        key_copy = KeyCopy.objects.create(profile=profile, inventory_code="KEY-002")
        issue = KeyIssue.objects.create(key_copy=key_copy, external_holder="Contractor")

        key_copy.refresh_from_db()
        self.assertEqual(key_copy.status, "issued")

        issue.returned_at = timezone.now()
        issue.save()
        key_copy.refresh_from_db()
        self.assertEqual(key_copy.status, "available")

    def test_lost_key_cannot_be_issued(self):
        profile = KeyProfile.objects.create(
            building_object=self.building_object,
            code="LOST",
            name="Lost key profile",
        )
        key_copy = KeyCopy.objects.create(
            profile=profile,
            inventory_code="KEY-003",
            status="lost",
        )
        issue = KeyIssue(key_copy=key_copy, external_holder="Contractor")

        with self.assertRaises(ValidationError):
            issue.full_clean()

    def test_key_profile_cannot_open_lock_in_another_building_object(self):
        space = Space.objects.create(
            level=self.level,
            reference="CORRIDOR",
            name="Corridor",
            kind="corridor",
        )
        door = Door.objects.create(
            level=self.level,
            reference="D2",
            name="Corridor door",
            from_space=space,
        )
        lock = LockCylinder.objects.create(door=door, name="Main")
        profile = KeyProfile.objects.create(
            building_object=self.other_building_object,
            code="OTHER",
            name="Other key",
        )
        relation = KeyProfileLock(key_profile=profile, lock=lock)

        with self.assertRaises(ValidationError):
            relation.full_clean()

    def test_technical_connection_requires_same_system(self):
        water = TechnicalSystem.objects.create(
            building_object=self.building_object,
            name="Cold water",
            kind="cold_water",
        )
        gas = TechnicalSystem.objects.create(
            building_object=self.building_object,
            name="Gas",
            kind="gas",
        )
        valve = TechnicalAsset.objects.create(
            system=water,
            code="HUV",
            name="Main water valve",
            asset_type="valve",
        )
        gas_valve = TechnicalAsset.objects.create(
            system=gas,
            code="HUP",
            name="Main gas valve",
            asset_type="valve",
        )
        connection = TechnicalConnection(
            from_asset=valve,
            to_asset=gas_valve,
            kind="feeds",
        )

        with self.assertRaises(ValidationError):
            connection.full_clean()
