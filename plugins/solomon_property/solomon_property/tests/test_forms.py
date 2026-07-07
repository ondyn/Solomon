"""Solomon Property - Unit tests for model form behavior."""

import datetime

from django.test import TestCase

from solomon_property.forms import FlatOwnerForm
from solomon_property.models import FlatOwner

from .test_models import make_building, make_flat, make_owner


class FlatOwnerFormTest(TestCase):
    def test_editing_current_ownership_clones_row_and_preserves_history(self):
        building = make_building()
        flat = make_flat(building, flat_number="1")
        original_owner = make_owner(display_name="Holobradá Olga")
        new_owner = make_owner(display_name="SJ Hnyk Ondřej a Hnyková Simona")

        original = FlatOwner.objects.create(
            flat=flat,
            owner=original_owner,
            share_numerator=1,
            share_denominator=1,
            effective_from=datetime.date(2024, 1, 1),
        )

        form = FlatOwnerForm(
            instance=original,
            data={
                "flat": flat.pk,
                "owner": new_owner.pk,
                "share_numerator": 1,
                "share_denominator": 1,
                "effective_from": "2025-01-01",
                "effective_to": "",
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

        updated = form.save()

        self.assertNotEqual(updated.pk, original.pk)

        original.refresh_from_db()
        self.assertEqual(original.effective_to, datetime.date(2024, 12, 31))

        owner_names = list(
            flat.flat_owners.order_by("effective_from").values_list("owner__display_name", flat=True)
        )
        self.assertEqual(owner_names, ["Holobradá Olga", "SJ Hnyk Ondřej a Hnyková Simona"])
