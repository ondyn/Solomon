"""Solomon Property - Unit tests for contacts import matching."""

from django.test import TestCase

from solomon_property.contacts.contacts_parser import ContactRow, match_contacts_to_persons
from solomon_property.models import Person


class ContactMatcherTest(TestCase):
    def test_last_name_with_flat_metadata_matches_owner_person(self):
        person = Person.objects.create(first_name="Matěj", last_name="Pejsar")

        row = ContactRow(
            row_number=1,
            first_name="Matej",
            last_name="Pejsar 1939 whatever 4 3+1",
            phones=["+420123123123"],
        )

        matched = match_contacts_to_persons([row])[0]

        self.assertEqual(matched.match_status, "matched")
        self.assertEqual(matched.matched_person, person)
        self.assertEqual(matched.match_note, "exact")
