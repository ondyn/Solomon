"""NetBox and interactive schematic views for Solomon Facilities."""

import json

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import layout
from netbox.ui.panels import ContextTablePanel
from netbox.views import generic
from netbox.views.generic import ObjectChangeLogView
from solomon_property.models import Building, Flat, PropertyOwner
from utilities.views import ViewTab, register_model_view

from . import filtersets, forms, models, tables
from .ui.panels import (
    DoorPanel,
    KeyCopyPanel,
    KeyProfilePanel,
    SpacePanel,
    TechnicalAssetPanel,
    TechnicalSystemPanel,
)


class FacilitiesObjectChangeLogView(ObjectChangeLogView):
    base_template = "generic/object.html"


class BuildingLevelListView(generic.ObjectListView):
    queryset = models.BuildingLevel.objects.select_related("building_object")
    table = tables.BuildingLevelTable
    filterset = filtersets.BuildingLevelFilterSet


class BuildingLevelEditView(generic.ObjectEditView):
    queryset = models.BuildingLevel.objects.all()
    form = forms.BuildingLevelForm


class BuildingLevelDeleteView(generic.ObjectDeleteView):
    queryset = models.BuildingLevel.objects.all()


class FloorPlanListView(generic.ObjectListView):
    queryset = models.FloorPlan.objects.select_related(
        "level__building_object", "active_revision"
    )
    table = tables.FloorPlanTable
    filterset = filtersets.FloorPlanFilterSet


class FloorPlanView(generic.ObjectView):
    queryset = models.FloorPlan.objects.select_related(
        "level__building_object", "active_revision"
    )
    template_name = "solomon_facilities/floorplan.html"

    def get_extra_context(self, request, instance):
        revision = _display_revision(instance)
        can_edit = request.user.has_perms(
            (
                "solomon_facilities.change_floorplan",
                "solomon_facilities.change_planrevision",
            )
        )
        if revision is None and can_edit:
            revision = (
                instance.revisions.filter(status="draft").order_by("-revision").first()
            )
        return {"revision": revision}


class FloorPlanEditView(generic.ObjectEditView):
    queryset = models.FloorPlan.objects.all()
    form = forms.FloorPlanForm


class FloorPlanDeleteView(generic.ObjectDeleteView):
    queryset = models.FloorPlan.objects.all()


class PlanRevisionEditView(generic.ObjectEditView):
    queryset = models.PlanRevision.objects.filter(status="draft")
    form = forms.PlanRevisionForm


class FloorPlanEditorView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = (
        "solomon_facilities.change_floorplan",
        "solomon_facilities.change_planrevision",
    )

    def get(self, request, pk):
        plan = get_object_or_404(
            models.FloorPlan.objects.select_related(
                "level__building_object", "active_revision"
            ),
            pk=pk,
        )
        revision = plan.revisions.filter(status="draft").order_by("-revision").first()
        if revision is None:
            next_revision = (
                plan.revisions.aggregate(Max("revision"))["revision__max"] or 0
            ) + 1
            source = plan.active_revision
            revision = models.PlanRevision.objects.create(
                plan=plan,
                revision=next_revision,
                source_file=source.source_file.name
                if source and source.source_file
                else "",
                background_file=(
                    source.background_file.name
                    if source and source.background_file
                    else ""
                ),
                background_rotation=source.background_rotation if source else 0,
                source_page=source.source_page if source else None,
                scale_denominator=source.scale_denominator if source else None,
                source_note=source.source_note if source else "",
            )
            if source:
                for element in source.elements.all():
                    models.PlanElement.objects.create(
                        revision=revision,
                        element_type=element.element_type,
                        label=element.label,
                        geometry=element.geometry,
                        style=element.style,
                        z_index=element.z_index,
                        locked=element.locked,
                        space=element.space,
                        door=element.door,
                        technical_asset=element.technical_asset,
                    )
        return render(
            request,
            "solomon_facilities/floorplan_editor.html",
            {"object": plan, "plan": plan, "revision": revision},
        )


class FloorPlanPublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "solomon_facilities.change_planrevision"

    def post(self, request, pk):
        plan = get_object_or_404(models.FloorPlan, pk=pk)
        revision = get_object_or_404(
            models.PlanRevision,
            pk=request.POST.get("revision_id"),
            plan=plan,
            status="draft",
        )
        with transaction.atomic():
            revision.status = "published"
            revision.save()
            plan.active_revision = revision
            plan.save()
        return redirect(plan)


class FloorPlanDataView(LoginRequiredMixin, View):
    """Read or atomically replace canonical elements in one draft revision."""

    def dispatch(self, request, *args, **kwargs):
        permission = (
            "solomon_facilities.view_floorplan"
            if request.method == "GET"
            else "solomon_facilities.change_planrevision"
        )
        if not request.user.has_perm(permission):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        plan = get_object_or_404(
            models.FloorPlan.objects.select_related("level", "active_revision"), pk=pk
        )
        revision = (
            plan.revisions.filter(status="draft").order_by("-revision").first()
            if request.GET.get("draft") == "1"
            else _display_revision(plan)
        )
        if revision is None:
            return JsonResponse({"detail": _("This plan has no revision.")}, status=404)
        return JsonResponse(_serialize_plan(request, plan, revision))

    def put(self, request, pk):
        plan = get_object_or_404(models.FloorPlan, pk=pk)
        try:
            payload = json.loads(request.body)
        except (TypeError, ValueError, UnicodeDecodeError):
            return JsonResponse({"detail": _("Invalid JSON payload.")}, status=400)

        elements = payload.get("elements")
        if not isinstance(elements, list):
            return JsonResponse(
                {"detail": _("Elements must be a JSON array.")}, status=400
            )
        if len(elements) > 5000:
            return JsonResponse(
                {"detail": _("A revision may contain at most 5000 elements.")},
                status=400,
            )

        revision = get_object_or_404(
            models.PlanRevision,
            pk=payload.get("revision_id"),
            plan=plan,
            status="draft",
        )
        saved = []
        try:
            with transaction.atomic():
                revision.elements.all().delete()
                for index, item in enumerate(elements):
                    element = models.PlanElement(
                        revision=revision,
                        element_type=item.get("element_type"),
                        label=item.get("label", ""),
                        geometry=item.get("geometry", {}),
                        style=item.get("style", {}),
                        z_index=item.get("z_index", index),
                        locked=bool(item.get("locked", False)),
                        space_id=item.get("space_id"),
                        door_id=item.get("door_id"),
                        technical_asset_id=item.get("technical_asset_id"),
                    )
                    element.full_clean()
                    element.save()
                    saved.append(element.pk)
        except (ValidationError, ObjectDoesNotExist, TypeError, ValueError) as error:
            message = (
                getattr(error, "message_dict", None)
                or getattr(error, "messages", None)
                or str(error)
            )
            return JsonResponse({"detail": message}, status=400)

        return JsonResponse({"revision_id": revision.pk, "element_ids": saved})


def _display_revision(plan):
    if plan.active_revision_id:
        return plan.active_revision
    return plan.revisions.filter(status="published").order_by("-revision").first()


