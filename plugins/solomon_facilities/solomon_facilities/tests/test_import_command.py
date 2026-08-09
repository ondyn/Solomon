from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from solomon_property.models import Building, BuildingObject, Flat

from solomon_facilities.management.commands.import_salounova_schematics import (
    FLAT_INVENTORY,
    SOURCE_FILES,
)
from solomon_facilities.models import (
    BuildingLevel,
    FloorPlan,
    PlanElement,
    Space,
    SpaceFlatAssignment,
    TechnicalAsset,
    TechnicalConnection,
    TechnicalSystem,
)


class SalounovaImportCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.building_object = BuildingObject.objects.create(name="Salounova 1937-1941")
        cls.buildings = {}
        for house in ("1937", "1938", "1939", "1940", "1941"):
            building = Building.objects.create(
                building_object=cls.building_object,
                name=f"Salounova {house}",
                street="Salounova",
                house_number=house,
            )
            cls.buildings[house] = building
        for house, suffix in FLAT_INVENTORY:
            Flat.objects.create(
                building=cls.buildings[house],
                flat_number=f"{house}/{suffix}",
            )

    def test_imports_all_verified_records_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            source_dir = Path(directory)
            generated_dir = source_dir / "generated"
            generated_dir.mkdir()
            self._write_bbox_fixtures(generated_dir)

            call_command(
                "import_salounova_schematics",
                source_dir=source_dir,
                skip_files=True,
                stdout=StringIO(),
            )

            self.assertEqual(BuildingLevel.objects.count(), 7)
            self.assertEqual(FloorPlan.objects.count(), 7)
            self.assertEqual(Space.objects.filter(kind="flat").count(), 85)
            self.assertEqual(Space.objects.filter(kind="cellar").count(), 52)
            self.assertEqual(Space.objects.filter(kind="balcony").count(), 52)
            self.assertEqual(
                PlanElement.objects.filter(element_type="space").count(), 85
            )
            self.assertEqual(SpaceFlatAssignment.objects.count(), 189)
            self.assertEqual(TechnicalSystem.objects.count(), 5)
            self.assertEqual(TechnicalAsset.objects.count(), 23)
            self.assertEqual(TechnicalConnection.objects.count(), 10)

            flat = Flat.objects.get(
                building=self.buildings["1937"], flat_number="1937/4"
            )
            self.assertEqual(str(flat.area_m2), "77.90")
            self.assertEqual(flat.floor, 1)
            self.assertEqual(flat.cellar_unit, "S4")
            self.assertTrue(flat.has_balcony)
            self.assertFalse(flat.gas_installed)

            counts_before = {
                "levels": BuildingLevel.objects.count(),
                "plans": FloorPlan.objects.count(),
                "spaces": Space.objects.count(),
                "elements": PlanElement.objects.count(),
                "assets": TechnicalAsset.objects.count(),
            }
            second_output = StringIO()
            call_command(
                "import_salounova_schematics",
                source_dir=source_dir,
                skip_files=True,
                stdout=second_output,
            )
            counts_after = {
                "levels": BuildingLevel.objects.count(),
                "plans": FloorPlan.objects.count(),
                "spaces": Space.objects.count(),
                "elements": PlanElement.objects.count(),
                "assets": TechnicalAsset.objects.count(),
            }
            self.assertEqual(counts_after, counts_before)
            self.assertIn("Imported: no changes", second_output.getvalue())

    def _write_bbox_fixtures(self, generated_dir):
        for floor, reference, name, filename in SOURCE_FILES:
            if floor < 0:
                continue
            keys = [
                key for key, data in FLAT_INVENTORY.items() if data["floor"] == floor
            ]
            if floor == 0:
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
                keys.sort(key=lambda key: (int(key[0]), ground_order[key]))
            else:
                keys.sort(key=lambda key: (int(key[0]), key[1]))

            words = []
            for index, key in enumerate(keys):
                y_min = 10 + index * 20
                y_max = y_min + 8
                words.append(
                    f'<word xMin="400" yMin="{y_min}" xMax="410" yMax="{y_max}">'
                    f"{FLAT_INVENTORY[key]['area_m2']}</word>"
                )
            document = (
                '<html xmlns="http://www.w3.org/1999/xhtml"><body><doc>'
                '<page width="841.92" height="1190.52">'
                + "".join(words)
                + "</page></doc></body></html>"
            )
            path = generated_dir / f"{Path(filename).stem}.bbox.html"
            path.write_text(document, encoding="utf-8")
