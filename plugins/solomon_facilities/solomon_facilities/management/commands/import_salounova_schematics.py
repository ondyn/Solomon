"""Import verified facility data from the Salounova floor plans and declaration."""

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ElementTree

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from solomon_property.models import BuildingObject

from solomon_facilities import models


SOURCE_FILES = (
    (-1, "1PP", "Basement", "Šalounova_1PP_4.pdf"),
    (0, "1NP", "Ground floor", "Šalounova_1NP_přeměření.pdf"),
    (1, "2NP", "Second floor", "Šalounova_2NP.pdf"),
    (2, "3NP", "Third floor", "Šalounova_3NP.pdf"),
    (3, "4NP", "Fourth floor", "Šalounova_4NP.pdf"),
    (4, "5NP", "Fifth floor", "Šalounova_5NP.pdf"),
    (5, "6NP", "Sixth floor", "Šalounova_6NP.pdf"),
)
HOUSE_NUMBERS = ("1937", "1938", "1939", "1940", "1941")
LEGAL_DOCUMENT = "Šalounova 1937-41_PV_verze_110423_POSLEDNÍ_poslané 130423.pdf"

CELLAR_PAGES = {
    "1937": dict(
        zip(
            (2, 3, 4, 7, 8, 11, 12, 15, 16, 19, 20, 23),
            (5, 6, 8, 12, 14, 18, 19, 23, 25, 29, 31, 35),
        )
    ),
    "1938": dict(
        zip(
            (2, 3, 4, 7, 8, 11, 12, 15, 16, 19, 20, 23),
            (38, 39, 41, 45, 47, 51, 52, 57, 58, 62, 64, 68),
        )
    ),
    "1939": dict(
        zip(
            (2, 3, 4, 7, 8, 11, 12, 15, 16, 19, 20, 23),
            (71, 72, 74, 78, 80, 84, 85, 89, 91, 95, 97, 101),
        )
    ),
    "1940": dict(zip(range(1, 9), (102, 104, 105, 107, 108, 110, 111, 113))),
    "1941": dict(zip(range(1, 9), (114, 116, 117, 119, 120, 122, 123, 125))),
}

COMMON_SPACE_INVENTORY = (
    ("LAUNDRY", "Laundry", 4),
    ("DRYING", "Drying room", 8),
    ("MANGLING", "Mangle room", 2),
    ("IRONING", "Ironing room", 2),
    ("PRAM", "Pram room", 2),
    ("BICYCLE", "Bicycle room", 2),
    ("MOPED", "Moped room", 2),
    ("BICYCLE-MOPED", "Bicycle and moped room", 2),
    ("CLEANING", "Cleaning room", 4),
    ("WC", "Common WC", 5),
    ("WASHROOM", "Washroom", 1),
    ("WORKSHOP-HUV", "Workshop and main water valve", 1),
    ("MAINTENANCE", "Maintenance room", 2),
    ("STORAGE", "Storage room", 9),
    ("CLUBROOM", "Club room", 1),
)


def build_flat_inventory():
    inventory = {}
    for house in ("1937", "1938", "1939"):
        inventory[(house, 1)] = {
            "floor": 0,
            "area_m2": "46.7" if house == "1939" else "33.0",
            "disposition": "1+kk",
            "radiator_count": 2 if house == "1939" else 1,
        }
        for suffix in (2, 3):
            inventory[(house, suffix)] = {
                "floor": 0,
                "area_m2": "77.6",
                "disposition": "3+1",
                "radiator_count": 4,
                "balcony_area": "5.0",
                "cellar": f"S{suffix}",
            }
        for floor, start in enumerate((4, 8, 12, 16, 20), start=1):
            for offset, (area, disposition, radiators) in enumerate(
                (
                    ("77.9", "3+1", 4),
                    ("30.9", "1+kk", 1),
                    ("43.8", "1+1", 2),
                    ("77.9", "3+1", 4),
                )
            ):
                suffix = start + offset
                if house == "1939" and suffix == 23:
                    disposition = "4+kk"
                data = {
                    "floor": floor,
                    "area_m2": area,
                    "disposition": disposition,
                    "radiator_count": radiators,
                }
                if offset in (0, 3):
                    data.update({"balcony_area": "4.8", "cellar": f"S{suffix}"})
                inventory[(house, suffix)] = data

    for house in ("1940", "1941"):
        inventory[(house, 1)] = {
            "floor": 0,
            "area_m2": "79.3",
            "disposition": "3+1",
            "radiator_count": 4,
            "balcony_area": "2.6",
            "cellar": "S1",
        }
        inventory[(house, 2)] = {
            "floor": 0,
            "area_m2": "82.0",
            "disposition": "3+1",
            "radiator_count": 4,
            "balcony_area": "3.8",
            "cellar": "S2",
        }
        for floor, start in enumerate((3, 5, 7), start=1):
            inventory[(house, start)] = {
                "floor": floor,
                "area_m2": "88.0",
                "disposition": "4+1",
                "radiator_count": 5,
                "balcony_area": "2.6",
                "cellar": f"S{start}",
            }
            inventory[(house, start + 1)] = {
                "floor": floor,
                "area_m2": "94.5",
                "disposition": "4+1",
                "radiator_count": 5,
                "balcony_area": "3.8",
                "cellar": f"S{start + 1}",
            }
    return inventory


