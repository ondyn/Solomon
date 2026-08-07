"""Solomon Property - Unit tests for view behavior."""

import datetime

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import FieldDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase

from solomon_property.contacts_views import ContactsExportView, ContactsImportView
from solomon_property.filtersets import PropertyOwnerFilterSet
from solomon_property.models import FlatOwner, PropertyOwner
from solomon_property.tables import PersonCompactTable, PersonTable, PropertyOwnerTable
from solomon_property.views import FlatView
from solomon_property.views import PersonView

from .test_models import make_building, make_flat, make_owner, make_person


def add_session_and_messages(request):
    SessionMiddleware(lambda response: response).process_request(request)
    request._messages = FallbackStorage(request)
    request.user = AnonymousUser()
    return request


class ArrayListTemplateTest(TestCase):
    def test_phone_values_render_as_clickable_rows(self):
        rendered = render_to_string(
            "solomon_property/attrs/phone_list.html",
            {"value": ["+420608523221", "+420778492409"]},
        )

        self.assertHTMLEqual(
            rendered,
            '<div class="d-grid gap-1">'
            '<div class="text-break">'
            '<a href="tel:+420608523221">+420608523221</a>'
            "</div>"
            '<div class="text-break">'
            '<a href="tel:+420778492409">+420778492409</a>'
            "</div>"
            "</div>",
        )

    def test_email_values_render_as_clickable_rows(self):
        rendered = render_to_string(
            "solomon_property/attrs/email_list.html",
            {"value": ["jiri@example.com", "egrt@example.com"]},
        )

        self.assertIn('href="mailto:jiri@example.com"', rendered)
        self.assertIn('href="mailto:egrt@example.com"', rendered)


class ContactTableTest(TestCase):
    def test_person_tables_render_all_phone_and_email_links(self):
        person = make_person(
            emails=["jiri@example.com", "egrt@example.com"],
            phones=["+420608523221", "+420778492409"],
        )
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        for table_class in (PersonTable, PersonCompactTable):
            with self.subTest(table=table_class.__name__):
                rendered = table_class([person]).as_html(request)
                self.assertIn('href="mailto:jiri@example.com"', rendered)
                self.assertIn('href="mailto:egrt@example.com"', rendered)
                self.assertIn('href="tel:+420608523221"', rendered)
                self.assertIn('href="tel:+420778492409"', rendered)

    def test_owner_model_and_table_do_not_expose_contact_fields(self):
        for field_name in ("email", "phone"):
            with self.subTest(field=field_name):
                with self.assertRaises(FieldDoesNotExist):
                    PropertyOwner._meta.get_field(field_name)
                self.assertNotIn(field_name, PropertyOwnerTable.base_columns)


class PropertyOwnerFilterSetTest(TestCase):
    def test_search_uses_owner_name_and_linked_person_contacts(self):
        owner = make_owner(display_name="SJ Egrt Jiří a Egrtová Šárka")
        owner.persons.add(
            make_person(
                first_name="Jiří",
                last_name="Egrt",
                emails=["jiri.egrt@example.com"],
                phones=["+420608523221"],
            ),
            make_person(
                first_name="Šárka",
                last_name="Egrtová",
                emails=["sarka.egrt@example.com"],
            ),
        )
        make_owner(display_name="Unrelated owner")

        for search_term in (
            "SJ Egrt",
            "Jiří",
            "Egrt",
            "jiri.egrt@example.com",
            "+420608523221",
        ):
            with self.subTest(search_term=search_term):
                queryset = PropertyOwnerFilterSet(
                    {"q": search_term},
                    queryset=PropertyOwner.objects.all(),
                ).qs
                self.assertEqual(list(queryset), [owner])


class ContactsImportViewTest(TestCase):
    def test_uploaded_csv_is_still_parsed_and_saved_for_preview(self):
        csv_file = SimpleUploadedFile(
            "contacts.csv",
            (
                b"First Name,Last Name,E-mail 1 - Value\r\n"
                b"Jan,Novak,jan@example.com\r\n"
            ),
            content_type="text/csv",
        )
        request = add_session_and_messages(
            RequestFactory().post(
                "/plugins/property/contacts/import/",
                {"action": "upload", "csv_file": csv_file},
            )
        )

        response = ContactsImportView().post(request)

        self.assertEqual(response.status_code, 302)
        rows = request.session["contacts_import_rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["emails"], ["jan@example.com"])

    def test_pasted_csv_is_parsed_and_saved_for_preview(self):
        csv_content = (
            "First Name,Last Name,E-mail 1 - Value,Phone 1 - Value\r\n"
            "Jan,Novak,jan@example.com,+420123456789\r\n"
        )
        request = add_session_and_messages(
            RequestFactory().post(
                "/plugins/property/contacts/import/",
                {"action": "upload", "csv_content": csv_content},
            )
        )

        response = ContactsImportView().post(request)

        self.assertEqual(response.status_code, 302)
        rows = request.session["contacts_import_rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["first_name"], "Jan")
        self.assertEqual(rows[0]["emails"], ["jan@example.com"])


class ContactsExportViewTest(TestCase):
    def setUp(self):
        self.person = make_person(
            first_name="Jan",
            last_name="Novak",
            emails=["jan@example.com"],
        )

    def test_copy_action_renders_csv_in_textarea(self):
        request = add_session_and_messages(
            RequestFactory().post(
                "/plugins/property/contacts/export/",
                {"include_others": "1", "action": "copy"},
            )
        )

        response = ContactsExportView().post(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="csv_content"')
        self.assertContains(response, "jan@example.com")

    def test_download_action_still_returns_csv_attachment(self):
        request = add_session_and_messages(
            RequestFactory().post(
                "/plugins/property/contacts/export/",
                {"include_others": "1", "action": "download"},
            )
        )

        response = ContactsExportView().post(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("jan@example.com", response.content.decode())


class PersonViewTest(TestCase):
    def test_person_ownership_table_orders_by_effective_from_desc(self):
        person = make_person(first_name="Ondrej", last_name="Hnyk")
        building = make_building(name="Salounova 1")
        flat = make_flat(building, flat_number="101")
        owner = make_owner(display_name="Ondrej Hnyk")
        owner.persons.add(person)

        older = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2023, 1, 1),
        )
        newer = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2024, 1, 1),
        )

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        context = PersonView().get_extra_context(request, person)

        ownership_table = context["ownership_table"]
        ownership_ids = [row.record.pk for row in ownership_table.rows]

        self.assertEqual(ownership_ids, [newer.pk, older.pk])


class FlatViewTest(TestCase):
    def test_ownership_history_orders_by_effective_from_desc(self):
        building = make_building(name="Salounova 1")
        flat = make_flat(building, flat_number="101")
        owner = make_owner(display_name="Ondrej Hnyk")

        older = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2026, 7, 3),
            effective_to=datetime.date(2026, 7, 5),
        )
        middle = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2026, 7, 5),
            effective_to=datetime.date(2026, 7, 6),
        )
        newest = FlatOwner.objects.create(
            flat=flat,
            owner=owner,
            share_numerator=1,
            share_denominator=2,
            effective_from=datetime.date(2026, 7, 7),
        )

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        context = FlatView().get_extra_context(request, flat)

        owner_table = context["owner_table"]
        ownership_ids = [row.record.pk for row in owner_table.rows]

        self.assertEqual(ownership_ids, [newest.pk, middle.pk, older.pk])
