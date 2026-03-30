"""
Solomon — Tests for CUZK import functionality.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from buildings.models import Building
from core.cuzk_import import (
    ACTION_CREATE,
    ACTION_SKIP,
    ACTION_UPDATE,
    build_import_preview,
    compute_building_diff,
    compute_unit_diff,
    execute_import,
)
from core.cuzk_service import (
    CUZKBuilding,
    CUZKShare,
    CUZKTitleDeed,
    CUZKUnit,
    CUZKUnitRef,
    group_units_by_house_number,
)
from flats.models import Flat


# ---------------------------------------------------------------------------
#  Test helpers / fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_cuzk_building():
    """A sample CUZK building response with a single house number."""
    return CUZKBuilding(
        id=951290101,
        building_type_code=1,
        building_type_name="budova s cislem popisnym",
        house_numbers=[1800],
        municipality_code=554782,
        municipality_name="Praha",
        city_part_code=400611,
        city_part_name="Chodov",
        usage_code=6,
        usage_name="bytovy dum",
        lv=CUZKTitleDeed(id=123, number=10136, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
        unit_refs=[
            CUZKUnitRef(id=145572601, unit_number=18000001),
            CUZKUnitRef(id=145572602, unit_number=18000002),
            CUZKUnitRef(id=145572603, unit_number=18000003),
        ],
    )


@pytest.fixture
def sample_cuzk_units():
    """Sample CUZK units with compound unit numbers (house_number * 10000 + flat_number)."""
    return [
        CUZKUnit(
            id=145572601,
            unit_number=18000001,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=650, denominator=10000),
            lv=CUZKTitleDeed(id=200, number=10137, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
            building_id=951290101,
        ),
        CUZKUnit(
            id=145572602,
            unit_number=18000002,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=480, denominator=10000),
            lv=CUZKTitleDeed(id=201, number=10138, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
            building_id=951290101,
        ),
        CUZKUnit(
            id=145572603,
            unit_number=18000003,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=520, denominator=10000),
            lv=CUZKTitleDeed(id=202, number=10139, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
            building_id=951290101,
        ),
    ]


@pytest.fixture
def multi_building_cuzk():
    """A CUZK building with multiple house numbers (like Salounova 1937-1941)."""
    building = CUZKBuilding(
        id=940255101,
        building_type_code=1,
        building_type_name="budova s cislem popisnym",
        house_numbers=[1937, 1938, 1939],
        municipality_code=554782,
        municipality_name="Praha",
        city_part_code=400211,
        city_part_name="Chodov",
        usage_code=6,
        usage_name="bytovy dum",
        lv=CUZKTitleDeed(id=100, number=10136, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
        unit_refs=[
            CUZKUnitRef(id=1001, unit_number=19370001),
            CUZKUnitRef(id=1002, unit_number=19370002),
            CUZKUnitRef(id=1003, unit_number=19380001),
            CUZKUnitRef(id=1004, unit_number=19380002),
            CUZKUnitRef(id=1005, unit_number=19390001),
        ],
    )
    units = [
        CUZKUnit(
            id=1001,
            unit_number=19370001,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=100, denominator=10000),
            building_id=940255101,
        ),
        CUZKUnit(
            id=1002,
            unit_number=19370002,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=100, denominator=10000),
            building_id=940255101,
        ),
        CUZKUnit(
            id=1003,
            unit_number=19380001,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=200, denominator=10000),
            building_id=940255101,
        ),
        CUZKUnit(
            id=1004,
            unit_number=19380002,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=200, denominator=10000),
            building_id=940255101,
        ),
        CUZKUnit(
            id=1005,
            unit_number=19390001,
            unit_type_code=3,
            unit_type_name="byt",
            share=CUZKShare(numerator=300, denominator=10000),
            building_id=940255101,
        ),
    ]
    return building, units


# ---------------------------------------------------------------------------
#  CUZK Service (data classes) tests
# ---------------------------------------------------------------------------
class TestCUZKDataClasses:
    def test_share_from_api(self):
        share = CUZKShare.from_api({"citatel": 650, "jmenovatel": 10000})
        assert share is not None
        assert share.numerator == 650
        assert share.denominator == 10000
        assert str(share) == "650/10000"

    def test_share_from_api_none(self):
        assert CUZKShare.from_api(None) is None

    def test_title_deed_from_api(self):
        lv = CUZKTitleDeed.from_api(
            {
                "id": 123,
                "cislo": 10136,
                "katastralniUzemi": {"kod": 728225, "nazev": "Chodov"},
            }
        )
        assert lv is not None
        assert lv.number == 10136
        assert lv.cadastral_territory_name == "Chodov"

    def test_building_from_api(self):
        data = {
            "id": 940255101,
            "typStavby": {"kod": 1, "nazev": "budova s cislem popisnym"},
            "cislaDomovni": [1937, 1938, 1939, 1940, 1941],
            "obec": {"kod": 554782, "nazev": "Praha"},
            "castObce": {"kod": 400211, "nazev": "Chodov"},
            "zpusobVyuziti": {"kod": 6, "nazev": "bytovy dum"},
            "lv": {"id": 123, "cislo": 10136, "katastralniUzemi": {"kod": 728225, "nazev": "Chodov"}},
            "jednotky": [
                {"id": 145572601, "cisloJednotky": 19370001},
                {"id": 145572602, "cisloJednotky": 19380002},
            ],
        }
        building = CUZKBuilding.from_api(data)
        assert building.id == 940255101
        assert building.house_numbers == [1937, 1938, 1939, 1940, 1941]
        assert building.municipality_name == "Praha"
        assert len(building.unit_refs) == 2
        assert building.lv.number == 10136

    def test_unit_from_api(self):
        data = {
            "id": 145572601,
            "cisloJednotky": 19370002,
            "typJednotky": {"kod": 3, "nazev": "byt"},
            "zpusobVyuziti": {"kod": 2, "nazev": "byt"},
            "podilNaSpolecnychCastechDomu": {"citatel": 650, "jmenovatel": 10000},
            "lv": {"id": 200, "cislo": 10137, "katastralniUzemi": {"kod": 728225, "nazev": "Chodov"}},
            "vymezenaVeStavbe": {"id": 940255101},
        }
        unit = CUZKUnit.from_api(data)
        assert unit.id == 145572601
        assert unit.unit_number == 19370002
        assert unit.house_number == 1937
        assert unit.flat_number_in_building == "2"
        assert unit.share.numerator == 650
        assert unit.share.denominator == 10000
        assert unit.building_id == 940255101

    def test_unit_house_number_extraction(self):
        """Test house_number and flat_number_in_building properties."""
        # Compound number: 19370002 → building 1937, flat 2
        unit = CUZKUnit(id=1, unit_number=19370002)
        assert unit.house_number == 1937
        assert unit.flat_number_in_building == "2"

        # Compound number: 19410008 → building 1941, flat 8
        unit2 = CUZKUnit(id=2, unit_number=19410008)
        assert unit2.house_number == 1941
        assert unit2.flat_number_in_building == "8"

        # Simple number (< 10000): house_number = 0, flat = number itself
        unit3 = CUZKUnit(id=3, unit_number=5)
        assert unit3.house_number == 0
        assert unit3.flat_number_in_building == "5"

    def test_group_units_by_house_number(self):
        """Test that units are correctly grouped by their house number."""
        units = [
            CUZKUnit(id=1, unit_number=19370001),
            CUZKUnit(id=2, unit_number=19370002),
            CUZKUnit(id=3, unit_number=19380001),
            CUZKUnit(id=4, unit_number=19390001),
            CUZKUnit(id=5, unit_number=19390002),
        ]
        grouped = group_units_by_house_number(units, [1937, 1938, 1939])
        assert len(grouped[1937]) == 2
        assert len(grouped[1938]) == 1
        assert len(grouped[1939]) == 2

    def test_group_units_simple_numbers_go_to_first(self):
        """Simple unit numbers (< 10000) are assigned to the first house number."""
        units = [
            CUZKUnit(id=1, unit_number=1),
            CUZKUnit(id=2, unit_number=2),
        ]
        grouped = group_units_by_house_number(units, [1800])
        assert len(grouped[1800]) == 2


# ---------------------------------------------------------------------------
#  Import diff computation tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestImportDiff:
    def test_building_diff_new(self, sample_cuzk_building):
        """Test diff when no existing building exists."""
        diff = compute_building_diff(sample_cuzk_building, 1800, None)
        assert diff.suggested_action == ACTION_CREATE
        assert diff.existing_building is None
        assert diff.house_number == 1800
        assert any(d.field_name == "house_number" and d.new_value == "1800" for d in diff.field_diffs)

    def test_building_diff_no_changes(self, sample_cuzk_building):
        """Test diff when building exists with same data."""
        building = Building.objects.create(
            name="Test",
            street="Chodov",
            house_number="1800",
            city="Praha",
            postal_code="14900",
            cuzk_building_id=951290101,
            cuzk_lv_number=10136,
        )
        diff = compute_building_diff(sample_cuzk_building, 1800, building)
        assert diff.suggested_action == ACTION_SKIP

    def test_building_diff_with_changes(self, sample_cuzk_building):
        """Test diff when building exists but data differs."""
        building = Building.objects.create(
            name="Test",
            street="Chodov",
            house_number="1799",
            city="Praha",
            postal_code="14900",
            cuzk_building_id=951290101,
        )
        diff = compute_building_diff(sample_cuzk_building, 1800, building)
        assert diff.suggested_action == ACTION_UPDATE
        house_diff = next(d for d in diff.field_diffs if d.field_name == "house_number")
        assert house_diff.is_changed

    def test_unit_diff_new(self, sample_cuzk_units):
        """Test diff when no existing flat exists."""
        diff = compute_unit_diff(sample_cuzk_units[0], None)
        assert diff.suggested_action == ACTION_CREATE
        assert diff.existing_flat is None
        # unit_number=18000001 → flat_number_in_building="1"
        assert any(d.field_name == "flat_number" and d.new_value == "1" for d in diff.field_diffs)

    def test_unit_diff_no_changes(self, sample_cuzk_units):
        """Test diff when flat exists with same CUZK data."""
        building = Building.objects.create(
            name="Test",
            street="Test",
            house_number="1800",
            city="Test",
            postal_code="00000",
        )
        flat = Flat.objects.create(
            building=building,
            flat_number="1",
            cuzk_unit_id=145572601,
            cuzk_share_numerator=650,
            cuzk_share_denominator=10000,
        )
        diff = compute_unit_diff(sample_cuzk_units[0], flat)
        assert diff.suggested_action == ACTION_SKIP

    def test_unit_diff_with_changes(self, sample_cuzk_units):
        """Test diff when flat exists but share differs."""
        building = Building.objects.create(
            name="Test",
            street="Test",
            house_number="1800",
            city="Test",
            postal_code="00000",
        )
        flat = Flat.objects.create(
            building=building,
            flat_number="1",
            cuzk_unit_id=145572601,
            cuzk_share_numerator=600,
            cuzk_share_denominator=10000,
        )
        diff = compute_unit_diff(sample_cuzk_units[0], flat)
        assert diff.suggested_action == ACTION_UPDATE


# ---------------------------------------------------------------------------
#  Multi-building import preview tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestMultiBuildingPreview:
    def test_preview_creates_multiple_building_diffs(self, multi_building_cuzk):
        """One CUZK stavba with 3 house numbers → 3 BuildingDiffs."""
        cuzk_building, cuzk_units = multi_building_cuzk
        building_diffs, unit_diffs = build_import_preview(cuzk_building, cuzk_units)

        assert len(building_diffs) == 3
        assert building_diffs[0].house_number == 1937
        assert building_diffs[1].house_number == 1938
        assert building_diffs[2].house_number == 1939
        assert all(bd.suggested_action == ACTION_CREATE for bd in building_diffs)

    def test_preview_groups_units_correctly(self, multi_building_cuzk):
        """Units are grouped by house number extracted from cisloJednotky."""
        cuzk_building, cuzk_units = multi_building_cuzk
        building_diffs, unit_diffs = build_import_preview(cuzk_building, cuzk_units)

        # 2 units for 1937, 2 for 1938, 1 for 1939
        assert len(unit_diffs) == 5
        hn_1937_units = [u for u in unit_diffs if u.house_number == 1937]
        hn_1938_units = [u for u in unit_diffs if u.house_number == 1938]
        hn_1939_units = [u for u in unit_diffs if u.house_number == 1939]
        assert len(hn_1937_units) == 2
        assert len(hn_1938_units) == 2
        assert len(hn_1939_units) == 1

    def test_no_duplicate_flat_numbers_across_buildings(self, multi_building_cuzk):
        """Flat number '1' can exist in multiple buildings without conflict."""
        cuzk_building, cuzk_units = multi_building_cuzk
        _, unit_diffs = build_import_preview(cuzk_building, cuzk_units)

        # Both 19370001 and 19380001 produce flat_number "1" but for different buildings
        flat_1_units = [u for u in unit_diffs if u.cuzk_unit.flat_number_in_building == "1"]
        assert len(flat_1_units) == 3  # One per building (1937, 1938, 1939)
        house_numbers = {u.house_number for u in flat_1_units}
        assert house_numbers == {1937, 1938, 1939}


# ---------------------------------------------------------------------------
#  Import execution tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestImportExecution:
    def test_create_building_and_flats(self, sample_cuzk_building, sample_cuzk_units):
        """Test full import creating a new building with flats."""
        building_diffs, unit_diffs = build_import_preview(
            sample_cuzk_building,
            sample_cuzk_units,
        )
        building_actions = {1800: ACTION_CREATE}
        unit_actions = {u.cuzk_unit.id: ACTION_CREATE for u in unit_diffs}

        stats = execute_import(building_diffs, building_actions, unit_diffs, unit_actions)

        assert stats["buildings_created"] == 1
        assert stats["flats_created"] == 3

        # Verify DB state
        building = Building.objects.get(cuzk_building_id=951290101)
        assert building.house_number == "1800"
        assert building.city == "Praha"
        assert building.cuzk_lv_number == 10136

        flats = Flat.objects.filter(building=building).order_by("flat_number")
        assert flats.count() == 3
        flat1 = flats.get(flat_number="1")
        assert flat1.cuzk_unit_id == 145572601
        assert flat1.cuzk_share_numerator == 650
        assert flat1.cuzk_share_denominator == 10000

    def test_create_multiple_buildings(self, multi_building_cuzk):
        """Test import creating multiple buildings from one CUZK stavba."""
        cuzk_building, cuzk_units = multi_building_cuzk
        building_diffs, unit_diffs = build_import_preview(cuzk_building, cuzk_units)

        building_actions = {hn: ACTION_CREATE for hn in [1937, 1938, 1939]}
        unit_actions = {u.cuzk_unit.id: ACTION_CREATE for u in unit_diffs}

        stats = execute_import(building_diffs, building_actions, unit_diffs, unit_actions)

        assert stats["buildings_created"] == 3
        assert stats["flats_created"] == 5
        assert stats["skipped"] == 0

        # Each building has the correct flats
        b1937 = Building.objects.get(house_number="1937", city="Praha")
        b1938 = Building.objects.get(house_number="1938", city="Praha")
        b1939 = Building.objects.get(house_number="1939", city="Praha")

        assert Flat.objects.filter(building=b1937).count() == 2
        assert Flat.objects.filter(building=b1938).count() == 2
        assert Flat.objects.filter(building=b1939).count() == 1

        # Verify no duplicate flat_number conflict within a building
        assert Flat.objects.filter(building=b1937, flat_number="1").count() == 1
        assert Flat.objects.filter(building=b1938, flat_number="1").count() == 1

    def test_update_existing_building(self, sample_cuzk_building, sample_cuzk_units):
        """Test import updating an existing building."""
        building = Building.objects.create(
            name="Old Name",
            street="Old Street",
            house_number="1799",
            city="Brno",
            postal_code="00000",
            cuzk_building_id=951290101,
        )

        building_diffs, unit_diffs = build_import_preview(
            sample_cuzk_building,
            sample_cuzk_units,
            {1800: building},
        )
        building_actions = {1800: ACTION_UPDATE}
        unit_actions = {u.cuzk_unit.id: ACTION_CREATE for u in unit_diffs}

        stats = execute_import(building_diffs, building_actions, unit_diffs, unit_actions)

        assert stats["buildings_updated"] == 1
        building.refresh_from_db()
        assert building.house_number == "1800"
        assert building.city == "Praha"

    def test_skip_all(self, sample_cuzk_building, sample_cuzk_units):
        """Test skipping all items."""
        building_diffs, unit_diffs = build_import_preview(
            sample_cuzk_building,
            sample_cuzk_units,
        )
        building_actions = {1800: ACTION_SKIP}
        unit_actions = {u.cuzk_unit.id: ACTION_SKIP for u in unit_diffs}

        stats = execute_import(building_diffs, building_actions, unit_diffs, unit_actions)

        # Building skip + unit skips (units skipped because no building resolved)
        assert stats["skipped"] >= 1
        assert Building.objects.filter(cuzk_building_id=951290101).count() == 0

    def test_partial_import(self, sample_cuzk_building, sample_cuzk_units):
        """Test importing building and only some flats."""
        building_diffs, unit_diffs = build_import_preview(
            sample_cuzk_building,
            sample_cuzk_units,
        )
        building_actions = {1800: ACTION_CREATE}
        unit_actions = {
            sample_cuzk_units[0].id: ACTION_CREATE,
            sample_cuzk_units[1].id: ACTION_SKIP,
            sample_cuzk_units[2].id: ACTION_SKIP,
        }

        stats = execute_import(building_diffs, building_actions, unit_diffs, unit_actions)

        assert stats["buildings_created"] == 1
        assert stats["flats_created"] == 1
        assert stats["skipped"] == 2

        building = Building.objects.get(cuzk_building_id=951290101)
        assert Flat.objects.filter(building=building).count() == 1


# ---------------------------------------------------------------------------
#  View tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCUZKImportViews:
    def test_search_view_requires_login(self, client):
        resp = client.get(reverse("core:cuzk-import-search"))
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_search_view_get(self, admin_client):
        resp = admin_client.get(reverse("core:cuzk-import-search"))
        assert resp.status_code == 200
        assert "CUZK" in resp.content.decode()

    @patch("core.cuzk_import.CUZKClient")
    def test_search_view_post_success(self, mock_client_cls, admin_client, sample_cuzk_building, sample_cuzk_units):
        mock_client = MagicMock()
        mock_client.get_building_with_units.return_value = (sample_cuzk_building, sample_cuzk_units)
        mock_client_cls.return_value = mock_client

        resp = admin_client.post(
            reverse("core:cuzk-import-search"),
            {
                "cuzk_building_id": "951290101",
            },
        )
        assert resp.status_code == 302
        assert "preview" in resp.url

    def test_search_view_post_empty_id(self, admin_client):
        resp = admin_client.post(
            reverse("core:cuzk-import-search"),
            {
                "cuzk_building_id": "",
            },
        )
        assert resp.status_code == 200  # re-renders form with error

    def test_preview_view_without_session_data(self, admin_client):
        resp = admin_client.get(reverse("core:cuzk-import-preview"))
        assert resp.status_code == 302  # redirects to search

    @patch("core.cuzk_import.CUZKClient")
    def test_full_import_flow(self, mock_client_cls, admin_client, sample_cuzk_building, sample_cuzk_units):
        """Test the complete import flow: search -> preview -> execute."""
        mock_client = MagicMock()
        mock_client.get_building_with_units.return_value = (sample_cuzk_building, sample_cuzk_units)
        mock_client_cls.return_value = mock_client

        # Step 1: Search
        resp = admin_client.post(
            reverse("core:cuzk-import-search"),
            {
                "cuzk_building_id": "951290101",
            },
        )
        assert resp.status_code == 302

        # Step 2: Preview (GET)
        resp = admin_client.get(reverse("core:cuzk-import-preview"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Praha" in content
        assert "1800" in content

        # Step 3: Execute (POST) — building_action is per house number
        resp = admin_client.post(
            reverse("core:cuzk-import-preview"),
            {
                "building_action_1800": "create",
                "unit_action_145572601": "create",
                "unit_action_145572602": "create",
                "unit_action_145572603": "skip",
            },
        )
        assert resp.status_code == 302

        # Verify results
        building = Building.objects.get(cuzk_building_id=951290101)
        assert building.city == "Praha"
        assert Flat.objects.filter(building=building).count() == 2

    @patch("core.cuzk_import.CUZKClient")
    def test_full_multi_building_import_flow(self, mock_client_cls, admin_client, multi_building_cuzk):
        """Test import flow with multiple house numbers."""
        cuzk_building, cuzk_units = multi_building_cuzk
        mock_client = MagicMock()
        mock_client.get_building_with_units.return_value = (cuzk_building, cuzk_units)
        mock_client_cls.return_value = mock_client

        # Step 1: Search
        resp = admin_client.post(
            reverse("core:cuzk-import-search"),
            {"cuzk_building_id": "940255101"},
        )
        assert resp.status_code == 302

        # Step 2: Preview
        resp = admin_client.get(reverse("core:cuzk-import-preview"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "1937" in content
        assert "1938" in content
        assert "1939" in content

        # Step 3: Execute — create all buildings and all units
        post_data = {
            "building_action_1937": "create",
            "building_action_1938": "create",
            "building_action_1939": "create",
        }
        for unit in cuzk_units:
            post_data[f"unit_action_{unit.id}"] = "create"

        resp = admin_client.post(reverse("core:cuzk-import-preview"), post_data)
        assert resp.status_code == 302

        # Verify: 3 buildings, no flat_number collisions
        assert Building.objects.filter(cuzk_building_id=940255101).count() == 3
        assert Flat.objects.count() == 5

    def test_city_part_search_requires_login(self, client):
        resp = client.get(reverse("core:cuzk-city-part-search"))
        assert resp.status_code == 302

    @patch("core.cuzk_import.CUZKClient")
    def test_city_part_search_short_query(self, mock_client_cls, admin_client):
        """Queries shorter than 3 chars return empty list."""
        resp = admin_client.get(reverse("core:cuzk-city-part-search") + "?q=Ch")
        assert resp.status_code == 200
        assert resp.json() == []
