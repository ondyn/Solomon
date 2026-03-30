"""
Solomon — Tests for CUZK import functionality.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.test import Client, TestCase
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
    CUZKClient,
    CUZKShare,
    CUZKTitleDeed,
    CUZKUnit,
    CUZKUnitRef,
)
from flats.models import Flat


# ---------------------------------------------------------------------------
#  Test helpers / fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_cuzk_building():
    """A sample CUZK building response."""
    return CUZKBuilding(
        id=951290101,
        building_type_code=1,
        building_type_name="budova s číslem popisným",
        house_numbers=[1800],
        municipality_code=554782,
        municipality_name="Praha",
        city_part_code=400611,
        city_part_name="Chodov",
        usage_code=6,
        usage_name="bytový dům",
        lv=CUZKTitleDeed(id=123, number=10136, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
        unit_refs=[
            CUZKUnitRef(id=145572601, unit_number=1),
            CUZKUnitRef(id=145572602, unit_number=2),
            CUZKUnitRef(id=145572603, unit_number=3),
        ],
    )


@pytest.fixture
def sample_cuzk_units():
    """Sample CUZK units."""
    return [
        CUZKUnit(
            id=145572601, unit_number=1,
            unit_type_code=3, unit_type_name="byt",
            share=CUZKShare(numerator=650, denominator=10000),
            lv=CUZKTitleDeed(id=200, number=10137, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
            building_id=951290101,
        ),
        CUZKUnit(
            id=145572602, unit_number=2,
            unit_type_code=3, unit_type_name="byt",
            share=CUZKShare(numerator=480, denominator=10000),
            lv=CUZKTitleDeed(id=201, number=10138, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
            building_id=951290101,
        ),
        CUZKUnit(
            id=145572603, unit_number=3,
            unit_type_code=3, unit_type_name="byt",
            share=CUZKShare(numerator=520, denominator=10000),
            lv=CUZKTitleDeed(id=202, number=10139, cadastral_territory_code=728225, cadastral_territory_name="Chodov"),
            building_id=951290101,
        ),
    ]


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
        lv = CUZKTitleDeed.from_api({
            "id": 123,
            "cislo": 10136,
            "katastralniUzemi": {"kod": 728225, "nazev": "Chodov"},
        })
        assert lv is not None
        assert lv.number == 10136
        assert lv.cadastral_territory_name == "Chodov"

    def test_building_from_api(self):
        data = {
            "id": 951290101,
            "typStavby": {"kod": 1, "nazev": "budova s číslem popisným"},
            "cislaDomovni": [1800],
            "obec": {"kod": 554782, "nazev": "Praha"},
            "castObce": {"kod": 400611, "nazev": "Chodov"},
            "zpusobVyuziti": {"kod": 6, "nazev": "bytový dům"},
            "lv": {"id": 123, "cislo": 10136, "katastralniUzemi": {"kod": 728225, "nazev": "Chodov"}},
            "jednotky": [
                {"id": 145572601, "cisloJednotky": 1},
                {"id": 145572602, "cisloJednotky": 2},
            ],
        }
        building = CUZKBuilding.from_api(data)
        assert building.id == 951290101
        assert building.house_numbers == [1800]
        assert building.municipality_name == "Praha"
        assert len(building.unit_refs) == 2
        assert building.lv.number == 10136

    def test_unit_from_api(self):
        data = {
            "id": 145572601,
            "cisloJednotky": 1,
            "typJednotky": {"kod": 3, "nazev": "byt"},
            "zpusobVyuziti": {"kod": 2, "nazev": "byt"},
            "podilNaSpolecnychCastechDomu": {"citatel": 650, "jmenovatel": 10000},
            "lv": {"id": 200, "cislo": 10137, "katastralniUzemi": {"kod": 728225, "nazev": "Chodov"}},
            "vymezenaVeStavbe": {"id": 951290101},
        }
        unit = CUZKUnit.from_api(data)
        assert unit.id == 145572601
        assert unit.unit_number == 1
        assert unit.share.numerator == 650
        assert unit.share.denominator == 10000
        assert unit.building_id == 951290101


# ---------------------------------------------------------------------------
#  Import diff computation tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestImportDiff:
    def test_building_diff_new(self, sample_cuzk_building):
        """Test diff when no existing building exists."""
        diff = compute_building_diff(sample_cuzk_building, None)
        assert diff.suggested_action == ACTION_CREATE
        assert diff.existing_building is None
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
        diff = compute_building_diff(sample_cuzk_building, building)
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
        diff = compute_building_diff(sample_cuzk_building, building)
        assert diff.suggested_action == ACTION_UPDATE
        house_diff = next(d for d in diff.field_diffs if d.field_name == "house_number")
        assert house_diff.is_changed

    def test_unit_diff_new(self, sample_cuzk_units):
        """Test diff when no existing flat exists."""
        diff = compute_unit_diff(sample_cuzk_units[0], None)
        assert diff.suggested_action == ACTION_CREATE
        assert diff.existing_flat is None

    def test_unit_diff_no_changes(self, sample_cuzk_units):
        """Test diff when flat exists with same CUZK data."""
        building = Building.objects.create(
            name="Test", street="Test", house_number="1", city="Test", postal_code="00000",
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
            name="Test", street="Test", house_number="1", city="Test", postal_code="00000",
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
#  Import execution tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestImportExecution:
    def test_create_building_and_flats(self, sample_cuzk_building, sample_cuzk_units):
        """Test full import creating a new building with flats."""
        building_diff, unit_diffs = build_import_preview(
            sample_cuzk_building, sample_cuzk_units,
        )
        unit_actions = {u.cuzk_unit.id: ACTION_CREATE for u in unit_diffs}

        stats = execute_import(building_diff, ACTION_CREATE, unit_diffs, unit_actions)

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

        building_diff, unit_diffs = build_import_preview(
            sample_cuzk_building, sample_cuzk_units, building,
        )
        unit_actions = {u.cuzk_unit.id: ACTION_CREATE for u in unit_diffs}

        stats = execute_import(building_diff, ACTION_UPDATE, unit_diffs, unit_actions)

        assert stats["buildings_updated"] == 1
        building.refresh_from_db()
        assert building.house_number == "1800"
        assert building.city == "Praha"

    def test_skip_items(self, sample_cuzk_building, sample_cuzk_units):
        """Test skipping all items — building skip means units won't be processed."""
        building_diff, unit_diffs = build_import_preview(
            sample_cuzk_building, sample_cuzk_units,
        )
        unit_actions = {u.cuzk_unit.id: ACTION_SKIP for u in unit_diffs}

        stats = execute_import(building_diff, ACTION_SKIP, unit_diffs, unit_actions)

        # When building is skipped, there's no building to attach units to,
        # so only the building skip is counted
        assert stats["skipped"] == 1
        assert Building.objects.filter(cuzk_building_id=951290101).count() == 0

    def test_partial_import(self, sample_cuzk_building, sample_cuzk_units):
        """Test importing building and only some flats."""
        building_diff, unit_diffs = build_import_preview(
            sample_cuzk_building, sample_cuzk_units,
        )
        # Create building, import first unit, skip others
        unit_actions = {
            sample_cuzk_units[0].id: ACTION_CREATE,
            sample_cuzk_units[1].id: ACTION_SKIP,
            sample_cuzk_units[2].id: ACTION_SKIP,
        }

        stats = execute_import(building_diff, ACTION_CREATE, unit_diffs, unit_actions)

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

        resp = admin_client.post(reverse("core:cuzk-import-search"), {
            "cuzk_building_id": "951290101",
        })
        assert resp.status_code == 302
        assert "preview" in resp.url

    def test_search_view_post_empty_id(self, admin_client):
        resp = admin_client.post(reverse("core:cuzk-import-search"), {
            "cuzk_building_id": "",
        })
        assert resp.status_code == 200  # re-renders form with error

    def test_preview_view_without_session_data(self, admin_client):
        resp = admin_client.get(reverse("core:cuzk-import-preview"))
        assert resp.status_code == 302  # redirects to search

    @patch("core.cuzk_import.CUZKClient")
    def test_full_import_flow(self, mock_client_cls, admin_client, sample_cuzk_building, sample_cuzk_units):
        """Test the complete import flow: search → preview → execute."""
        mock_client = MagicMock()
        mock_client.get_building_with_units.return_value = (sample_cuzk_building, sample_cuzk_units)
        mock_client_cls.return_value = mock_client

        # Step 1: Search
        resp = admin_client.post(reverse("core:cuzk-import-search"), {
            "cuzk_building_id": "951290101",
        })
        assert resp.status_code == 302

        # Step 2: Preview (GET)
        resp = admin_client.get(reverse("core:cuzk-import-preview"))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Praha" in content
        assert "1800" in content

        # Step 3: Execute (POST)
        resp = admin_client.post(reverse("core:cuzk-import-preview"), {
            "building_action": "create",
            "unit_action_145572601": "create",
            "unit_action_145572602": "create",
            "unit_action_145572603": "skip",
        })
        assert resp.status_code == 302

        # Verify results
        building = Building.objects.get(cuzk_building_id=951290101)
        assert building.city == "Praha"
        assert Flat.objects.filter(building=building).count() == 2
