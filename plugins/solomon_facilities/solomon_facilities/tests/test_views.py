import json
import re

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from solomon_property.models import (
    Building,
    BuildingObject,
    Flat,
    FlatOwner,
    Person,
    PropertyOwner,
)

from solomon_facilities.models import (
    BuildingLevel,
    Door,
    FloorPlan,
    KeyCopy,
    KeyIssue,
    KeyProfile,
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
from users.models import ObjectPermission


def grant_object_permission(user, model, *actions):
    permission = ObjectPermission.objects.create(
        name=f"Test {model._meta.label} {'-'.join(actions)}",
        actions=list(actions),
    )
    permission.object_types.add(ContentType.objects.get_for_model(model))
    user.object_permissions.add(permission)


class FloorPlanViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.building_object = BuildingObject.objects.create(name="Salounova 1937-1941")
        cls.building = Building.objects.create(
            building_object=cls.building_object,
            name="Salounova 1937",
            street="Salounova",
            house_number="1937",
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
        cls.plan = FloorPlan.objects.create(level=cls.level, name="Second floor")
        cls.revision = PlanRevision.objects.create(
            plan=cls.plan,
            revision=1,
            status="published",
        )
        cls.plan.active_revision = cls.revision
        cls.plan.save()
        cls.space = Space.objects.create(
            level=cls.level,
            building=cls.building,
            reference="1937-4",
            name="Flat 1937/4",
            kind="flat",
            area_m2="77.90",
        )
        SpaceFlatAssignment.objects.create(
            space=cls.space,
            flat=cls.flat,
            role="primary",
        )
        cls.person = Person.objects.create(first_name="Current", last_name="Tenant")
        SpaceUsage.objects.create(
            space=cls.space,
            person=cls.person,
            usage_type="rental",
            effective_from=timezone.localdate(),
        )
        cls.element = PlanElement.objects.create(
            revision=cls.revision,
            element_type="space",
            label="1937/4",
            geometry={"type": "rect", "x": 10, "y": 20, "width": 100, "height": 80},
            style={"fill": "#dce9e4", "stroke": "#39806a"},
            space=cls.space,
        )
        cls.user = get_user_model().objects.create_user(
            username="viewer", password="test"
        )
        grant_object_permission(cls.user, FloorPlan, "view")

    def setUp(self):
        self.client.force_login(self.user)

    def test_plan_page_renders_viewer(self):
        response = self.client.get(
            reverse("plugins:solomon_facilities:floorplan", kwargs={"pk": self.plan.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "schematic-canvas")
        self.assertContains(response, "Second floor")

    def test_plan_without_revision_shows_empty_state(self):
        level = BuildingLevel.objects.create(
            building_object=self.building_object,
            number=2,
            reference="3NP",
        )
        plan = FloorPlan.objects.create(level=level, name="Empty plan")

        response = self.client.get(
            reverse("plugins:solomon_facilities:floorplan", kwargs={"pk": plan.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No plan revision yet")
        self.assertNotContains(response, "solomon_facilities/viewer.js")

    def test_draft_only_plan_renders_for_editor_with_upload_link(self):
        grant_object_permission(self.user, FloorPlan, "change")
        grant_object_permission(self.user, PlanRevision, "change")
        level = BuildingLevel.objects.create(
            building_object=self.building_object,
            number=2,
            reference="3NP",
        )
        plan = FloorPlan.objects.create(level=level, name="Draft plan")
        draft = PlanRevision.objects.create(plan=plan, revision=1, status="draft")

        response = self.client.get(
            reverse("plugins:solomon_facilities:floorplan", kwargs={"pk": plan.pk})
        )

        data_url = reverse(
            "plugins:solomon_facilities:floorplan_data", kwargs={"pk": plan.pk}
        )
        upload_url = reverse(
            "plugins:solomon_facilities:planrevision_edit", kwargs={"pk": draft.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-url="{data_url}?draft=1"')
        self.assertContains(response, upload_url)

        editor_response = self.client.get(
            reverse("plugins:solomon_facilities:floorplan_draw", kwargs={"pk": plan.pk})
        )
        self.assertContains(editor_response, 'class="form-select no-ts"', count=2)
        self.assertContains(editor_response, "No linkable objects loaded")
        self.assertContains(editor_response, "New space")
        self.assertContains(editor_response, "New door")
        self.assertContains(editor_response, "Refresh")

        data_response = self.client.get(data_url, {"draft": "1"})
        self.assertEqual(data_response.status_code, 200)
        self.assertEqual(data_response.json()["revision"]["id"], draft.pk)

    def test_plan_data_hides_person_without_property_permission(self):
        response = self.client.get(
            reverse(
                "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
            )
        )

        self.assertEqual(response.status_code, 200)
        space = response.json()["targets"]["spaces"][str(self.space.pk)]
        self.assertEqual(space["usages"], [])
        self.assertEqual(space["assignments"][0]["flat"], str(self.flat))

    def test_plan_data_includes_holder_with_property_permission(self):
        grant_object_permission(self.user, Person, "view")

        response = self.client.get(
            reverse(
                "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
            )
        )

        space = response.json()["targets"]["spaces"][str(self.space.pk)]
        self.assertEqual(space["usages"][0]["holder"], str(self.person))

    def test_put_atomically_replaces_draft_elements(self):
        draft = PlanRevision.objects.create(plan=self.plan, revision=2, status="draft")
        PlanElement.objects.create(
            revision=draft,
            element_type="text",
            label="Old",
            geometry={"type": "text", "x": 1, "y": 1, "text": "Old"},
        )
        grant_object_permission(self.user, PlanRevision, "change")
        payload = {
            "revision_id": draft.pk,
            "elements": [
                {
                    "element_type": "wall",
                    "label": "North wall",
                    "geometry": {"type": "line", "x1": 1, "y1": 2, "x2": 30, "y2": 2},
                    "style": {"stroke": "#27343a", "stroke_width": 7},
                }
            ],
        }

        response = self.client.put(
            reverse(
                "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
            ),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(draft.elements.count(), 1)
        self.assertEqual(draft.elements.get().label, "North wall")

    def test_invalid_put_rolls_back_existing_draft(self):
        draft = PlanRevision.objects.create(plan=self.plan, revision=2, status="draft")
        original = PlanElement.objects.create(
            revision=draft,
            element_type="text",
            label="Keep me",
            geometry={"type": "text", "x": 1, "y": 1, "text": "Keep me"},
        )
        grant_object_permission(self.user, PlanRevision, "change")
        payload = {
            "revision_id": draft.pk,
            "elements": [
                {
                    "element_type": "wall",
                    "geometry": {
                        "type": "line",
                        "x1": "invalid",
                        "y1": 2,
                        "x2": 30,
                        "y2": 2,
                    },
                }
            ],
        }

        response = self.client.put(
            reverse(
                "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
            ),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            PlanElement.objects.filter(pk=original.pk, label="Keep me").exists()
        )

    def test_editor_requires_plan_and_revision_change_permissions(self):
        grant_object_permission(self.user, FloorPlan, "change")

        response = self.client.get(
            reverse(
                "plugins:solomon_facilities:floorplan_draw", kwargs={"pk": self.plan.pk}
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_lists_and_saves_linked_door_with_csrf(self):
        grant_object_permission(self.user, FloorPlan, "change")
        grant_object_permission(self.user, PlanRevision, "change")
        door = Door.objects.create(
            level=self.level,
            reference="D-EDITOR",
            name="Editor door",
            from_space=self.space,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        editor_response = client.get(
            reverse(
                "plugins:solomon_facilities:floorplan_draw", kwargs={"pk": self.plan.pk}
            )
        )
        token_match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            editor_response.content.decode(),
        )
        self.assertIsNotNone(token_match)
        draft = self.plan.revisions.get(status="draft")

        data_response = client.get(
            reverse(
                "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
            ),
            {"draft": "1"},
        )
        self.assertEqual(data_response.status_code, 200)
        self.assertEqual(
            data_response.json()["targets"]["doors"][str(door.pk)]["label"],
            str(door),
        )

        save_response = client.put(
            reverse(
                "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
            ),
            data=json.dumps(
                {
                    "revision_id": draft.pk,
                    "elements": [
                        {
                            "element_type": "door",
                            "label": "Editor door",
                            "geometry": {
                                "type": "line",
                                "x1": 10,
                                "y1": 20,
                                "x2": 40,
                                "y2": 20,
                            },
                            "door_id": door.pk,
                        }
                    ],
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token_match.group(1),
        )

        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(draft.elements.get().door, door)

    def test_floor_plan_rest_endpoint_serializes_url(self):
        response = self.client.get(
            reverse("plugins-api:solomon_facilities-api:floorplan-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["id"], self.plan.pk)
        self.assertIn("url", response.json()["results"][0])

    def test_flat_and_owner_details_link_to_schematic_tabs(self):
        self.user.is_superuser = True
        self.user.save()
        owner = PropertyOwner.objects.create(display_name="Test Owner")
        FlatOwner.objects.create(
            flat=self.flat,
            owner=owner,
            effective_from=timezone.localdate(),
        )
        flat_tab_url = reverse(
            "plugins:solomon_property:flat_schematics", kwargs={"pk": self.flat.pk}
        )
        owner_tab_url = reverse(
            "plugins:solomon_property:propertyowner_schematics",
            kwargs={"pk": owner.pk},
        )

        flat_detail = self.client.get(self.flat.get_absolute_url())
        owner_detail = self.client.get(owner.get_absolute_url())
        flat_tab = self.client.get(flat_tab_url)
        owner_tab = self.client.get(owner_tab_url)

        self.assertContains(flat_detail, flat_tab_url)
        self.assertContains(owner_detail, owner_tab_url)
        self.assertContains(flat_tab, self.plan.get_absolute_url())
        self.assertContains(
            owner_tab, f"{self.plan.get_absolute_url()}?highlight={self.space.pk}"
        )

    def test_all_crud_views_and_templates_render(self):
        self.user.is_superuser = True
        self.user.save()
        door = Door.objects.create(
            level=self.level,
            reference="D-01",
            name="Entrance",
            door_type="entrance",
            from_space=self.space,
        )
        lock = LockCylinder.objects.create(door=door, name="Main cylinder")
        key_profile = KeyProfile.objects.create(
            building_object=self.building_object,
            code="MASTER",
            name="Master key",
        )
        key_copy = KeyCopy.objects.create(
            profile=key_profile,
            inventory_code="KEY-001",
        )
        key_issue = KeyIssue.objects.create(
            key_copy=key_copy,
            external_holder="Test contractor",
        )
        system = TechnicalSystem.objects.create(
            building_object=self.building_object,
            name="Cold water",
            kind="cold_water",
        )
        source_asset = TechnicalAsset.objects.create(
            system=system,
            level=self.level,
            space=self.space,
            code="CW-01",
            name="Main valve",
            asset_type="valve",
        )
        target_asset = TechnicalAsset.objects.create(
            system=system,
            level=self.level,
            space=self.space,
            code="CW-02",
            name="Riser",
            asset_type="riser",
        )
        connection = TechnicalConnection.objects.create(
            from_asset=source_asset,
            to_asset=target_asset,
        )

        records = {
            "buildinglevel": self.level,
            "floorplan": self.plan,
            "space": self.space,
            "spaceflatassignment": self.space.flat_assignments.get(),
            "spaceusage": self.space.usages.get(),
            "door": door,
            "lockcylinder": lock,
            "keyprofile": key_profile,
            "keycopy": key_copy,
            "keyissue": key_issue,
            "technicalsystem": system,
            "technicalasset": source_asset,
            "technicalconnection": connection,
        }

        for model_name, record in records.items():
            with self.subTest(model=model_name, view="list"):
                response = self.client.get(
                    reverse(f"plugins:solomon_facilities:{model_name}_list")
                )
                self.assertEqual(response.status_code, 200)
            for action in ("edit", "delete", "changelog"):
                with self.subTest(model=model_name, view=action):
                    response = self.client.get(
                        reverse(
                            f"plugins:solomon_facilities:{model_name}_{action}",
                            kwargs={"pk": record.pk},
                        )
                    )
                    self.assertLess(response.status_code, 400)

        for model_name, record in {
            "floorplan": self.plan,
            "space": self.space,
            "door": door,
            "keyprofile": key_profile,
            "keycopy": key_copy,
            "technicalsystem": system,
            "technicalasset": source_asset,
        }.items():
            with self.subTest(model=model_name, view="detail"):
                response = self.client.get(
                    reverse(
                        f"plugins:solomon_facilities:{model_name}",
                        kwargs={"pk": record.pk},
                    )
                )
                self.assertEqual(response.status_code, 200)
