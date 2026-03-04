"""
Solomon — Shared pytest fixtures.

This file is automatically discovered by pytest.
"""

import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    """Django test client."""
    return Client()


@pytest.fixture
def admin_client(client: Client, admin_user) -> Client:
    """Django test client logged in as admin."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def admin_user(db, django_user_model):
    """Create an admin superuser."""
    return django_user_model.objects.create_superuser(
        username="admin",
        email="admin@test.cz",
        password="testpass123",  # noqa: S106
    )
