"""
Solomon — CUZK Import views.

Workflow:
1. User enters a CUZK building ID (or searches by address).
2. System fetches building + units data from CUZK API.
3. User sees a preview/diff: what will be created, updated, or skipped.
4. User selects which items to import and what action to take for each.
5. System executes the import based on user's decisions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views import View

from buildings.models import Building
from flats.models import Flat

from .cuzk_service import CUZKApiError, CUZKBuilding, CUZKClient, CUZKUnit

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Import diff data structures
# ---------------------------------------------------------------------------
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_SKIP = "skip"

ACTION_CHOICES = [
    (ACTION_CREATE, _lazy("Create new")),
    (ACTION_UPDATE, _lazy("Update existing")),
    (ACTION_SKIP, _lazy("Skip")),
]


@dataclass
class FieldDiff:
    """Difference for a single field."""

    field_name: str
    field_label: str
    current_value: Any
    new_value: Any

    @property
    def is_changed(self) -> bool:
        return str(self.current_value) != str(self.new_value)


@dataclass
class BuildingDiff:
    """Comparison between CUZK data and existing building."""

    cuzk_building: CUZKBuilding
    existing_building: Building | None
    suggested_action: str
    field_diffs: list[FieldDiff]


@dataclass
class UnitDiff:
    """Comparison between CUZK unit and existing flat."""

    cuzk_unit: CUZKUnit
    existing_flat: Flat | None
    suggested_action: str
    field_diffs: list[FieldDiff]


# ---------------------------------------------------------------------------
#  Diff computation
# ---------------------------------------------------------------------------
def compute_building_diff(cuzk_building: CUZKBuilding, building: Building | None) -> BuildingDiff:
    """Compare CUZK building data with an existing Building record."""
    diffs: list[FieldDiff] = []
    house_number_str = str(cuzk_building.house_numbers[0]) if cuzk_building.house_numbers else ""

    if building:
        diffs.append(FieldDiff(
            "house_number", _("House number"),
            building.house_number, house_number_str,
        ))
        diffs.append(FieldDiff(
            "city", _("City"),
            building.city, cuzk_building.municipality_name,
        ))
        lv_number = cuzk_building.lv.number if cuzk_building.lv else None
        diffs.append(FieldDiff(
            "cuzk_lv_number", _("Title deed number (LV)"),
            building.cuzk_lv_number, lv_number,
        ))
        has_changes = any(d.is_changed for d in diffs)
        action = ACTION_UPDATE if has_changes else ACTION_SKIP
    else:
        diffs.append(FieldDiff("house_number", _("House number"), "—", house_number_str))
        diffs.append(FieldDiff("city", _("City"), "—", cuzk_building.municipality_name))
        lv_number = cuzk_building.lv.number if cuzk_building.lv else None
        diffs.append(FieldDiff("cuzk_lv_number", _("Title deed number (LV)"), "—", lv_number))
        action = ACTION_CREATE

    return BuildingDiff(
        cuzk_building=cuzk_building,
        existing_building=building,
        suggested_action=action,
        field_diffs=diffs,
    )


def compute_unit_diff(cuzk_unit: CUZKUnit, flat: Flat | None) -> UnitDiff:
    """Compare CUZK unit data with an existing Flat record."""
    diffs: list[FieldDiff] = []
    # Extract the modulo number for display (CUZK uses compound unit numbers)
    unit_number_display = str(cuzk_unit.unit_number % 10000) if cuzk_unit.unit_number > 9999 else str(cuzk_unit.unit_number)
    share_num = cuzk_unit.share.numerator if cuzk_unit.share else None
    share_den = cuzk_unit.share.denominator if cuzk_unit.share else None

    if flat:
        diffs.append(FieldDiff(
            "flat_number", _("Flat number"),
            flat.flat_number, unit_number_display,
        ))
        diffs.append(FieldDiff(
            "cuzk_share_numerator", _("Share numerator (common parts)"),
            flat.cuzk_share_numerator, share_num,
        ))
        diffs.append(FieldDiff(
            "cuzk_share_denominator", _("Share denominator (common parts)"),
            flat.cuzk_share_denominator, share_den,
        ))
        has_changes = any(d.is_changed for d in diffs)
        action = ACTION_UPDATE if has_changes else ACTION_SKIP
    else:
        diffs.append(FieldDiff("flat_number", _("Flat number"), "—", unit_number_display))
        diffs.append(FieldDiff("cuzk_share_numerator", _("Share numerator (common parts)"), "—", share_num))
        diffs.append(FieldDiff("cuzk_share_denominator", _("Share denominator (common parts)"), "—", share_den))
        action = ACTION_CREATE

    return UnitDiff(
        cuzk_unit=cuzk_unit,
        existing_flat=flat,
        suggested_action=action,
        field_diffs=diffs,
    )


def build_import_preview(
    cuzk_building: CUZKBuilding,
    cuzk_units: list[CUZKUnit],
    target_building: Building | None = None,
) -> tuple[BuildingDiff, list[UnitDiff]]:
    """
    Build a full preview of what will be imported.

    If target_building is given, tries to match units to existing flats
    (by cuzk_unit_id or by flat_number).
    """
    # Try to find existing building by CUZK ID
    if target_building is None:
        target_building = Building.objects.filter(cuzk_building_id=cuzk_building.id).first()

    building_diff = compute_building_diff(cuzk_building, target_building)

    unit_diffs: list[UnitDiff] = []
    for cuzk_unit in cuzk_units:
        existing_flat = None
        if target_building:
            # Match by CUZK ID first, then by flat number
            existing_flat = Flat.objects.filter(
                building=target_building,
                cuzk_unit_id=cuzk_unit.id,
            ).first()
            if not existing_flat:
                unit_num = str(cuzk_unit.unit_number % 10000) if cuzk_unit.unit_number > 9999 else str(cuzk_unit.unit_number)
                existing_flat = Flat.objects.filter(
                    building=target_building,
                    flat_number=unit_num,
                ).first()
        unit_diffs.append(compute_unit_diff(cuzk_unit, existing_flat))

    return building_diff, unit_diffs


# ---------------------------------------------------------------------------
#  Import execution
# ---------------------------------------------------------------------------
@transaction.atomic
def execute_import(
    building_diff: BuildingDiff,
    building_action: str,
    unit_diffs: list[UnitDiff],
    unit_actions: dict[int, str],
) -> dict[str, int]:
    """
    Execute the import based on user decisions.

    Returns a summary dict with counts of created/updated/skipped items.
    """
    stats = {"buildings_created": 0, "buildings_updated": 0, "flats_created": 0, "flats_updated": 0, "skipped": 0}
    cuzk_b = building_diff.cuzk_building
    building = building_diff.existing_building
    house_number_str = str(cuzk_b.house_numbers[0]) if cuzk_b.house_numbers else ""
    lv_number = cuzk_b.lv.number if cuzk_b.lv else None

    if building_action == ACTION_CREATE:
        building = Building.objects.create(
            name=f"{cuzk_b.city_part_name} {house_number_str}".strip(),
            street=cuzk_b.city_part_name,
            house_number=house_number_str,
            city=cuzk_b.municipality_name,
            postal_code="",
            cuzk_building_id=cuzk_b.id,
            cuzk_lv_number=lv_number,
        )
        stats["buildings_created"] = 1
    elif building_action == ACTION_UPDATE and building:
        building.house_number = house_number_str
        building.city = cuzk_b.municipality_name
        building.cuzk_building_id = cuzk_b.id
        building.cuzk_lv_number = lv_number
        building.save()
        stats["buildings_updated"] = 1
    else:
        stats["skipped"] += 1

    # Process units only if we have a building to attach them to
    if building:
        for udiff in unit_diffs:
            action = unit_actions.get(udiff.cuzk_unit.id, ACTION_SKIP)
            cu = udiff.cuzk_unit
            unit_num = str(cu.unit_number % 10000) if cu.unit_number > 9999 else str(cu.unit_number)
            share_num = cu.share.numerator if cu.share else None
            share_den = cu.share.denominator if cu.share else None

            if action == ACTION_CREATE:
                Flat.objects.create(
                    building=building,
                    flat_number=unit_num,
                    cuzk_unit_id=cu.id,
                    cuzk_share_numerator=share_num,
                    cuzk_share_denominator=share_den,
                )
                stats["flats_created"] += 1
            elif action == ACTION_UPDATE and udiff.existing_flat:
                flat = udiff.existing_flat
                flat.cuzk_unit_id = cu.id
                flat.cuzk_share_numerator = share_num
                flat.cuzk_share_denominator = share_den
                flat.save()
                stats["flats_updated"] += 1
            else:
                stats["skipped"] += 1

    return stats


# ---------------------------------------------------------------------------
#  Views
# ---------------------------------------------------------------------------
class CUZKImportSearchView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Step 1: User enters a CUZK building ID to start the import.
    """

    permission_required = "buildings.add_building"
    template_name = "core/cuzk_import_search.html"

    def get(self, request):
        buildings = Building.objects.all().order_by("name")
        return render(request, self.template_name, {
            "title": _("CUZK Import"),
            "buildings": buildings,
        })

    def post(self, request):
        building_id_str = request.POST.get("cuzk_building_id", "").strip()
        target_building_pk = request.POST.get("target_building", "").strip()

        if not building_id_str:
            messages.error(request, _("Please enter a CUZK building ID."))
            return render(request, self.template_name, {"title": _("CUZK Import")})

        try:
            building_id = int(building_id_str)
        except (ValueError, TypeError):
            messages.error(request, _("Invalid CUZK building ID."))
            return render(request, self.template_name, {"title": _("CUZK Import")})

        # Fetch data from CUZK
        client = CUZKClient()
        try:
            cuzk_building, cuzk_units = client.get_building_with_units(building_id)
        except CUZKApiError as exc:
            messages.error(request, _("CUZK API error: %(detail)s") % {"detail": exc.detail})
            return render(request, self.template_name, {"title": _("CUZK Import")})

        # Optionally link to an existing building
        target_building = None
        if target_building_pk:
            target_building = Building.objects.filter(pk=target_building_pk).first()

        # Compute diff/preview
        building_diff, unit_diffs = build_import_preview(cuzk_building, cuzk_units, target_building)

        # Store the fetched data in session for the next step
        request.session["cuzk_import_data"] = {
            "cuzk_building": _serialize_cuzk_building(cuzk_building),
            "cuzk_units": [_serialize_cuzk_unit(u) for u in cuzk_units],
            "target_building_pk": str(target_building.pk) if target_building else None,
        }

        return redirect(reverse("core:cuzk-import-preview"))


