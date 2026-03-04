"""
Solomon — User administration tests.
"""

import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse

from core.permissions import Roles


@pytest.fixture
def _setup_groups(db):
    """Ensure role groups exist."""
    for role_name in [Roles.ADMIN, Roles.CHAIRMAN, Roles.BOARD_MEMBER, Roles.OWNER]:
        Group.objects.get_or_create(name=role_name)


@pytest.mark.django_db
@pytest.mark.usefixtures("_setup_groups")
class TestUserViews:
    def test_user_list_requires_permission(self, client, django_user_model):
        """Regular user without view_user permission cannot see user list."""
        user = django_user_model.objects.create_user(username="regular", password="test123")
        client.force_login(user)
        url = reverse("accounts:user-list")
        resp = client.get(url)
        assert resp.status_code == 403

    def test_user_list_admin(self, admin_client):
        url = reverse("accounts:user-list")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_user_create(self, admin_client):
        url = reverse("accounts:user-create")
        data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "new@example.cz",
            "is_active": True,
            "password1": "testpass123!",
            "password2": "testpass123!",
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        assert User.objects.filter(username="newuser").exists()

    def test_user_detail(self, admin_client, admin_user):
        url = reverse("accounts:user-detail", kwargs={"pk": admin_user.pk})
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_user_update(self, admin_client, admin_user):
        url = reverse("accounts:user-update", kwargs={"pk": admin_user.pk})
        data = {
            "username": admin_user.username,
            "first_name": "Updated",
            "last_name": "Admin",
            "email": "updated@test.cz",
            "is_active": True,
        }
        resp = admin_client.post(url, data)
        assert resp.status_code == 302
        admin_user.refresh_from_db()
        assert admin_user.first_name == "Updated"
