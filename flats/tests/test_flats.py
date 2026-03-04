"""
Solomon — Flat model & view tests.
"""

import pytest
from django.urls import reverse

from buildings.tests import BuildingFactory
from flats.models import Flat
from flats.tests import FlatFactory


@pytest.mark.django_db
class TestFlatModel:
    def test_create_flat(self):
        flat = FlatFactory()
        assert flat.pk is not None
        assert flat.building is not None

    def test_str(self):
        flat = FlatFactory(flat_number="42")
        assert "42" in str(flat)

    def test_soft_delete(self):
        flat = FlatFactory()
        pk = flat.pk
        flat.delete()
        assert Flat.objects.filter(pk=pk).count() == 0
        assert Flat.all_objects.filter(pk=pk).count() == 1

    def test_unique_together(self):
        building = BuildingFactory()
        FlatFactory(building=building, flat_number="1")
        with pytest.raises(Exception):
            FlatFactory(building=building, flat_number="1")

    def test_optional_fields(self):
        flat = FlatFactory(
            floor=None,
            area_m2=None,
            number_of_rooms=None,
            water_outlets=None,
            waste_outlets=None,
            radiator_count=None,
            radiator_power_kw=None,
        )
        assert flat.pk is not None


@pytest.mark.django_db
class TestFlatViews:
    def test_list_requires_login(self, client):
        url = reverse("flats:flat-list")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_list_authenticated(self, admin_client):
        FlatFactory.create_batch(3)
        url = reverse("flats:flat-list")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_detail_view(self, admin_client):
        flat = FlatFactory()
        url = reverse("flats:flat-detail", kwargs={"pk": flat.pk})
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_create_view(self, admin_client):
        building = BuildingFactory()
        url = reverse("flats:flat-create")
        data = {
            "building": str(building.pk),
            "flat_number": "99",
            "floor": 3,
            "area_m2": "65.50",
            "disposition": "2+1",
            "gas_installed": False,
            "has_balcony": False,
            "cellar_unit": "",
            "ownership_cert_number": "",
            "note": "",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        assert Flat.objects.filter(flat_number="99").exists()

    def test_delete_view(self, admin_client):
        flat = FlatFactory()
        url = reverse("flats:flat-delete", kwargs={"pk": flat.pk})
        resp = admin_client.post(url)
        assert resp.status_code == 302
        assert Flat.objects.filter(pk=flat.pk).count() == 0