class CUZKImportPreviewView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Step 2: Show preview/diff and let user decide actions.
    """

    permission_required = "buildings.add_building"
    template_name = "core/cuzk_import_preview.html"

    def get(self, request):
        import_data = request.session.get("cuzk_import_data")
        if not import_data:
            messages.warning(request, _("No import data found. Please start a new import."))
            return redirect(reverse("core:cuzk-import-search"))

        cuzk_building = _deserialize_cuzk_building(import_data["cuzk_building"])
        cuzk_units = [_deserialize_cuzk_unit(u) for u in import_data["cuzk_units"]]

        target_building = None
        if import_data.get("target_building_pk"):
            target_building = Building.objects.filter(pk=import_data["target_building_pk"]).first()

        building_diff, unit_diffs = build_import_preview(cuzk_building, cuzk_units, target_building)

        return render(request, self.template_name, {
            "title": _("CUZK Import — Preview"),
            "building_diff": building_diff,
            "unit_diffs": unit_diffs,
            "action_choices": ACTION_CHOICES,
            "buildings": Building.objects.all().order_by("name"),
        })

    def post(self, request):
        """Execute the import based on user's action selections."""
        import_data = request.session.get("cuzk_import_data")
        if not import_data:
            messages.warning(request, _("No import data found. Please start a new import."))
            return redirect(reverse("core:cuzk-import-search"))

        cuzk_building = _deserialize_cuzk_building(import_data["cuzk_building"])
        cuzk_units = [_deserialize_cuzk_unit(u) for u in import_data["cuzk_units"]]

        target_building = None
        if import_data.get("target_building_pk"):
            target_building = Building.objects.filter(pk=import_data["target_building_pk"]).first()

        building_diff, unit_diffs = build_import_preview(cuzk_building, cuzk_units, target_building)

        # Get user's action decisions
        building_action = request.POST.get("building_action", ACTION_SKIP)
        unit_actions: dict[int, str] = {}
        for udiff in unit_diffs:
            action_key = f"unit_action_{udiff.cuzk_unit.id}"
            unit_actions[udiff.cuzk_unit.id] = request.POST.get(action_key, ACTION_SKIP)

        # Execute import
        try:
            stats = execute_import(building_diff, building_action, unit_diffs, unit_actions)
        except Exception:
            logger.exception("CUZK import failed")
            messages.error(request, _("Import failed. Please check the logs."))
            return redirect(reverse("core:cuzk-import-search"))

        # Clean up session
        del request.session["cuzk_import_data"]

        # Success message
        msg_parts = []
        if stats["buildings_created"]:
            msg_parts.append(_("%(count)d building(s) created") % {"count": stats["buildings_created"]})
        if stats["buildings_updated"]:
            msg_parts.append(_("%(count)d building(s) updated") % {"count": stats["buildings_updated"]})
        if stats["flats_created"]:
            msg_parts.append(_("%(count)d flat(s) created") % {"count": stats["flats_created"]})
        if stats["flats_updated"]:
            msg_parts.append(_("%(count)d flat(s) updated") % {"count": stats["flats_updated"]})
        if stats["skipped"]:
            msg_parts.append(_("%(count)d item(s) skipped") % {"count": stats["skipped"]})

        messages.success(request, _("Import completed: ") + ", ".join(msg_parts) + ".")

        return redirect(reverse("core:cuzk-import-search"))


