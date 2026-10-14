import csv
import json
import re
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override
from extras.models import Tag

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
from solomon_facilities.forms import SpaceBulkEditForm, SpaceUsageForm
from solomon_facilities.tables import SpaceTable
from solomon_facilities.views import SpaceListView
from users.models import ObjectPermission


def grant_object_permission(user, model, *actions):
    permission = ObjectPermission.objects.create(
        name=f"Test {model._meta.label} {'-'.join(actions)}",
        actions=list(actions),
    )
    permission.object_types.add(ContentType.objects.get_for_model(model))
    user.object_permissions.add(permission)


class SpaceListViewTest(TestCase):
    columns = ("flat_assignments", "usages", "technical_assets")

    @classmethod
    def setUpTestData(cls):
        cls.building_object = BuildingObject.objects.create(name="Test object")
        cls.building = Building.objects.create(
            building_object=cls.building_object,
            name="Test entrance",
            street="Test street",
            house_number="1",
        )
        cls.level = BuildingLevel.objects.create(
            building_object=cls.building_object, number=0, reference="1NP"
        )
        cls.space = Space.objects.create(
            level=cls.level, reference="S-01", name="Common room", kind="common_room"
        )
        cls.flat = Flat.objects.create(building=cls.building, flat_number="1/1", floor=0)
        cls.assignment = SpaceFlatAssignment.objects.create(
            space=cls.space, flat=cls.flat, role="exclusive_use"
        )
        cls.person = Person.objects.create(first_name="Current", last_name="Tenant")
        cls.owner = PropertyOwner.objects.create(
            display_name="Current organization", person_type="legal"
        )
        cls.usage = SpaceUsage.objects.create(
            space=cls.space,
            person=cls.person,
            effective_from=timezone.localdate(),
        )
        SpaceUsage.objects.create(
            space=cls.space,
            owner=cls.owner,
            usage_type="occupancy",
            effective_from=timezone.localdate(),
        )
        system = TechnicalSystem.objects.create(
            building_object=cls.building_object, name="Water", kind="cold_water"
        )
        cls.asset = TechnicalAsset.objects.create(
            system=system,
            space=cls.space,
            code="CW-01",
            name="Main valve",
            asset_type="valve",
        )
        cls.user = get_user_model().objects.create_user(
            username="space-list-viewer", is_superuser=True
        )

    def setUp(self):
        self.client.force_login(self.user)

    def get_list(self, **params):
        return self.client.get(reverse("plugins:solomon_facilities:space_list"), params)

    def select_columns(self):
        self.user.config.set(
            "tables.SpaceTable.columns",
            ["reference", *self.columns],
            commit=True,
        )

    def test_related_columns_are_optional_and_configurable(self):
        response = self.get_list()
        self.assertEqual(response.status_code, 200)
        table = response.context["table"]
        available = dict(table.available_columns)
        self.assertEqual(str(available["flat_assignments"]), "Flat assignments")
        self.assertEqual(str(available["usages"]), "Rentals and occupancy")
        self.assertEqual(str(available["technical_assets"]), "Technical assets")
        for column in self.columns:
            self.assertFalse(table.columns[column].visible)

        self.select_columns()
        response = self.get_list()
        self.assertEqual(response.status_code, 200)
        for column in self.columns:
            self.assertTrue(response.context["table"].columns[column].visible)
        for obj in (self.flat, self.person, self.owner, self.asset):
            self.assertContains(response, obj.get_absolute_url())
            self.assertContains(response, str(obj))
        self.assertContains(response, "Common area under exclusive use")
        self.assertContains(response, "Rental")
        self.assertContains(response, "Occupancy")

    def test_related_column_headers_are_translated(self):
        with override("cs"):
            table = SpaceTable([])
            self.assertEqual(
                str(table.columns["flat_assignments"].header), "Přiřazení prostorů"
            )
            self.assertEqual(
                str(table.columns["usages"].header), "Pronájmy a užívání"
            )
            self.assertEqual(
                str(table.columns["technical_assets"].header), "Technické součásti"
            )
            form = SpaceBulkEditForm()
            self.assertEqual(str(form.fields["level"].label), "Úroveň")
            self.assertEqual(
                str(form.fields["building"].label), "Vchod nebo budova"
            )
            self.assertEqual(str(form.fields["parent"].label), "Nadřazený prostor")

    def test_only_current_assignments_and_usages_are_shown(self):
        today = timezone.localdate()
        self.select_columns()
        for label, start, end in (
            ("Past", today - timedelta(days=2), today - timedelta(days=1)),
            ("Future", today + timedelta(days=1), None),
            ("Boundary", today, today),
        ):
            flat = Flat.objects.create(
                building=self.building, flat_number=label, floor=0
            )
            SpaceFlatAssignment.objects.create(
                space=self.space,
                flat=flat,
                role="exclusive_use",
                effective_from=start,
                effective_to=end,
            )
            person = Person.objects.create(first_name=label, last_name="Holder")
            SpaceUsage.objects.create(
                space=self.space,
                person=person,
                effective_from=start,
                effective_to=end,
            )
        response = self.get_list()
        self.assertContains(response, "Boundary")
        self.assertContains(response, "Boundary Holder")
        self.assertNotContains(response, "Past")
        self.assertNotContains(response, "Future")
        self.assertContains(response, str(self.flat))
        self.assertContains(response, str(self.person))

    def test_assets_include_all_statuses_but_only_located_assets(self):
        self.select_columns()
        self.asset.status = "out_of_service"
        self.asset.save()
        elsewhere = TechnicalAsset.objects.create(
            system=self.asset.system,
            code="CW-ELSEWHERE",
            name="Elsewhere",
            asset_type="valve",
        )
        elsewhere.serves_spaces.add(self.space)
        response = self.get_list()
        self.assertContains(response, str(self.asset))
        self.assertNotContains(response, elsewhere.code)

    def test_related_records_require_view_permissions(self):
        self.select_columns()
        self.user.is_superuser = False
        self.user.save()
        grant_object_permission(self.user, Space, "view")
        response = self.get_list()
        self.assertEqual(response.status_code, 200)
        for obj in (self.flat, self.person, self.owner, self.asset):
            self.assertNotContains(response, obj.get_absolute_url())
            self.assertNotContains(response, str(obj))

    def test_related_object_constraints_and_holder_permissions_are_respected(self):
        self.select_columns()
        self.user.is_superuser = False
        self.user.save()
        for model in (Space, SpaceFlatAssignment, SpaceUsage, Flat, Person):
            grant_object_permission(self.user, model, "view")
        permission = ObjectPermission.objects.create(
            name="Other assets only",
            actions=["view"],
            constraints={"id": self.asset.pk + 1},
        )
        permission.object_types.add(ContentType.objects.get_for_model(TechnicalAsset))
        self.user.object_permissions.add(permission)
        response = self.get_list()
        self.assertContains(response, str(self.flat))
        self.assertContains(response, str(self.person))
        self.assertNotContains(response, str(self.owner))
        self.assertNotContains(response, str(self.asset))

    def test_related_cells_use_bounded_queries_and_escape_labels(self):
        self.person.first_name = "<script>alert(1)</script>"
        self.person.save()
        Space.objects.create(
            level=self.level, reference="S-02", name="Empty", kind="common_room"
        )
        request = RequestFactory().get("/")
        request.user = self.user
        queryset = SpaceListView().get_queryset(request)
        table = SpaceTable(queryset)
        with self.assertNumQueries(4):
            cells = [
                [row.get_cell(column) for column in self.columns]
                for row in table.rows
            ]
        self.assertIn("&lt;script&gt;", cells[0][1])
        self.assertNotIn("<script>", cells[0][1])
        for cell in cells[1]:
            self.assertEqual(cell, "&mdash;")

    def test_selected_related_columns_export_as_plain_text(self):
        self.select_columns()
        response = self.get_list(export="table")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn("<a", content)
        rows = list(csv.reader(StringIO(content)))
        self.assertEqual(
            rows[0],
            [
                "Reference",
                "Flat assignments",
                "Rentals and occupancy",
                "Technical assets",
            ],
        )
        self.assertIn(str(self.flat), rows[1][1])
        self.assertIn(str(self.person), rows[1][2])
        self.assertIn(str(self.owner), rows[1][2])
        self.assertIn(str(self.asset), rows[1][3])

    def bulk_edit(self, data, query=""):
        return self.client.post(
            reverse("plugins:solomon_facilities:space_bulk_edit") + query, data
        )

    def create_second_space(self):
        return Space.objects.create(
            level=self.level,
            reference="S-02",
            name="Second room",
            kind="common_room",
        )

    def test_bulk_edit_action_has_valid_url_with_list_filters(self):
        response = self.get_list(page=2, q="dry")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'formaction="/plugins/facilities/spaces/edit/?page=2&amp;q=dry"',
        )

    def test_bulk_edit_selected_spaces_uses_netbox_form_and_preserves_blanks(self):
        second = self.create_second_space()
        unselected = Space.objects.create(
            level=self.level, reference="S-03", name="Unselected", kind="room"
        )
        selected = [self.space.pk, second.pk]
        response = self.bulk_edit({"pk": selected}, "?page=2&q=dry")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "generic/bulk_edit.html")
        self.assertIsInstance(response.context["form"], SpaceBulkEditForm)
        self.assertEqual(
            set(response.context["form"].initial["pk"]), set(map(str, selected))
        )
        self.assertContains(response, "Common room")
        self.assertContains(response, "Second room")

        response = self.bulk_edit(
            {"pk": selected, "status": "inactive", "_apply": "1"}
        )
        self.assertRedirects(
            response, reverse("plugins:solomon_facilities:space_list")
        )
        self.space.refresh_from_db()
        second.refresh_from_db()
        unselected.refresh_from_db()
        self.assertEqual(self.space.status, "inactive")
        self.assertEqual(second.status, "inactive")
        self.assertEqual(unselected.status, "active")
        self.assertEqual(self.space.kind, "common_room")
        self.assertEqual(self.space.name, "Common room")
        self.assertEqual(self.space.reference, "S-01")
        self.assertEqual(second.reference, "S-02")

    def test_bulk_edit_all_matching_spaces_respects_search(self):
        second = self.create_second_space()
        response = self.bulk_edit(
            {"_all": "1", "status": "inactive", "_apply": "1"},
            "?q=Common&page=2",
        )
        self.assertEqual(response.status_code, 302)
        self.space.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.space.status, "inactive")
        self.assertEqual(second.status, "active")

    def test_bulk_edit_browser_defaults_preserve_mixed_types_and_statuses(self):
        second = self.create_second_space()
        second.kind = "technical_room"
        second.status = "planned"
        second.save()
        selected = [self.space.pk, second.pk]
        response = self.bulk_edit({"pk": selected})
        html = response.content.decode()
        defaults = {}
        for field in ("kind", "status"):
            select = re.search(
                rf'<select\b[^>]*name="{field}"[^>]*>(.*?)</select>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(select)
            first_option = re.search(r'<option value="([^"]*)"', select.group(1))
            self.assertIsNotNone(first_option)
            defaults[field] = first_option.group(1)
            self.assertEqual(defaults[field], "")
        response = self.bulk_edit(
            {"pk": selected, "notes": "Updated notes", "_apply": "1", **defaults}
        )
        self.assertEqual(response.status_code, 302)
        self.space.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.space.kind, "common_room")
        self.assertEqual(second.kind, "technical_room")
        self.assertEqual(self.space.status, "active")
        self.assertEqual(second.status, "planned")
        self.assertEqual(self.space.notes, "Updated notes")
        self.assertEqual(second.notes, "Updated notes")

    def test_bulk_edit_explicit_type_choice_updates_selected_spaces(self):
        second = self.create_second_space()
        response = self.bulk_edit(
            {
                "pk": [self.space.pk, second.pk],
                "kind": "technical_room",
                "status": "",
                "_apply": "1",
            }
        )
        self.assertEqual(response.status_code, 302)
        self.space.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.space.kind, "technical_room")
        self.assertEqual(second.kind, "technical_room")

    def test_bulk_edit_clears_nullable_fields_and_preserves_zero_area(self):
        self.space.building = self.building
        self.space.area_m2 = "12.50"
        self.space.notes = "Clear this"
        self.space.save()
        response = self.bulk_edit(
            {
                "pk": [self.space.pk],
                "_nullify": ["building", "notes"],
                "area_m2": "0",
                "_apply": "1",
            }
        )
        self.assertEqual(response.status_code, 302)
        self.space.refresh_from_db()
        self.assertIsNone(self.space.building_id)
        self.assertEqual(self.space.notes, "")
        self.assertEqual(self.space.area_m2, 0)

    def test_bulk_edit_model_validation_rolls_back_all_selected_spaces(self):
        parent = Space.objects.create(
            level=self.level, reference="P-01", name="Parent", kind="common_room"
        )
        other_level = BuildingLevel.objects.create(
            building_object=self.building_object, number=1, reference="2NP"
        )
        second = Space.objects.create(
            level=other_level, reference="S-02", name="Other floor", kind="room"
        )
        response = self.bulk_edit(
            {
                "pk": [self.space.pk, second.pk],
                "status": "inactive",
                "parent": parent.pk,
                "_apply": "1",
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.space.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.space.status, "active")
        self.assertEqual(second.status, "active")
        self.assertIsNone(self.space.parent_id)
        self.assertIsNone(second.parent_id)

    def test_bulk_edit_updates_tags_and_preserves_return_url(self):
        added = Tag.objects.create(name="New tag", slug="new-tag")
        removed = Tag.objects.create(name="Old tag", slug="old-tag")
        self.space.tags.add(removed)
        return_url = reverse("plugins:solomon_facilities:space_list") + "?page=2&q=dry"
        response = self.bulk_edit(
            {
                "pk": [self.space.pk],
                "add_tags": [added.pk],
                "remove_tags": [removed.pk],
                "changelog_message": "Bulk space update",
                "return_url": return_url,
                "_apply": "1",
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, return_url)
        self.assertEqual(list(self.space.tags.all()), [added])

    def test_bulk_edit_requires_change_permission(self):
        self.user.is_superuser = False
        self.user.save()
        grant_object_permission(self.user, Space, "view")
        response = self.bulk_edit(
            {"pk": [self.space.pk], "status": "inactive", "_apply": "1"}
        )
        self.assertEqual(response.status_code, 403)
        self.space.refresh_from_db()
        self.assertEqual(self.space.status, "active")

    def test_bulk_edit_respects_object_change_constraints(self):
        second = self.create_second_space()
        self.user.is_superuser = False
        self.user.save()
        grant_object_permission(self.user, Space, "view")
        permission = ObjectPermission.objects.create(
            name="Change first space only",
            actions=["change"],
            constraints={"id": self.space.pk},
        )
        permission.object_types.add(ContentType.objects.get_for_model(Space))
        self.user.object_permissions.add(permission)
        response = self.bulk_edit(
            {
                "pk": [self.space.pk, second.pk],
                "status": "inactive",
                "_apply": "1",
            }
        )
        self.assertEqual(response.status_code, 302)
        self.space.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.space.status, "inactive")
        self.assertEqual(second.status, "active")


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

    def test_space_usage_form_uses_netbox_date_pickers(self):
        grant_object_permission(self.user, SpaceUsage, "add")
        form = SpaceUsageForm()

        self.assertTrue(form.fields["effective_from"].required)
        self.assertFalse(form.fields["effective_to"].required)
        for field_name in ("effective_from", "effective_to"):
            widget = form.fields[field_name].widget
            self.assertEqual(widget.attrs["class"], "date-picker")
            self.assertEqual(widget.attrs["placeholder"], "YYYY-MM-DD")

        response = self.client.get(
            reverse("plugins:solomon_facilities:spaceusage_add")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "date-picker", count=2)
        self.assertContains(response, 'placeholder="YYYY-MM-DD"', count=2)

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

    def test_plan_view_loads_transform_aware_viewer(self):
        response = self.client.get(
            reverse("plugins:solomon_facilities:floorplan", kwargs={"pk": self.plan.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "viewer.js?v=5")
        self.assertContains(response, "solomon_facilities/labels.js?v=2")

    def test_space_detail_links_to_selected_schematic(self):
        grant_object_permission(self.user, Space, "view")
        response = self.client.get(self.space.get_absolute_url())
        url = f"{self.plan.get_absolute_url()}?highlight={self.space.pk}"
        self.assertContains(response, f'href="{url}"')
        self.assertContains(response, "View schematic")
        plan_response = self.client.get(url)
        self.assertContains(plan_response, f'data-highlight="{self.space.pk}"')

        response = self.client.get(
            self.space.get_absolute_url(), HTTP_ACCEPT_LANGUAGE="cs"
        )
        self.assertContains(response, "Zobrazit schéma")

    def test_space_detail_omits_schematic_without_linked_element(self):
        grant_object_permission(self.user, Space, "view")
        self.element.delete()
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")

    def test_space_detail_omits_schematic_without_plan(self):
        grant_object_permission(self.user, Space, "view")
        self.plan.delete()
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")

    def test_space_detail_uses_displayed_revision_not_old_or_draft_links(self):
        grant_object_permission(self.user, Space, "view")
        published = PlanRevision.objects.create(
            plan=self.plan, revision=2, status="published"
        )
        self.plan.active_revision = published
        self.plan.save()
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")
        self.revision.status = "draft"
        self.revision.save()
        grant_object_permission(self.user, FloorPlan, "change")
        grant_object_permission(self.user, PlanRevision, "change")
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")

    def test_space_detail_uses_latest_published_revision_without_active_revision(self):
        grant_object_permission(self.user, Space, "view")
        self.plan.active_revision = None
        self.plan.save()
        response = self.client.get(self.space.get_absolute_url())
        self.assertContains(response, "View schematic")

    def test_space_detail_draft_only_link_requires_editor_permissions(self):
        grant_object_permission(self.user, Space, "view")
        self.plan.active_revision = None
        self.plan.save()
        self.revision.status = "draft"
        self.revision.save()
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")
        grant_object_permission(self.user, FloorPlan, "change")
        grant_object_permission(self.user, PlanRevision, "change")
        response = self.client.get(self.space.get_absolute_url())
        self.assertContains(response, "View schematic")

    def test_space_detail_schematic_respects_plan_object_permissions(self):
        user = get_user_model().objects.create_user(username="space-only-viewer")
        grant_object_permission(user, Space, "view")
        self.client.force_login(user)
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")
        grant_object_permission(user, FloorPlan, "view")
        permission = user.object_permissions.get(
            object_types=ContentType.objects.get_for_model(FloorPlan)
        )
        permission.constraints = {"pk": self.plan.pk + 1}
        permission.save()
        response = self.client.get(self.space.get_absolute_url())
        self.assertNotContains(response, "View schematic")

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
        self.assertContains(editor_response, "Duplicate selected", count=2)
        self.assertContains(editor_response, 'aria-keyshortcuts="Shift+D"')
        self.assertContains(editor_response, 'id="cancel-edit"')
        self.assertContains(editor_response, 'id="save-form"')
        self.assertNotContains(editor_response, 'id="publish-form"')
        self.assertNotContains(editor_response, ">Publish<")
        self.assertContains(editor_response, "editor.js?v=12")
        self.assertContains(editor_response, "solomon_facilities/labels.js?v=2")
        self.assertContains(editor_response, 'id="element-label-visible"')
        self.assertContains(editor_response, "Show label on floor plan")
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

    def test_label_visibility_survives_save_publish_and_revision_copy(self):
        draft = PlanRevision.objects.create(plan=self.plan, revision=2, status="draft")
        grant_object_permission(self.user, FloorPlan, "change")
        grant_object_permission(self.user, PlanRevision, "change")
        data_url = reverse(
            "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
        )
        elements = [
            {
                "element_type": "space",
                "label": "Visible room" if visible else "Hidden room",
                "geometry": {
                    "type": "rect",
                    "x": 10,
                    "y": 20,
                    "width": 100,
                    "height": 60,
                },
                "style": {"label_visible": visible},
            }
            for visible in (True, False)
        ]
        response = self.client.put(
            data_url,
            data=json.dumps({"revision_id": draft.pk, "elements": elements}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                element["style"]["label_visible"]
                for element in self.client.get(data_url, {"draft": "1"}).json()["elements"]
            ],
            [True, False],
        )
        response = self.client.post(
            reverse(
                "plugins:solomon_facilities:floorplan_publish",
                kwargs={"pk": self.plan.pk},
            ),
            {"revision_id": draft.pk},
        )
        self.assertEqual(response.status_code, 302)
        published = self.client.get(data_url).json()["elements"]
        self.assertEqual(
            [item["label"] for item in published], ["Visible room", "Hidden room"]
        )
        self.assertEqual(
            [item["style"]["label_visible"] for item in published], [True, False]
        )
        editor_url = reverse(
            "plugins:solomon_facilities:floorplan_draw", kwargs={"pk": self.plan.pk}
        )
        response = self.client.get(editor_url, HTTP_ACCEPT_LANGUAGE="cs")
        self.assertContains(response, "Zobrazit popisek na půdorysu")
        copied = self.client.get(data_url, {"draft": "1"}).json()["elements"]
        self.assertEqual(
            [item["style"]["label_visible"] for item in copied], [True, False]
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

    def test_editor_save_sequence_activates_saved_revision(self):
        grant_object_permission(self.user, FloorPlan, "change")
        grant_object_permission(self.user, PlanRevision, "change")
        editor_url = reverse(
            "plugins:solomon_facilities:floorplan_draw", kwargs={"pk": self.plan.pk}
        )
        self.assertEqual(self.client.get(editor_url).status_code, 200)
        draft = self.plan.revisions.get(status="draft")
        data_url = reverse(
            "plugins:solomon_facilities:floorplan_data", kwargs={"pk": self.plan.pk}
        )
        save_response = self.client.put(
            data_url,
            data=json.dumps(
                {
                    "revision_id": draft.pk,
                    "elements": [
                        {
                            "element_type": "wall",
                            "geometry": {
                                "type": "line",
                                "x1": 10,
                                "y1": 20,
                                "x2": 190,
                                "y2": 20,
                            },
                            "style": {"stroke_width": 7, "scale_x": 1.5},
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(save_response.status_code, 200)

        publish_response = self.client.post(
            reverse(
                "plugins:solomon_facilities:floorplan_publish",
                kwargs={"pk": self.plan.pk},
            ),
            {"revision_id": draft.pk},
        )

        self.assertRedirects(publish_response, self.plan.get_absolute_url())
        self.plan.refresh_from_db()
        draft.refresh_from_db()
        self.assertEqual(self.plan.active_revision, draft)
        self.assertEqual(draft.status, "published")
        self.assertEqual(draft.elements.get().geometry["x2"], 190)

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