def _serialize_plan(request, plan, revision):
    level = plan.level
    can_view_people = request.user.has_perm("solomon_property.view_person")
    can_view_owners = request.user.has_perm("solomon_property.view_propertyowner")
    can_view_keys = request.user.has_perm("solomon_facilities.view_keyprofile")

    spaces = {}
    space_queryset = level.spaces.select_related("building").prefetch_related(
        "flat_assignments__flat__building", "usages__person", "usages__owner"
    )
    for space in space_queryset:
        assignments = [
            {
                "flat": str(assignment.flat),
                "role": assignment.get_role_display(),
                "url": assignment.flat.get_absolute_url(),
            }
            for assignment in space.flat_assignments.all()
            if assignment.is_current
        ]
        usages = []
        for usage in space.usages.all():
            if not usage.is_current:
                continue
            holder = None
            holder_url = None
            if usage.person_id and can_view_people:
                holder = str(usage.person)
                holder_url = usage.person.get_absolute_url()
            elif usage.owner_id and can_view_owners:
                holder = str(usage.owner)
                holder_url = usage.owner.get_absolute_url()
            if holder:
                usages.append(
                    {
                        "holder": holder,
                        "url": holder_url,
                        "type": usage.get_usage_type_display(),
                    }
                )
        spaces[str(space.pk)] = {
            "id": space.pk,
            "label": str(space),
            "url": space.get_absolute_url(),
            "kind": space.kind,
            "kind_label": space.get_kind_display(),
            "area_m2": str(space.area_m2) if space.area_m2 is not None else None,
            "assignments": assignments,
            "usages": usages,
        }

    doors = {}
    for door in level.doors.prefetch_related("locks__key_profiles"):
        lock_data = []
        if can_view_keys:
            lock_data = [
                {
                    "name": str(lock),
                    "keys": [
                        {"label": str(profile), "url": profile.get_absolute_url()}
                        for profile in lock.key_profiles.all()
                    ],
                }
                for lock in door.locks.all()
            ]
        doors[str(door.pk)] = {
            "id": door.pk,
            "label": str(door),
            "url": door.get_absolute_url(),
            "type": door.get_door_type_display(),
            "locks": lock_data,
        }

    assets = {}
    for asset in level.technical_assets.select_related(
        "system", "space"
    ).prefetch_related("serves_flats", "serves_spaces"):
        assets[str(asset.pk)] = {
            "id": asset.pk,
            "label": str(asset),
            "url": asset.get_absolute_url(),
            "type": asset.asset_type,
            "system": asset.system.get_kind_display(),
            "space": str(asset.space) if asset.space_id else None,
            "serves_flats": [str(flat) for flat in asset.serves_flats.all()],
            "emergency_instructions": asset.emergency_instructions,
        }

    serialized_elements = []
    for element in revision.elements.select_related("space", "door", "technical_asset"):
        serialized_elements.append(
            {
                "id": element.pk,
                "element_type": element.element_type,
                "label": element.label,
                "geometry": element.geometry,
                "style": element.style,
                "z_index": element.z_index,
                "locked": element.locked,
                "space_id": element.space_id,
                "door_id": element.door_id,
                "technical_asset_id": element.technical_asset_id,
            }
        )

    return {
        "plan": {
            "id": plan.pk,
            "name": plan.name,
            "width": float(plan.width),
            "height": float(plan.height),
            "measurement_unit": plan.measurement_unit,
        },
        "revision": {
            "id": revision.pk,
            "number": revision.revision,
            "status": revision.status,
            "source_url": revision.source_file.url if revision.source_file else None,
            "background_url": revision.background_file.url
            if revision.background_file
            else None,
            "background_rotation": revision.background_rotation,
        },
        "elements": serialized_elements,
        "targets": {"spaces": spaces, "doors": doors, "technical_assets": assets},
    }


class SpaceListView(generic.ObjectListView):
    queryset = models.Space.objects.select_related("level", "building")
    table = tables.SpaceTable
    filterset = filtersets.SpaceFilterSet


