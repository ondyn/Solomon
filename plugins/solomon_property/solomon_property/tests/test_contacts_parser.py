"""Solomon Property - Unit tests for contacts import matching."""

from django.test import TestCase

from solomon_property.contacts.contacts_parser import (
    ContactRow,
    match_contacts_to_persons,
    parse_google_csv,
)
from solomon_property.models import Person


class GoogleContactsParserTest(TestCase):
    def test_multiple_phone_numbers_in_one_cell_are_preserved(self):
        csv_text = (
            "First Name,Last Name,Phone 1 - Value\r\n"
            'Jirka,Egrt,"+420 608 523 221 ::: +420 778 492 409"\r\n'
        )

        rows = parse_google_csv(csv_text)

        self.assertEqual(
            rows[0].phones,
            ["+420608523221", "+420778492409"],
        )


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