# ---------------------------------------------------------------------------
#  Session serialization helpers
# ---------------------------------------------------------------------------
def _serialize_cuzk_building(b: CUZKBuilding) -> dict:
    return {
        "id": b.id,
        "building_type_code": b.building_type_code,
        "building_type_name": b.building_type_name,
        "house_numbers": b.house_numbers,
        "municipality_code": b.municipality_code,
        "municipality_name": b.municipality_name,
        "city_part_code": b.city_part_code,
        "city_part_name": b.city_part_name,
        "usage_code": b.usage_code,
        "usage_name": b.usage_name,
        "lv": {"id": b.lv.id, "number": b.lv.number, "cadastral_territory_code": b.lv.cadastral_territory_code, "cadastral_territory_name": b.lv.cadastral_territory_name} if b.lv else None,
        "unit_refs": [{"id": u.id, "unit_number": u.unit_number} for u in b.unit_refs],
    }


def _deserialize_cuzk_building(data: dict) -> CUZKBuilding:
    from .cuzk_service import CUZKShare, CUZKTitleDeed, CUZKUnitRef

    lv = None
    if data.get("lv"):
        lv = CUZKTitleDeed(**data["lv"])
    return CUZKBuilding(
        id=data["id"],
        building_type_code=data.get("building_type_code"),
        building_type_name=data.get("building_type_name", ""),
        house_numbers=data.get("house_numbers", []),
        municipality_code=data.get("municipality_code"),
        municipality_name=data.get("municipality_name", ""),
        city_part_code=data.get("city_part_code"),
        city_part_name=data.get("city_part_name", ""),
        usage_code=data.get("usage_code"),
        usage_name=data.get("usage_name", ""),
        lv=lv,
        unit_refs=[CUZKUnitRef(**u) for u in data.get("unit_refs", [])],
    )