class SpaceView(generic.ObjectView):
    queryset = models.Space.objects.select_related("level", "building", "parent")
    template_name = "generic/object.html"
    layout = layout.SimpleLayout(
        left_panels=[SpacePanel(), CustomFieldsPanel(), TagsPanel()],
        bottom_panels=[
            ContextTablePanel(table="assignment_table", title=_("Flat assignments")),
            ContextTablePanel(table="usage_table", title=_("Rentals and occupancy")),
            ContextTablePanel(table="asset_table", title=_("Technical assets")),
        ],
    )

    def get_extra_context(self, request, instance):
        assignment_table = tables.SpaceFlatAssignmentTable(
            instance.flat_assignments.all()
        )
        usage_table = tables.SpaceUsageTable(instance.usages.all())
        asset_table = tables.TechnicalAssetTable(instance.technical_assets.all())
        for table in (assignment_table, usage_table, asset_table):
            table.configure(request)
        return {
            "assignment_table": assignment_table,
            "usage_table": usage_table,
            "asset_table": asset_table,
        }


class SpaceEditView(generic.ObjectEditView):
    queryset = models.Space.objects.all()
    form = forms.SpaceForm


class SpaceDeleteView(generic.ObjectDeleteView):
    queryset = models.Space.objects.all()


class SpaceFlatAssignmentListView(generic.ObjectListView):
    queryset = models.SpaceFlatAssignment.objects.select_related("space", "flat")
    table = tables.SpaceFlatAssignmentTable


class SpaceFlatAssignmentEditView(generic.ObjectEditView):
    queryset = models.SpaceFlatAssignment.objects.all()
    form = forms.SpaceFlatAssignmentForm


class SpaceFlatAssignmentDeleteView(generic.ObjectDeleteView):
    queryset = models.SpaceFlatAssignment.objects.all()


class SpaceUsageListView(generic.ObjectListView):
    queryset = models.SpaceUsage.objects.select_related("space", "person", "owner")
    table = tables.SpaceUsageTable


class SpaceUsageEditView(generic.ObjectEditView):
    queryset = models.SpaceUsage.objects.all()
    form = forms.SpaceUsageForm


class SpaceUsageDeleteView(generic.ObjectDeleteView):
    queryset = models.SpaceUsage.objects.all()


class DoorListView(generic.ObjectListView):
    queryset = models.Door.objects.select_related("level", "from_space", "to_space")
    table = tables.DoorTable
    filterset = filtersets.DoorFilterSet


class DoorView(generic.ObjectView):
    queryset = models.Door.objects.select_related("level", "from_space", "to_space")
    template_name = "generic/object.html"
    layout = layout.SimpleLayout(
        left_panels=[DoorPanel(), CustomFieldsPanel(), TagsPanel()],
        bottom_panels=[
            ContextTablePanel(table="lock_table", title=_("Lock cylinders"))
        ],
    )

    def get_extra_context(self, request, instance):
        lock_table = tables.LockCylinderTable(instance.locks.all())
        lock_table.configure(request)
        return {"lock_table": lock_table}


class DoorEditView(generic.ObjectEditView):
    queryset = models.Door.objects.all()
    form = forms.DoorForm


class DoorDeleteView(generic.ObjectDeleteView):
    queryset = models.Door.objects.all()


class LockCylinderListView(generic.ObjectListView):
    queryset = models.LockCylinder.objects.select_related("door")
    table = tables.LockCylinderTable


class LockCylinderEditView(generic.ObjectEditView):
    queryset = models.LockCylinder.objects.all()
    form = forms.LockCylinderForm


class LockCylinderDeleteView(generic.ObjectDeleteView):
    queryset = models.LockCylinder.objects.all()


class KeyProfileListView(generic.ObjectListView):
    queryset = models.KeyProfile.objects.select_related(
        "building_object"
    ).prefetch_related("copies")
    table = tables.KeyProfileTable
    filterset = filtersets.KeyProfileFilterSet


