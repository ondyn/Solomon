"""
Solomon - CUZK building & flat import logic.

Handles multi-building import from the CUZK API.
One CUZK stavba may map to multiple Solomon Buildings (one per house number).
Units are grouped by house_number extracted from cisloJednotky.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from solomon_property.models import Building, Flat

from .service import (
    CUZKBuilding,
    CUZKUnit,
    group_units_by_house_number,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Action constants
# ---------------------------------------------------------------------------
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_SKIP = "skip"

ACTION_CHOICES = [
    (ACTION_CREATE, _("Create new")),
    (ACTION_UPDATE, _("Update existing")),
    (ACTION_SKIP, _("Skip")),
]


# ---------------------------------------------------------------------------
#  Diff data structures
# ---------------------------------------------------------------------------
@dataclass
class FieldDiff:
    field_name: str
    field_label: str
    current_value: Any
    new_value: Any

    @property
    def is_changed(self) -> bool:
        return str(self.current_value) != str(self.new_value)


@dataclass
class BuildingDiff:
    cuzk_building: CUZKBuilding
    house_number: int
    existing_building: Building | None
    suggested_action: str
    field_diffs: list[FieldDiff]


@dataclass
class UnitDiff:
    cuzk_unit: CUZKUnit
    house_number: int
    existing_flat: Flat | None
    suggested_action: str
    field_diffs: list[FieldDiff]


# ---------------------------------------------------------------------------
#  Diff computation
# ---------------------------------------------------------------------------
def compute_building_diff(
    cuzk_building: CUZKBuilding,
    house_number: int,
    building: Building | None,
) -> BuildingDiff:
    diffs: list[FieldDiff] = []
    house_number_str = str(house_number)
    lv_number = cuzk_building.lv.number if cuzk_building.lv else None

    if building:
        diffs.append(FieldDiff("house_number", _("House number"), building.house_number, house_number_str))
        diffs.append(FieldDiff("city", _("City"), building.city, cuzk_building.municipality_name))
        diffs.append(FieldDiff("cuzk_lv_number", _("Title deed (LV)"), building.cuzk_lv_number, lv_number))
        action = ACTION_UPDATE if any(d.is_changed for d in diffs) else ACTION_SKIP
    else:
        diffs.append(FieldDiff("house_number", _("House number"), "-", house_number_str))
        diffs.append(FieldDiff("city", _("City"), "-", cuzk_building.municipality_name))
        diffs.append(FieldDiff("cuzk_lv_number", _("Title deed (LV)"), "-", lv_number))
        action = ACTION_CREATE

    return BuildingDiff(
        cuzk_building=cuzk_building,
        house_number=house_number,
        existing_building=building,
        suggested_action=action,
        field_diffs=diffs,
    )


def compute_unit_diff(cuzk_unit: CUZKUnit, flat: Flat | None) -> UnitDiff:
    diffs: list[FieldDiff] = []
    unit_num = cuzk_unit.flat_number_in_building
    share_num = cuzk_unit.share.numerator if cuzk_unit.share else None
    share_den = cuzk_unit.share.denominator if cuzk_unit.share else None

    if flat:
        diffs.append(FieldDiff("flat_number", _("Flat number"), flat.flat_number, unit_num))
        diffs.append(FieldDiff("cuzk_share_numerator", _("Share numerator"), flat.cuzk_share_numerator, share_num))
        diffs.append(FieldDiff("cuzk_share_denominator", _("Share denominator"), flat.cuzk_share_denominator, share_den))
        action = ACTION_UPDATE if any(d.is_changed for d in diffs) else ACTION_SKIP
    else:
        diffs.append(FieldDiff("flat_number", _("Flat number"), "-", unit_num))
        diffs.append(FieldDiff("cuzk_share_numerator", _("Share numerator"), "-", share_num))
        diffs.append(FieldDiff("cuzk_share_denominator", _("Share denominator"), "-", share_den))
        action = ACTION_CREATE

    return UnitDiff(
        cuzk_unit=cuzk_unit,
        house_number=cuzk_unit.house_number,
        existing_flat=flat,
        suggested_action=action,
        field_diffs=diffs,
    )


def build_import_preview(
    cuzk_building: CUZKBuilding,
    cuzk_units: list[CUZKUnit],
    target_buildings: dict[int, Building | None] | None = None,
) -> tuple[list[BuildingDiff], list[UnitDiff]]:
    if target_buildings is None:
        target_buildings = {}

    house_numbers = cuzk_building.house_numbers or [0]

    existing_by_hn: dict[int, Building | None] = {}
    for hn in house_numbers:
        if hn in target_buildings and target_buildings[hn] is not None:
            existing_by_hn[hn] = target_buildings[hn]
        else:
            existing = Building.objects.filter(cuzk_building_id=cuzk_building.id, house_number=str(hn)).first()
            if not existing:
                existing = Building.objects.filter(house_number=str(hn), city=cuzk_building.municipality_name).first()
            existing_by_hn[hn] = existing

    grouped_units = group_units_by_house_number(cuzk_units, house_numbers)

    building_diffs: list[BuildingDiff] = []
    unit_diffs: list[UnitDiff] = []

    for hn in house_numbers:
        bdiff = compute_building_diff(cuzk_building, hn, existing_by_hn.get(hn))
        building_diffs.append(bdiff)
        for cu in grouped_units.get(hn, []):
            existing_flat = None
            if existing_by_hn.get(hn):
                bld = existing_by_hn[hn]
                existing_flat = Flat.objects.filter(building=bld, cuzk_unit_id=cu.id).first()
                if not existing_flat:
                    existing_flat = Flat.objects.filter(building=bld, flat_number=cu.flat_number_in_building).first()
            unit_diffs.append(compute_unit_diff(cu, existing_flat))

    return building_diffs, unit_diffs


# ---------------------------------------------------------------------------
#  Import execution
# ---------------------------------------------------------------------------
@transaction.atomic
def execute_import(
    building_diffs: list[BuildingDiff],
    building_actions: dict[int, str],
    unit_diffs: list[UnitDiff],
    unit_actions: dict[int, str],
) -> dict[str, int]:
    stats = {"buildings_created": 0, "buildings_updated": 0, "flats_created": 0, "flats_updated": 0, "skipped": 0}
    resolved_buildings: dict[int, Building | None] = {}

    for bdiff in building_diffs:
        hn = bdiff.house_number
        action = building_actions.get(hn, ACTION_SKIP)
        cb = bdiff.cuzk_building
        building = bdiff.existing_building
        lv_number = cb.lv.number if cb.lv else None

        if action == ACTION_CREATE:
            building = Building.objects.create(
                name=f"{cb.city_part_name} {hn}".strip() or str(hn),
                street=cb.city_part_name,
                house_number=str(hn),
                city=cb.municipality_name,
                postal_code="",
                cuzk_building_id=cb.id,
                cuzk_lv_number=lv_number,
            )
            stats["buildings_created"] += 1
        elif action == ACTION_UPDATE and building:
            building.house_number = str(hn)
            building.city = cb.municipality_name
            building.cuzk_building_id = cb.id
            building.cuzk_lv_number = lv_number
            building.save()
            stats["buildings_updated"] += 1
        else:
            stats["skipped"] += 1
        resolved_buildings[hn] = building

    for udiff in unit_diffs:
        action = unit_actions.get(udiff.cuzk_unit.id, ACTION_SKIP)
        cu = udiff.cuzk_unit
        building = resolved_buildings.get(cu.house_number)
        if not building:
            stats["skipped"] += 1
            continue

        share_num = cu.share.numerator if cu.share else None
        share_den = cu.share.denominator if cu.share else None

        if action == ACTION_CREATE:
            Flat.objects.create(
                building=building,
                flat_number=cu.flat_number_in_building,
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
#  Session serialization helpers
# ---------------------------------------------------------------------------
def serialize_building(b: CUZKBuilding) -> dict:
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
        "lv": {"id": b.lv.id, "number": b.lv.number,
               "cadastral_territory_code": b.lv.cadastral_territory_code,
               "cadastral_territory_name": b.lv.cadastral_territory_name} if b.lv else None,
        "unit_refs": [{"id": u.id, "unit_number": u.unit_number} for u in b.unit_refs],
    }


def deserialize_building(data: dict) -> CUZKBuilding:
    from .service import CUZKBuilding as B, CUZKTitleDeed, CUZKUnitRef
    lv = CUZKTitleDeed(**data["lv"]) if data.get("lv") else None
    return B(
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


def serialize_unit(u: CUZKUnit) -> dict:
    return {
        "id": u.id,
        "unit_number": u.unit_number,
        "unit_type_code": u.unit_type_code,
        "unit_type_name": u.unit_type_name,
        "usage_code": u.usage_code,
        "usage_name": u.usage_name,
        "share": {"numerator": u.share.numerator, "denominator": u.share.denominator} if u.share else None,
        "lv": {"id": u.lv.id, "number": u.lv.number,
               "cadastral_territory_code": u.lv.cadastral_territory_code,
               "cadastral_territory_name": u.lv.cadastral_territory_name} if u.lv else None,
        "building_id": u.building_id,
    }


def deserialize_unit(data: dict) -> CUZKUnit:
    from .service import CUZKShare, CUZKTitleDeed, CUZKUnit as U
    share = CUZKShare(**data["share"]) if data.get("share") else None
    lv = CUZKTitleDeed(**data["lv"]) if data.get("lv") else None
    return U(
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
