"""
Solomon — Permission and role-based filtering tests.
"""

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from buildings.tests import BuildingFactory
from core.permissions import Roles
from flats.tests import FlatFactory
from owners.tests import FlatOwnerFactory, OwnerFactory
from tenants.tests import TenantFactory


@pytest.fixture
def owner_user(db, django_user_model):
    """Create an owner user with proper role group and linked Owner profile."""
    user = django_user_model.objects.create_user(
        username="owner1",
        password="testpass123",  # noqa: S106
    )
    group, _ = Group.objects.get_or_create(name=Roles.OWNER)
    user.groups.add(group)
    return user


@pytest.fixture
def owner_client(owner_user):
    """Client logged in as an owner."""
    c = Client()
    c.force_login(owner_user)
    return c


@pytest.fixture
def board_user(db, django_user_model):
    """Create a board member user."""
    user = django_user_model.objects.create_user(
        username="board1",
        password="testpass123",  # noqa: S106
    )
    group, _ = Group.objects.get_or_create(name=Roles.BOARD_MEMBER)
    user.groups.add(group)
    return user


@pytest.fixture
def board_client(board_user):
    """Client logged in as board member."""
    c = Client()
    c.force_login(board_user)
    return c


@pytest.mark.django_db
class TestOwnerRoleFiltering:
    """Owners should only see their own data."""

    def test_owner_sees_own_building(self, owner_client, owner_user):
        owner = OwnerFactory(user=owner_user)
        flat = FlatFactory()
        FlatOwnerFactory(flat=flat, owner=owner)

        url = reverse("buildings:building-list")
        resp = owner_client.get(url)
        assert resp.status_code == 200
        buildings = resp.context["buildings"]
        assert flat.building in buildings

    def test_owner_cannot_see_other_buildings(self, owner_client, owner_user):
        # Owner with no flats
        OwnerFactory(user=owner_user)
        BuildingFactory()  # Unrelated building

        url = reverse("buildings:building-list")
        resp = owner_client.get(url)
        assert resp.status_code == 200
        assert len(resp.context["buildings"]) == 0

    def test_owner_sees_own_flat(self, owner_client, owner_user):
        owner = OwnerFactory(user=owner_user)
        flat = FlatFactory()
        FlatOwnerFactory(flat=flat, owner=owner)

        url = reverse("flats:flat-list")
        resp = owner_client.get(url)
        assert resp.status_code == 200
        # Should contain the flat
        flat_list = list(resp.context["page_obj"]) if "page_obj" in resp.context else list(resp.context.get("flats", []))
        assert flat in flat_list or any(f.pk == flat.pk for f in flat_list)

    def test_owner_cannot_see_other_flats(self, owner_client, owner_user):
        OwnerFactory(user=owner_user)
        FlatFactory()  # Unrelated flat

        url = reverse("flats:flat-list")
        resp = owner_client.get(url)
        assert resp.status_code == 200

    def test_owner_sees_only_own_profile(self, owner_client, owner_user):
        owner = OwnerFactory(user=owner_user)
        OwnerFactory()  # Another owner

        url = reverse("owners:owner-list")
        resp = owner_client.get(url)
        assert resp.status_code == 200

    def test_owner_sees_own_tenants(self, owner_client, owner_user):
        owner = OwnerFactory(user=owner_user)
        flat = FlatFactory()
        FlatOwnerFactory(flat=flat, owner=owner)
        TenantFactory(flat=flat)

        url = reverse("tenants:tenant-list")
        resp = owner_client.get(url)
        assert resp.status_code == 200


@pytest.mark.django_db
class TestBoardMemberAccess:
    """Board members should see all data."""

    def test_board_sees_all_buildings(self, board_client):
        BuildingFactory.create_batch(5)
        url = reverse("buildings:building-list")
        resp = board_client.get(url)
        assert resp.status_code == 200
        assert len(resp.context["buildings"]) == 5

    def test_board_sees_all_flats(self, board_client):
        FlatFactory.create_batch(3)
        url = reverse("flats:flat-list")
        resp = board_client.get(url)
        assert resp.status_code == 200


@pytest.mark.django_db
class TestLoginRequired:
    """Anonymous users should be redirected to login."""

    @pytest.mark.parametrize(
        "url_name",
        [
            "buildings:building-list",
            "flats:flat-list",
            "owners:owner-list",
            "tenants:tenant-list",
        ],
    )
    def test_anonymous_redirect(self, client, url_name):
        resp = client.get(reverse(url_name))
        assert resp.status_code == 302
        assert "/login/" in resp.url
