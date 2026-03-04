"""
Solomon — Owner model & view tests.
"""

import datetime

import pytest
from django.urls import reverse

from flats.tests import FlatFactory
from owners.models import FlatOwner, Owner
from owners.tests import FlatOwnerFactory, OwnerFactory


@pytest.mark.django_db
class TestOwnerModel:
    def test_create_owner(self):
        owner = OwnerFactory()
        assert owner.pk is not None

    def test_str(self):
        owner = OwnerFactory(first_name="Jan", last_name="Novák")
        assert str(owner) == "Novák Jan"

    def test_full_name(self):
        owner = OwnerFactory(first_name="Jan", last_name="Novák")
        assert owner.full_name == "Jan Novák"

    def test_person_type_choices(self):
        natural = OwnerFactory(person_type=Owner.PersonType.NATURAL)
        legal = OwnerFactory(person_type=Owner.PersonType.LEGAL)
        assert natural.person_type == "natural"
        assert legal.person_type == "legal"

    def test_soft_delete(self):
        owner = OwnerFactory()
        pk = owner.pk
        owner.delete()
        assert Owner.objects.filter(pk=pk).count() == 0
        assert Owner.all_objects.filter(pk=pk).count() == 1


@pytest.mark.django_db
class TestFlatOwnerModel:
    def test_create_flat_owner(self):
        fo = FlatOwnerFactory()
        assert fo.pk is not None
        assert fo.flat is not None
        assert fo.owner is not None

    def test_share_default(self):
        fo = FlatOwnerFactory()
        assert fo.share_numerator == 1
        assert fo.share_denominator == 1

    def test_effective_dates(self):
        fo = FlatOwnerFactory(
            effective_from=datetime.date(2020, 1, 1),
            effective_to=datetime.date(2025, 12, 31),
        )
        assert fo.effective_from == datetime.date(2020, 1, 1)
        assert fo.effective_to == datetime.date(2025, 12, 31)

    def test_str(self):
        fo = FlatOwnerFactory()
        s = str(fo)
        assert s  # Should have some string representation


@pytest.mark.django_db
class TestOwnerViews:
    def test_list_requires_login(self, client):
        url = reverse("owners:owner-list")
        resp = client.get(url)
        assert resp.status_code == 302

    def test_list_authenticated(self, admin_client):
        OwnerFactory.create_batch(3)
        url = reverse("owners:owner-list")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_detail_view(self, admin_client):
        owner = OwnerFactory()
        url = reverse("owners:owner-detail", kwargs={"pk": owner.pk})
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_create_view(self, admin_client):
        url = reverse("owners:owner-create")
        data = {
            "person_type": "natural",
            "first_name": "Karel",
            "last_name": "Dvořák",
            "email": "karel@example.cz",
            "phone": "",
            "permanent_address": "",
            "contact_address": "",
            "deputy_name": "",
            "deputy_contact": "",
            "note": "",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        assert Owner.objects.filter(last_name="Dvořák").exists()

    def test_delete_view(self, admin_client):
        owner = OwnerFactory()
        url = reverse("owners:owner-delete", kwargs={"pk": owner.pk})
        resp = admin_client.post(url)
        assert resp.status_code == 302
        assert Owner.objects.filter(pk=owner.pk).count() == 0


@pytest.mark.django_db
class TestFlatOwnerViews:
    def test_create_flatowner(self, admin_client):
        flat = FlatFactory()
        owner = OwnerFactory()
        url = reverse("owners:flatowner-create")
        data = {
            "flat": str(flat.pk),
            "owner": str(owner.pk),
            "share_numerator": 1,
            "share_denominator": 2,
            "effective_from": "2020-01-01",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        assert FlatOwner.objects.filter(flat=flat, owner=owner).exists()

    def test_delete_flatowner(self, admin_client):
        fo = FlatOwnerFactory()
        url = reverse("owners:flatowner-delete", kwargs={"pk": fo.pk})
        resp = admin_client.post(url)
        assert resp.status_code == 302
        assert FlatOwner.objects.filter(pk=fo.pk).count() == 0
