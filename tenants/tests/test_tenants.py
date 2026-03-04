"""
Solomon — Tenant model & view tests.
"""

import datetime

import pytest
from django.urls import reverse

from flats.tests import FlatFactory
from tenants.models import Tenant
from tenants.tests import TenantFactory


@pytest.mark.django_db
class TestTenantModel:
    def test_create_tenant(self):
        tenant = TenantFactory()
        assert tenant.pk is not None

    def test_str(self):
        tenant = TenantFactory(first_name="Jan", last_name="Novák")
        assert "Novák" in str(tenant)
        assert "Jan" in str(tenant)

    def test_full_name(self):
        tenant = TenantFactory(first_name="Jan", last_name="Novák")
        assert tenant.full_name == "Jan Novák"

    def test_soft_delete(self):
        tenant = TenantFactory()
        pk = tenant.pk
        tenant.delete()
        assert Tenant.objects.filter(pk=pk).count() == 0
        assert Tenant.all_objects.filter(pk=pk).count() == 1

    def test_effective_dates(self):
        tenant = TenantFactory(
            effective_from=datetime.date(2023, 1, 1),
            effective_to=datetime.date(2024, 12, 31),
        )
        assert tenant.effective_from == datetime.date(2023, 1, 1)
        assert tenant.effective_to == datetime.date(2024, 12, 31)


@pytest.mark.django_db
class TestTenantViews:
    def test_list_requires_login(self, client):
        url = reverse("tenants:tenant-list")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_list_authenticated(self, admin_client):
        TenantFactory.create_batch(3)
        url = reverse("tenants:tenant-list")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_detail_view(self, admin_client):
        tenant = TenantFactory()
        url = reverse("tenants:tenant-detail", kwargs={"pk": tenant.pk})
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_create_view(self, admin_client):
        flat = FlatFactory()
        url = reverse("tenants:tenant-create")
        data = {
            "flat": str(flat.pk),
            "first_name": "Marie",
            "last_name": "Svobodová",
            "email": "marie@example.cz",
            "phone": "",
            "permanent_address": "",
            "contact_address": "",
            "effective_from": "2023-06-01",
            "note": "",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        assert Tenant.objects.filter(last_name="Svobodová").exists()

    def test_delete_view(self, admin_client):
        tenant = TenantFactory()
        url = reverse("tenants:tenant-delete", kwargs={"pk": tenant.pk})
        resp = admin_client.post(url)
        assert resp.status_code == 302
        assert Tenant.objects.filter(pk=tenant.pk).count() == 0
