"""
Solomon — Building model & view tests.
"""

import pytest
from django.urls import reverse

from buildings.models import Building
from buildings.tests import BuildingFactory


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestBuildingModel:
    def test_create_building(self):
        building = BuildingFactory()
        assert building.pk is not None
        assert str(building.pk).count("-") == 4  # UUID format

    def test_str(self):
        building = BuildingFactory(name="Test Building", street="Ulice", house_number="42")
        assert str(building) == "Test Building (Ulice 42)"

    def test_soft_delete(self):
        building = BuildingFactory()
        pk = building.pk
        building.delete()
        # Soft-deleted: not in default manager
        assert Building.objects.filter(pk=pk).count() == 0
        # But exists in all_objects (soft-deleted)
        assert Building.all_objects.filter(pk=pk).count() == 1

    def test_timestamps(self):
        building = BuildingFactory()
        assert building.created_at is not None
        assert building.updated_at is not None

    def test_optional_fields_blank(self):
        building = BuildingFactory(
            number_of_floors=None,
            year_built=None,
            total_units=None,
            land_plot_number="",
            common_rooms="",
            floor_plan_url="",
            common_area_rental="",
        )
        assert building.pk is not None


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestBuildingViews:
    def test_list_requires_login(self, client):
        url = reverse("buildings:building-list")
        resp = client.get(url)
        assert resp.status_code == 302
        assert "/login/" in resp.url

    def test_list_authenticated(self, admin_client):
        BuildingFactory.create_batch(3)
        url = reverse("buildings:building-list")
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert len(resp.context["buildings"]) == 3

    def test_detail_view(self, admin_client):
        building = BuildingFactory()
        url = reverse("buildings:building-detail", kwargs={"pk": building.pk})
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert resp.context["building"] == building

    def test_create_view(self, admin_client):
        url = reverse("buildings:building-create")
        data = {
            "name": "New Building",
            "street": "Ulice",
            "house_number": "42",
            "city": "Brno",
            "postal_code": "612 00",
            "elevator": False,
            "gas_installed": False,
            "land_plot_number": "",
            "common_rooms": "",
            "floor_plan_url": "",
            "common_area_rental": "",
            "note": "",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        assert Building.objects.filter(name="New Building").exists()

    def test_update_view(self, admin_client):
        building = BuildingFactory(name="Old Name")
        url = reverse("buildings:building-update", kwargs={"pk": building.pk})
        data = {
            "name": "New Name",
            "street": building.street,
            "house_number": building.house_number,
            "city": building.city,
            "postal_code": building.postal_code,
            "elevator": building.elevator,
            "land_plot_number": building.land_plot_number,
            "common_rooms": building.common_rooms,
            "floor_plan_url": building.floor_plan_url,
            "common_area_rental": "",
            "note": "",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        building.refresh_from_db()
        assert building.name == "New Name"

    def test_delete_view(self, admin_client):
        building = BuildingFactory()
        url = reverse("buildings:building-delete", kwargs={"pk": building.pk})
        resp = admin_client.post(url)
        assert resp.status_code == 302
        # Soft-deleted
        assert Building.objects.filter(pk=building.pk).count() == 0