class KeyProfileView(generic.ObjectView):
    queryset = models.KeyProfile.objects.select_related(
        "building_object"
    ).prefetch_related("copies", "keyprofilelock_set__lock__door")
    template_name = "generic/object.html"
    layout = layout.SimpleLayout(
        left_panels=[KeyProfilePanel(), CustomFieldsPanel(), TagsPanel()],
        bottom_panels=[
            ContextTablePanel(table="copy_table", title=_("Physical copies")),
            ContextTablePanel(table="lock_table", title=_("Locks opened")),
        ],
    )

    def get_extra_context(self, request, instance):
        copy_table = tables.KeyCopyTable(instance.copies.all())
        lock_table = tables.KeyProfileLockTable(instance.keyprofilelock_set.all())
        copy_table.configure(request)
        lock_table.configure(request)
        return {"copy_table": copy_table, "lock_table": lock_table}


class KeyProfileEditView(generic.ObjectEditView):
    queryset = models.KeyProfile.objects.all()
    form = forms.KeyProfileForm


class KeyProfileDeleteView(generic.ObjectDeleteView):
    queryset = models.KeyProfile.objects.all()


class KeyCopyListView(generic.ObjectListView):
    queryset = models.KeyCopy.objects.select_related("profile")
    table = tables.KeyCopyTable
    filterset = filtersets.KeyCopyFilterSet


class KeyCopyView(generic.ObjectView):
    queryset = models.KeyCopy.objects.select_related("profile")
    template_name = "generic/object.html"
    layout = layout.SimpleLayout(
        left_panels=[KeyCopyPanel(), CustomFieldsPanel(), TagsPanel()],
        bottom_panels=[
            ContextTablePanel(table="issue_table", title=_("Custody history"))
        ],
    )

    def get_extra_context(self, request, instance):
        issue_table = tables.KeyIssueTable(instance.issues.select_related("person"))
        issue_table.configure(request)
        return {"issue_table": issue_table}


class KeyCopyEditView(generic.ObjectEditView):
    queryset = models.KeyCopy.objects.all()
    form = forms.KeyCopyForm


class KeyCopyDeleteView(generic.ObjectDeleteView):
    queryset = models.KeyCopy.objects.all()


class KeyIssueListView(generic.ObjectListView):
    queryset = models.KeyIssue.objects.select_related("key_copy", "person")
    table = tables.KeyIssueTable


class KeyIssueEditView(generic.ObjectEditView):
    queryset = models.KeyIssue.objects.all()
    form = forms.KeyIssueForm


class KeyIssueDeleteView(generic.ObjectDeleteView):
    queryset = models.KeyIssue.objects.all()


class TechnicalSystemListView(generic.ObjectListView):
    queryset = models.TechnicalSystem.objects.select_related("building_object")
    table = tables.TechnicalSystemTable
    filterset = filtersets.TechnicalSystemFilterSet


class TechnicalSystemView(generic.ObjectView):
    queryset = models.TechnicalSystem.objects.select_related("building_object")
    template_name = "generic/object.html"
    layout = layout.SimpleLayout(
        left_panels=[TechnicalSystemPanel(), CustomFieldsPanel(), TagsPanel()],
        bottom_panels=[ContextTablePanel(table="asset_table", title=_("Components"))],
    )

    def get_extra_context(self, request, instance):
        asset_table = tables.TechnicalAssetTable(instance.assets.all())
        asset_table.configure(request)
        return {"asset_table": asset_table}


class TechnicalSystemEditView(generic.ObjectEditView):
    queryset = models.TechnicalSystem.objects.all()
    form = forms.TechnicalSystemForm


class TechnicalSystemDeleteView(generic.ObjectDeleteView):
    queryset = models.TechnicalSystem.objects.all()


class TechnicalAssetListView(generic.ObjectListView):
    queryset = models.TechnicalAsset.objects.select_related("system", "level", "space")
    table = tables.TechnicalAssetTable
    filterset = filtersets.TechnicalAssetFilterSet


