"""
Solomon Property - Contacts import/export views.

Provides:
  - ContactsImportView  - upload Google CSV, preview matches, execute import
  - ContactsExportView  - download all persons as Google Contacts CSV
"""

from __future__ import annotations

import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from solomon_property.contacts.contacts_parser import (
    ContactRow,
    build_export_queryset,
    execute_contacts_import,
    export_persons_to_google_csv,
    match_contacts_to_persons,
    parse_google_csv,
)
from solomon_property.models import Building, Person

logger = logging.getLogger(__name__)


class ContactsImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Two-step import of Google Contacts CSV:
      1. Upload CSV -> parse & match -> show preview
      2. User selects rows to import -> execute
    """
    template_name = "solomon_property/contacts_import.html"
    permission_required = "solomon_property.import_contacts_data"
    raise_exception = True

    def get(self, request):
        # If there's parsed data in session, show preview
        preview_data = request.session.get("contacts_import_rows")
        if preview_data:
            rows = self._deserialize_rows(preview_data)
            rows = match_contacts_to_persons(rows)
            # Only show rows that actually matched something and have data to import
            preview_rows = [
                r for r in rows
                if r.match_status in ("matched", "ambiguous") and r.has_useful_data
            ]
            matched = sum(1 for r in rows if r.match_status == "matched" and r.has_useful_data)
            ambiguous = sum(1 for r in rows if r.match_status == "ambiguous" and r.has_useful_data)
            total_with_data = sum(1 for r in rows if r.has_useful_data)
            return render(request, self.template_name, {
                "title": _("Import Contacts from Google CSV"),
                "rows": preview_rows,
                "preview": True,
                "matched_count": matched,
                "ambiguous_count": ambiguous,
                "total_with_data": total_with_data,
                "total_rows": len(rows),
            })
        return render(request, self.template_name, {
            "title": _("Import Contacts from Google CSV"),
            "preview": False,
        })

    def post(self, request):
        action = request.POST.get("action", "upload")

        if action == "upload":
            return self._handle_upload(request)
        elif action == "import":
            return self._handle_import(request)
        elif action == "cancel":
            request.session.pop("contacts_import_rows", None)
            return redirect(reverse("plugins:solomon_property:contacts-import"))

        return redirect(reverse("plugins:solomon_property:contacts-import"))

    def _handle_upload(self, request):
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, _("Please select a CSV file."))
            return render(request, self.template_name, {
                "title": _("Import Contacts from Google CSV"),
                "preview": False,
            })

        try:
            csv_text = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                csv_file.seek(0)
                csv_text = csv_file.read().decode("latin-1")
            except Exception:
                messages.error(request, _("Unable to read the CSV file. Check encoding."))
                return render(request, self.template_name, {
                    "title": _("Import Contacts from Google CSV"),
                    "preview": False,
                })

        rows = parse_google_csv(csv_text)
        if not rows:
            messages.warning(request, _("No contacts found in the CSV file."))
            return render(request, self.template_name, {
                "title": _("Import Contacts from Google CSV"),
                "preview": False,
            })

        # Store in session (only serializable data)
        request.session["contacts_import_rows"] = self._serialize_rows(rows)
        return redirect(reverse("plugins:solomon_property:contacts-import"))

    def _handle_import(self, request):
        preview_data = request.session.get("contacts_import_rows")
        if not preview_data:
            messages.error(request, _("Session expired. Please upload the CSV again."))
            return redirect(reverse("plugins:solomon_property:contacts-import"))

        rows = self._deserialize_rows(preview_data)
        rows = match_contacts_to_persons(rows)

        merge_mode = request.POST.get("merge_mode", "append")

        # Collect selected row indices
        selected = set()
        person_overrides = {}
        for key, val in request.POST.items():
            if key.startswith("select_"):
                try:
                    idx = int(key.split("_", 1)[1])
                    selected.add(idx)
                except (ValueError, IndexError):
                    pass
            elif key.startswith("person_"):
                try:
                    idx = int(key.split("_", 1)[1])
                    person_overrides[idx] = int(val)
                except (ValueError, IndexError):
                    pass

        if not selected:
            messages.warning(request, _("No contacts selected for import."))
            return redirect(reverse("plugins:solomon_property:contacts-import"))

        results = execute_contacts_import(rows, selected, person_overrides, merge_mode)

        # Clean up session
        del request.session["contacts_import_rows"]

        # Summary
        errors = [r for r in results if r.error]
        total_emails = sum(r.emails_added for r in results)
        total_phones = sum(r.phones_added for r in results)
        updated = sum(1 for r in results if r.person and (r.emails_added or r.phones_added))

        if errors:
            for r in errors:
                messages.warning(request, _("%(name)s: %(err)s") % {
                    "name": r.row.display_name, "err": r.error
                })

        messages.success(request, _(
            "Import complete: %(u)d person(s) updated, "
            "%(e)d email(s) added, %(p)d phone(s) added."
        ) % {"u": updated, "e": total_emails, "p": total_phones})

        return redirect(reverse("plugins:solomon_property:person_list"))

    @staticmethod
    def _serialize_rows(rows: list[ContactRow]) -> list[dict]:
        return [
            {
                "row_number": r.row_number,
                "list_index": r.list_index,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "title_before": r.title_before,
                "title_after": r.title_after,
                "emails": r.emails,
                "phones": r.phones,
                "address": r.address,
                "birthday": r.birthday,
                "organization": r.organization,
                "notes": r.notes,
            }
            for r in rows
        ]

    @staticmethod
    def _deserialize_rows(data: list[dict]) -> list[ContactRow]:
        return [
            ContactRow(
                row_number=d["row_number"],
                list_index=d.get("list_index", i),
                first_name=d["first_name"],
                last_name=d["last_name"],
                title_before=d.get("title_before", ""),
                title_after=d.get("title_after", ""),
                emails=d["emails"],
                phones=d["phones"],
                address=d.get("address", ""),
                birthday=d.get("birthday", ""),
                organization=d.get("organization", ""),
                notes=d.get("notes", ""),
            )
            for i, d in enumerate(data)
        ]


class ContactsExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Two-step export of persons as Google Contacts CSV.

    GET  - show export filter form (buildings, roles)
    POST - apply filters and stream the CSV file download
    """
    template_name = "solomon_property/contacts_export.html"
    permission_required = "solomon_property.export_contacts_data"
    raise_exception = True

    def get(self, request):
        buildings = Building.objects.order_by("name")
        return render(request, self.template_name, {
            "title": _("Export Contacts to Google CSV"),
            "buildings": buildings,
            "is_initial": True,
            "include_owners": True,
            "include_tenants": False,
            "include_others": False,
            "selected_buildings": [],
        })

    def post(self, request):
        building_ids = request.POST.getlist("buildings")  # list of str PKs, may be empty
        include_owners = "include_owners" in request.POST
        include_tenants = "include_tenants" in request.POST
        include_others = "include_others" in request.POST

        if not any([include_owners, include_tenants, include_others]):
            messages.error(request, _("Please select at least one contact group to export."))
            buildings = Building.objects.order_by("name")
            return render(request, self.template_name, {
                "title": _("Export Contacts to Google CSV"),
                "buildings": buildings,
                "selected_buildings": building_ids,
                "include_owners": include_owners,
                "include_tenants": include_tenants,
                "include_others": include_others,
            })

        # Convert to ints (ignore invalid values)
        try:
            building_id_ints = [int(bid) for bid in building_ids if bid]
        except (ValueError, TypeError):
            building_id_ints = []

        persons = build_export_queryset(
            building_ids=building_id_ints,
            include_owners=include_owners,
            include_tenants=include_tenants,
            include_others=include_others,
        )

        csv_content = export_persons_to_google_csv(persons)

        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="solomon_contacts.csv"'
        return response
