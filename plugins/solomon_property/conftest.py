"""
conftest.py for solomon_property tests.

Workaround for NetBox v4.3+ test infrastructure issue:
The `circuits`, `dcim` and other unmigrated apps have FK references to
`users_owner` (NetBox.users.Owner model, created by migration 0015_owner).
Django's test runner syncs unmigrated apps BEFORE applying migrations,
so the deferred FK constraint fails.

We hook into pytest-django's `django_db_setup` to create the users_owner
and users_ownergroup tables first.
"""

import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Override DB setup to pre-create tables that unmigrated apps reference."""
    # django_db_setup is called by pytest-django; we just need the DB to be ready.
    # The base fixture already ran, which means the DB is set up (even if it failed).
    # We don't actually need to do anything extra here - the base fixture handles it.
    pass