class TechnicalAssetView(generic.ObjectView):
    queryset = models.TechnicalAsset.objects.select_related(
        "system", "parent", "level", "space"
    )
    template_name = "generic/object.html"
    layout = layout.SimpleLayout(
        left_panels=[TechnicalAssetPanel(), CustomFieldsPanel(), TagsPanel()],
        bottom_panels=[
            ContextTablePanel(
                table="outgoing_table", title=_("Downstream relationships")
            ),
            ContextTablePanel(
                table="incoming_table", title=_("Upstream relationships")
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        outgoing_table = tables.TechnicalConnectionTable(
            instance.outgoing_connections.all()
        )
        incoming_table = tables.TechnicalConnectionTable(
            instance.incoming_connections.all()
        )
        outgoing_table.configure(request)
        incoming_table.configure(request)
        return {"outgoing_table": outgoing_table, "incoming_table": incoming_table}


class TechnicalAssetEditView(generic.ObjectEditView):
    queryset = models.TechnicalAsset.objects.all()
    form = forms.TechnicalAssetForm


class TechnicalAssetDeleteView(generic.ObjectDeleteView):
    queryset = models.TechnicalAsset.objects.all()


class TechnicalConnectionListView(generic.ObjectListView):
    queryset = models.TechnicalConnection.objects.select_related(
        "from_asset", "to_asset"
    )
    table = tables.TechnicalConnectionTable


class TechnicalConnectionEditView(generic.ObjectEditView):
    queryset = models.TechnicalConnection.objects.all()
    form = forms.TechnicalConnectionForm


class TechnicalConnectionDeleteView(generic.ObjectDeleteView):
    queryset = models.TechnicalConnection.objects.all()


class SchematicTabMixin:
    template_name = "solomon_facilities/object_schematics.html"
    tab = ViewTab(
        label=_("Schematics"),
        hide_if_empty=False,
        permission="solomon_facilities.view_floorplan",
    )


@register_model_view(Building, name="schematics")
class BuildingSchematicsView(SchematicTabMixin, generic.ObjectView):
    queryset = Building.objects.select_related("building_object")

    def get_extra_context(self, request, instance):
        plans = models.FloorPlan.objects.filter(
            level__building_object=instance.building_object
        ).select_related("level", "active_revision")
        return {"plans": plans, "related_flats": (), "highlight_space_ids": ()}


@register_model_view(Flat, name="schematics")
class FlatSchematicsView(SchematicTabMixin, generic.ObjectView):
    queryset = Flat.objects.select_related("building__building_object")

    def get_extra_context(self, request, instance):
        assignments = instance.space_assignments.filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=timezone.localdate())
        ).select_related("space__level")
        level_ids = {assignment.space.level_id for assignment in assignments}
        plans = models.FloorPlan.objects.filter(
            Q(level_id__in=level_ids)
            | Q(
                level__building_object=instance.building.building_object,
                level__number=instance.floor,
            )
        ).select_related("level", "active_revision")
        return {
            "plans": plans.distinct(),
            "related_flats": (instance,),
            "highlight_space_ids": [assignment.space_id for assignment in assignments],
        }


@register_model_view(PropertyOwner, name="schematics")
class OwnerSchematicsView(SchematicTabMixin, generic.ObjectView):
    queryset = PropertyOwner.objects.all()

    def get_extra_context(self, request, instance):
        flats = Flat.objects.filter(
            flat_owners__owner=instance,
            flat_owners__effective_to__isnull=True,
        ).select_related("building__building_object")
        assignments = models.SpaceFlatAssignment.objects.filter(
            flat__in=flats,
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=timezone.localdate())
        )
        level_ids = set(assignments.values_list("space__level_id", flat=True))
        for flat in flats:
            level_ids.update(
                models.BuildingLevel.objects.filter(
                    building_object=flat.building.building_object,
                    number=flat.floor,
                ).values_list("pk", flat=True)
            )
        plans = models.FloorPlan.objects.filter(level_id__in=level_ids).select_related(
            "level", "active_revision"
        )
        return {
            "plans": plans,
            "related_flats": flats,
            "highlight_space_ids": list(assignments.values_list("space_id", flat=True)),
        }