FLAT_INVENTORY = build_flat_inventory()


class Command(BaseCommand):
    help = "Import Salounova levels, floor plans, spaces, and verified technical assets"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-dir",
            type=Path,
            default=Path("/opt/netbox/support/floor-schematics"),
            help="Directory containing floor PDFs and generated SVG/bbox files",
        )
        parser.add_argument("--building-object-id", type=int)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--skip-files", action="store_true")

    def handle(self, *args, **options):
        source_dir = options["source_dir"]
        generated_dir = source_dir / "generated"
        if not source_dir.is_dir():
            raise CommandError(f"Source directory does not exist: {source_dir}")
        building_object = self._find_building_object(options.get("building_object_id"))
        buildings = {
            str(building.house_number): building
            for building in building_object.buildings.filter(
                house_number__in=HOUSE_NUMBERS
            )
        }
        missing_buildings = set(HOUSE_NUMBERS) - set(buildings)
        if missing_buildings:
            raise CommandError(
                f"Building object {building_object.pk} is missing entrances: {', '.join(sorted(missing_buildings))}"
            )

        self.counts = Counter()
        self.warnings = []
        with transaction.atomic():
            levels, plans, revisions = self._import_plans(
                building_object,
                source_dir,
                generated_dir,
                skip_files=options["skip_files"],
                dry_run=options["dry_run"],
            )
            flats = self._match_and_enrich_flats(buildings)
            spaces = self._import_flat_spaces(levels, buildings, flats)
            self._import_plan_hotspots(revisions, spaces, generated_dir)
            common_spaces = self._import_common_spaces(levels[-1])
            self._import_entry_doors(levels[0], buildings)
            self._import_technical_assets(
                building_object, levels, buildings, common_spaces
            )
            if options["dry_run"]:
                transaction.set_rollback(True)

        qualifier = "Would import" if options["dry_run"] else "Imported"
        summary = (
            ", ".join(f"{value} {key}" for key, value in sorted(self.counts.items()))
            or "no changes"
        )
        self.stdout.write(self.style.SUCCESS(f"{qualifier}: {summary}"))
        for warning in self.warnings:
            self.stdout.write(self.style.WARNING(warning))
        self.stdout.write(
            f"Legal source used for assignments and system descriptions: {source_dir.parent / LEGAL_DOCUMENT}"
        )

    def _find_building_object(self, object_id):
        if object_id:
            try:
                return BuildingObject.objects.get(pk=object_id)
            except BuildingObject.DoesNotExist as error:
                raise CommandError(
                    f"Building object {object_id} does not exist"
                ) from error
        candidates = []
        for building_object in BuildingObject.objects.prefetch_related("buildings"):
            house_numbers = {
                str(building.house_number)
                for building in building_object.buildings.all()
            }
            if set(HOUSE_NUMBERS).issubset(house_numbers):
                candidates.append(building_object)
        if len(candidates) != 1:
            raise CommandError(
                "Could not uniquely identify the building object containing entrances 1937-1941; "
                "pass --building-object-id."
            )
        return candidates[0]

    def _import_plans(
        self, building_object, source_dir, generated_dir, skip_files, dry_run
    ):
        levels = {}
        plans = {}
        revisions = {}
        for number, reference, name, filename in SOURCE_FILES:
            level, created = models.BuildingLevel.objects.get_or_create(
                building_object=building_object,
                number=number,
                defaults={"reference": reference, "name": name},
            )
            if created:
                self.counts["levels"] += 1
            plan, created = models.FloorPlan.objects.get_or_create(
                level=level,
                defaults={
                    "name": f"{building_object.name} - {reference}",
                    "width": Decimal("1190.52"),
                    "height": Decimal("841.92"),
                    "measurement_unit": "cm",
                },
            )
            if created:
                self.counts["plans"] += 1
            revision = (
                plan.active_revision or plan.revisions.order_by("revision").first()
            )
            if revision is None:
                revision = models.PlanRevision.objects.create(
                    plan=plan,
                    revision=1,
                    status="published",
                    background_rotation=-90,
                    source_page=1,
                    scale_denominator=75,
                    source_note=(
                        f"Vector source {filename}, page 1. Imported without semantic polygon reconstruction; "
                        "apartment click targets are derived from verified area-label coordinates."
                    ),
                )
                self.counts["plan revisions"] += 1
            if not skip_files and not dry_run:
                pdf_path = source_dir / filename
                svg_path = generated_dir / f"{Path(filename).stem}.svg"
                if not pdf_path.is_file() or not svg_path.is_file():
                    raise CommandError(f"Missing PDF or generated SVG for {filename}")
                if not revision.source_file:
                    with pdf_path.open("rb") as source_handle:
                        revision.source_file.save(
                            filename, File(source_handle), save=False
                        )
                if not revision.background_file:
                    with svg_path.open("rb") as background_handle:
                        revision.background_file.save(
                            svg_path.name, File(background_handle), save=False
                        )
                revision.save()
            if plan.active_revision_id != revision.pk:
                plan.active_revision = revision
                plan.save()
            levels[number] = level
            plans[number] = plan
            revisions[number] = revision
        return levels, plans, revisions

    def _match_and_enrich_flats(self, buildings):
        matched = {}
        for house, building in buildings.items():
            by_suffix = {}
            for flat in building.flats.all():
                suffix_text = str(flat.flat_number).split("/")[-1].lstrip("0") or "0"
                if suffix_text.isdigit():
                    by_suffix[int(suffix_text)] = flat
            for (inventory_house, suffix), data in FLAT_INVENTORY.items():
                if inventory_house != house:
                    continue
                flat = by_suffix.get(suffix)
                if flat is None:
                    self.warnings.append(
                        f"No existing flat matched {house}/{suffix}; skipped"
                    )
                    continue
                updates = {
                    "floor": data["floor"],
                    "area_m2": Decimal(data["area_m2"]),
                    "disposition": data["disposition"],
                    "radiator_count": data["radiator_count"],
                }
                if data.get("cellar"):
                    updates["cellar_unit"] = data["cellar"]
                if data.get("balcony_area"):
                    updates["has_balcony"] = True
                changed = False
                for field, expected in updates.items():
                    current = getattr(flat, field)
                    is_missing = current is None or current == ""
                    if (
                        isinstance(current, bool)
                        and current is False
                        and expected is True
                    ):
                        is_missing = True
                    if is_missing:
                        setattr(flat, field, expected)
                        changed = True
                    elif current != expected:
                        self.warnings.append(
                            f"Kept existing {house}/{suffix} {field}={current!s}; source says {expected!s}"
                        )
                if changed:
                    flat.full_clean()
                    flat.save()
                    self.counts["enriched flats"] += 1
                matched[(house, suffix)] = flat
        return matched

    def _import_flat_spaces(self, levels, buildings, flats):
        spaces = {}
        basement = levels[-1]
        for key, flat in flats.items():
            house, suffix = key
            data = FLAT_INVENTORY[key]
            space, created = models.Space.objects.get_or_create(
                level=levels[data["floor"]],
                reference=f"{house}-{suffix}",
                defaults={
                    "building": buildings[house],
                    "name": f"Flat {house}/{suffix}",
                    "kind": "flat",
                    "area_m2": Decimal(data["area_m2"]),
                    "notes": "Area and disposition verified from the declaration and floor drawing.",
                },
            )
            if created:
                self.counts["flat spaces"] += 1
            models.SpaceFlatAssignment.objects.get_or_create(
                space=space,
                flat=flat,
                role="primary",
            )
            spaces[key] = space

            if data.get("cellar"):
                page = CELLAR_PAGES[house][suffix]
                cellar, created = models.Space.objects.get_or_create(
                    level=basement,
                    reference=f"{house}-{data['cellar']}",
                    defaults={
                        "building": buildings[house],
                        "name": f"Cellar {data['cellar']}",
                        "kind": "cellar",
                        "notes": (
                            f"Common part under exclusive use by flat {house}/{suffix}; declaration page {page}."
                        ),
                    },
                )
                if created:
                    self.counts["cellar spaces"] += 1
                models.SpaceFlatAssignment.objects.get_or_create(
                    space=cellar,
                    flat=flat,
                    role="cellar",
                    defaults={"notes": f"Declaration page {page}."},
                )

            if data.get("balcony_area"):
                balcony, created = models.Space.objects.get_or_create(
                    level=levels[data["floor"]],
                    reference=f"{house}-{suffix}-L",
                    defaults={
                        "building": buildings[house],
                        "name": f"Loggia {house}/{suffix}",
                        "kind": "balcony",
                        "area_m2": Decimal(data["balcony_area"]),
                        "notes": "Common part under exclusive use; declaration pages 125-128.",
                    },
                )
                if created:
                    self.counts["loggia spaces"] += 1
                models.SpaceFlatAssignment.objects.get_or_create(
                    space=balcony,
                    flat=flat,
                    role="balcony",
                    defaults={
                        "notes": "Common part under exclusive use; declaration pages 125-128."
                    },
                )
        return spaces

    def _import_plan_hotspots(self, revisions, spaces, generated_dir):
        for number, reference, name, filename in SOURCE_FILES:
            if number < 0:
                continue
            ground_order = {
                (house, suffix): index
                for house in ("1937", "1938", "1939")
                for index, suffix in enumerate((2, 1, 3))
            }
            ground_order.update(
                {
                    (house, suffix): index
                    for house in ("1940", "1941")
                    for index, suffix in enumerate((1, 2))
                }
            )
            expected = sorted(
                (
                    (key, data)
                    for key, data in FLAT_INVENTORY.items()
                    if data["floor"] == number and key in spaces
                ),
                key=lambda item: (
                    int(item[0][0]),
                    ground_order[item[0]] if number == 0 else item[0][1],
                ),
            )
            bbox_path = generated_dir / f"{Path(filename).stem}.bbox.html"
            if not bbox_path.is_file():
                self.warnings.append(
                    f"Missing positioned text file {bbox_path.name}; skipped hotspots"
                )
                continue
            page_width, words = self._read_bbox(bbox_path)
            expected_values = [Decimal(data["area_m2"]) for key, data in expected]
            candidates = sorted(
                (
                    word
                    for word in words
                    if self._decimal_or_none(word["text"]) in expected_values
                ),
                key=lambda word: word["y_min"],
            )
            actual_values = [self._decimal_or_none(word["text"]) for word in candidates]
            if actual_values != expected_values:
                self.warnings.append(
                    f"Area-label order mismatch for {reference}; expected {expected_values}, got {actual_values}. Skipped hotspots."
                )
                continue
            for (key, data), word in zip(expected, candidates):
                space = spaces[key]
                if revisions[number].elements.filter(space=space).exists():
                    continue
                center_x = (word["y_min"] + word["y_max"]) / 2
                center_y = page_width - (word["x_min"] + word["x_max"]) / 2
                models.PlanElement.objects.create(
                    revision=revisions[number],
                    element_type="space",
                    label=f"{key[0]}/{key[1]}",
                    geometry={
                        "type": "rect",
                        "x": center_x - 24,
                        "y": center_y - 18,
                        "width": 48,
                        "height": 36,
                    },
                    style={
                        "fill": "#dce9e4",
                        "stroke": "#39806a",
                        "stroke_width": 1.5,
                        "opacity": 0.28,
                    },
                    space=space,
                )
                self.counts["flat hotspots"] += 1

    def _read_bbox(self, path):
        root = ElementTree.parse(path).getroot()
        page = next(element for element in root.iter() if element.tag.endswith("page"))
        page_width = float(page.attrib["width"])
        words = []
        for element in root.iter():
            if not element.tag.endswith("word"):
                continue
            words.append(
                {
                    "text": "".join(element.itertext()).strip(),
                    "x_min": float(element.attrib["xMin"]),
                    "x_max": float(element.attrib["xMax"]),
                    "y_min": float(element.attrib["yMin"]),
                    "y_max": float(element.attrib["yMax"]),
                }
            )
        return page_width, words

    def _decimal_or_none(self, value):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _import_common_spaces(self, basement):
        spaces = {}
        for code, name, count in COMMON_SPACE_INVENTORY:
            for index in range(1, count + 1):
                reference = f"{code}-{index}"
                space, created = models.Space.objects.get_or_create(
                    level=basement,
                    reference=reference,
                    defaults={
                        "name": f"{name} {index}" if count > 1 else name,
                        "kind": "technical_room"
                        if code == "WORKSHOP-HUV"
                        else "common_room",
                        "notes": "Common-space inventory from declaration pages 125-126; exact outline awaits tracing.",
                    },
                )
                if created:
                    self.counts["common spaces"] += 1
                spaces[reference] = space
        return spaces

    def _import_entry_doors(self, ground_floor, buildings):
        for house, building in buildings.items():
            entrance, created = models.Space.objects.get_or_create(
                level=ground_floor,
                reference=f"ENTRY-{house}",
                defaults={
                    "building": building,
                    "name": f"Entrance {house}",
                    "kind": "corridor",
                    "notes": "Entrance and corridor shown on the 1NP plan.",
                },
            )
            if created:
                self.counts["entrance spaces"] += 1
            door, created = models.Door.objects.get_or_create(
                level=ground_floor,
                reference=f"ENTRANCE-{house}",
                defaults={
                    "name": f"Main entrance door {house}",
                    "door_type": "entrance",
                    "from_space": entrance,
                    "notes": "Seeded from the 1NP drawing; lock and key profile require physical survey.",
                },
            )
            if created:
                self.counts["doors"] += 1

    def _import_technical_assets(
        self, building_object, levels, buildings, common_spaces
    ):
        systems = {}
        descriptions = {
            "gas": "Two HUP groups and low-pressure basement distribution; declaration page 4.",
            "cold_water": "PPR water distribution with HUV access kept unobstructed; declaration pages 4 and 126.",
            "electrical": "RIS and 230/400 V meter/riser distribution; declaration pages 5, 102, 114 and 125.",
            "low_current": "Common TV/data, telephone and doorbell distribution; declaration pages 126-127.",
            "heating": "District heating, vertical risers and thermostatic radiator valves; declaration pages 4-5 and 126.",
        }
        names = {
            "gas": "Gas distribution",
            "cold_water": "Cold water distribution",
            "electrical": "Electrical distribution",
            "low_current": "Low-current and data distribution",
            "heating": "Heating distribution",
        }
        for kind, name in names.items():
            system, created = models.TechnicalSystem.objects.get_or_create(
                building_object=building_object,
                name=name,
                defaults={"kind": kind, "description": descriptions[kind]},
            )
            systems[kind] = system
            if created:
                self.counts["technical systems"] += 1

        hup_groups = (
            (
                "HUP-1937-1939",
                "Main gas shutoff for entrances 1937-1939",
                ("1937", "1938", "1939"),
            ),
            (
                "HUP-1940-1941",
                "Main gas shutoff for entrances 1940-1941",
                ("1940", "1941"),
            ),
        )
        for code, name, houses in hup_groups:
            hup, created = models.TechnicalAsset.objects.get_or_create(
                system=systems["gas"],
                code=code,
                defaults={
                    "name": name,
                    "asset_type": "main gas shutoff",
                    "emergency_instructions": "Located in front of the building; exact plan point requires survey.",
                    "notes": "Declaration page 4.",
                },
            )
            if created:
                self.counts["technical assets"] += 1
            for house in houses:
                for branch in ("A", "B"):
                    riser, created = models.TechnicalAsset.objects.get_or_create(
                        system=systems["gas"],
                        code=f"GAS-RISER-{house}-{branch}",
                        defaults={
                            "name": f"Gas riser valve {house} {branch}",
                            "asset_type": "riser valve",
                            "level": levels[-1],
                            "notes": "Two riser branches per entrance; exact room and served flats require survey. Declaration page 4.",
                        },
                    )
                    models.TechnicalConnection.objects.get_or_create(
                        from_asset=hup,
                        to_asset=riser,
                        kind="feeds",
                    )
                    if created:
                        self.counts["technical assets"] += 1

        water_asset, created = models.TechnicalAsset.objects.get_or_create(
            system=systems["cold_water"],
            code="HUV",
            defaults={
                "name": "Main water valve",
                "asset_type": "main water valve",
                "level": levels[-1],
                "space": common_spaces["WORKSHOP-HUV-1"],
                "emergency_instructions": "Keep access unobstructed.",
                "notes": "Workshop and HUV room listed in declaration pages 125-126.",
            },
        )
        if created:
            self.counts["technical assets"] += 1

        for house in HOUSE_NUMBERS:
            meter_level = levels[-1] if house in ("1937", "1938", "1939") else levels[0]
            for system_kind, code_prefix, asset_type, notes in (
                (
                    "electrical",
                    "EL-METER",
                    "meter switchboard",
                    "1937-1939: 1PP; 1940-1941: 1NP. Declaration pages 5, 102, 114 and 125.",
                ),
                (
                    "low_current",
                    "DATA-MAIN",
                    "low-current distribution board",
                    "Exact room and provider ownership require survey. Declaration pages 126-127.",
                ),
            ):
                asset, created = models.TechnicalAsset.objects.get_or_create(
                    system=systems[system_kind],
                    code=f"{code_prefix}-{house}",
                    defaults={
                        "name": f"{asset_type.title()} {house}",
                        "asset_type": asset_type,
                        "level": meter_level if system_kind == "electrical" else None,
                        "notes": notes,
                    },
                )
                if created:
                    self.counts["technical assets"] += 1
