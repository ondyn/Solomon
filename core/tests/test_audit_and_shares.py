"""
Solomon — Audit trail and ownership share validation tests.
"""

import pytest
from auditlog.models import LogEntry
from django.urls import reverse

from buildings.tests import BuildingFactory
from flats.tests import FlatFactory
from owners.tests import FlatOwnerFactory, OwnerFactory


@pytest.mark.django_db
class TestAuditTrail:
    """Verify that django-auditlog records create/update/delete events."""

    def test_building_create_logged(self):
        building = BuildingFactory()
        entries = LogEntry.objects.filter(
            object_pk=str(building.pk),
        )
        assert entries.count() >= 1

    def test_building_update_logged(self):
        building = BuildingFactory(name="Old Name")
        building.name = "New Name"
        building.save()
        update_entries = LogEntry.objects.filter(
            object_pk=str(building.pk),
            action=LogEntry.Action.UPDATE,
        )
        assert update_entries.count() >= 1

    def test_owner_create_logged(self):
        owner = OwnerFactory()
        entries = LogEntry.objects.filter(
            object_pk=str(owner.pk),
        )
        assert entries.count() >= 1


@pytest.mark.django_db
class TestAuditLogViews:
    def test_auditlog_list_view(self, admin_client):
        BuildingFactory()  # Trigger at least one log entry
        url = reverse("core:auditlog-list")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_auditlog_list_requires_login(self, client):
        url = reverse("core:auditlog-list")
        resp = client.get(url)
        assert resp.status_code == 302


@pytest.mark.django_db
class TestOwnershipShareValidation:
    """Verify that ownership shares summing != 100% trigger warnings."""

    def test_share_sums_to_100(self, admin_client):
        flat = FlatFactory()
        owner = OwnerFactory()
        url = reverse("owners:flatowner-create")
        data = {
            "flat": str(flat.pk),
            "owner": str(owner.pk),
            "share_numerator": 1,
            "share_denominator": 1,  # 100%
            "effective_from": "2020-01-01",
        }
        resp = admin_client.post(url, data, follow=True)
        assert resp.status_code == 200
        # No warning messages about shares
        msgs = [str(m) for m in resp.context.get("messages", [])]
        share_warnings = [m for m in msgs if "100" in m]
        # With 100% share, should not have warning
        assert len(share_warnings) == 0

    def test_share_not_100_triggers_warning(self, admin_client):
        flat = FlatFactory()
        owner = OwnerFactory()
        url = reverse("owners:flatowner-create")
        data = {
            "flat": str(flat.pk),
            "owner": str(owner.pk),
            "share_numerator": 1,
            "share_denominator": 3,  # 33.3%
            "effective_from": "2020-01-01",
        }
        resp = admin_client.post(url, data, follow=True)
        assert resp.status_code == 200
        # Should have a warning message about shares not summing to 100%
        msgs = [str(m) for m in resp.context.get("messages", [])]
        share_warnings = [m for m in msgs if "100" in m or "podíl" in m.lower()]
        assert len(share_warnings) >= 1

    def test_flat_detail_shows_share_total(self, admin_client):
        flat = FlatFactory()
        owner1 = OwnerFactory()
        owner2 = OwnerFactory()
        FlatOwnerFactory(flat=flat, owner=owner1, share_numerator=1, share_denominator=2)
        FlatOwnerFactory(flat=flat, owner=owner2, share_numerator=1, share_denominator=2)

        url = reverse("flats:flat-detail", kwargs={"pk": flat.pk})
        resp = admin_client.get(url)
        assert resp.status_code == 200
        # Context should include ownership_total_pct
        assert "ownership_total_pct" in resp.context