def _serialize_cuzk_unit(u: CUZKUnit) -> dict:
    return {
        "id": u.id,
        "unit_number": u.unit_number,
        "unit_type_code": u.unit_type_code,
        "unit_type_name": u.unit_type_name,
        "usage_code": u.usage_code,
        "usage_name": u.usage_name,
        "share": {"numerator": u.share.numerator, "denominator": u.share.denominator} if u.share else None,
        "lv": {"id": u.lv.id, "number": u.lv.number, "cadastral_territory_code": u.lv.cadastral_territory_code, "cadastral_territory_name": u.lv.cadastral_territory_name} if u.lv else None,
        "building_id": u.building_id,
    }


def _deserialize_cuzk_unit(data: dict) -> CUZKUnit:
    from .cuzk_service import CUZKShare, CUZKTitleDeed

    share = None
    if data.get("share"):
        share = CUZKShare(**data["share"])
    lv = None
    if data.get("lv"):
        lv = CUZKTitleDeed(**data["lv"])
    return CUZKUnit(
        id=data["id"],
        unit_number=data["unit_number"],
        unit_type_code=data.get("unit_type_code"),
        unit_type_name=data.get("unit_type_name", ""),
        usage_code=data.get("usage_code"),
        usage_name=data.get("usage_name", ""),
        share=share,
        lv=lv,
        building_id=data.get("building_id"),
    )
