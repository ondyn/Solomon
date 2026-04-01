"""
Solomon Property - CUZK import views.

Provides:
  - CUZKImportSearchView   - enter building ID or address (autocomplete)
  - CUZKBuildingAutoView   - JSON autocomplete endpoint (city parts + buildings)
  - CUZKImportPreviewView  - diff table + action selection
  - CUZKImportExecuteView  - execute the confirmed import
  - OwnersImportView       - upload + parse owners.txt, preview, execute
"""

from __future__ import annotations

import datetime
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from netbox.views import generic  # noqa: F401  (kept for future use)

from solomon_property.cuzk.import_building import (
    ACTION_CHOICES,
    ACTION_SKIP,
    build_import_preview,
    deserialize_building,
    deserialize_unit,
    execute_import,
    serialize_building,
    serialize_unit,
)
from solomon_property.cuzk.import_owners import import_owners
from solomon_property.cuzk.owners_parser import parse_owners_txt
from solomon_property.cuzk.service import CUZKApiError, CUZKClient
from solomon_property.models import Building

logger = logging.getLogger(__name__)

# Module-level cache for municipality/city-part lists (they rarely change)
_city_parts_cache: list | None = None
_municipality_cache: list | None = None


# ---------------------------------------------------------------------------
#  Step 1 - Search / enter building ID
# ---------------------------------------------------------------------------
class CUZKImportSearchView(LoginRequiredMixin, View):
    template_name = "solomon_property/cuzk_import_search.html"

    def get(self, request):
        return render(request, self.template_name, {
            "title": _("CUZK Import - Search"),
        })

    def post(self, request):
        building_id_str = request.POST.get("cuzk_building_id", "").strip()

        if not building_id_str:
            messages.error(request, _("Please enter a CUZK building ID."))
            return render(request, self.template_name, {"title": _("CUZK Import - Search")})

        try:
            building_id = int(building_id_str)
        except ValueError:
            messages.error(request, _("Invalid CUZK building ID - must be a number."))
            return render(request, self.template_name, {"title": _("CUZK Import - Search")})

        client = CUZKClient()
        try:
            cuzk_building, cuzk_units = client.get_building_with_units(building_id)
        except CUZKApiError as exc:
            messages.error(request, _("CUZK API error: %(detail)s") % {"detail": exc.detail})
            return render(request, self.template_name, {"title": _("CUZK Import - Search")})

        request.session["cuzk_import"] = {
            "building": serialize_building(cuzk_building),
            "units": [serialize_unit(u) for u in cuzk_units],
        }
        return redirect(reverse("plugins:solomon_property:cuzk-import-preview"))


# ---------------------------------------------------------------------------
#  Autocomplete - search buildings by address via CUZK
# ---------------------------------------------------------------------------
class CUZKAddressSearchView(LoginRequiredMixin, View):
    """POST: search CUZK buildings by city_part_code + house_number. Returns JSON."""

    def post(self, request):
        try:
            city_part_code = int(request.POST.get("city_part_code", ""))
            house_number = int(request.POST.get("house_number", ""))
            building_type = int(request.POST.get("building_type", "1"))
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid parameters"}, status=400)

        client = CUZKClient()
        try:
            results = client.search_building(city_part_code, house_number, building_type)
        except CUZKApiError as exc:
            return JsonResponse({"error": exc.detail}, status=502)

        data = [
            {
                "id": b.id,
                "house_numbers": b.house_numbers,
                "city_part_name": b.city_part_name,
                "municipality_name": b.municipality_name,
                "lv": b.lv.number if b.lv else None,
                "unit_count": len(b.unit_refs),
            }
            for b in results
        ]
        return JsonResponse(data, safe=False)


class CUZKCityPartAutocompleteView(LoginRequiredMixin, View):
    """GET ?q=<text>  - return matching city parts as JSON."""

    def get(self, request):
        global _city_parts_cache, _municipality_cache  # noqa: PLW0603
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse([], safe=False)

        client = CUZKClient()
        try:
            if _city_parts_cache is None:
                # Fetch districts and municipalities first to build lookup maps
                district_map = client.list_districts()  # code -> name
                if _municipality_cache is None:
                    _municipality_cache = client.list_municipalities()
                # municipality code -> (name, district_name)
                muni_info = {
                    m.code: (m.name, district_map.get(m.district_code, ""))
                    for m in _municipality_cache
                }

                # Fetch city parts and enrich with municipality + district names
                raw_parts = client.list_city_parts()
                for p in raw_parts:
                    if p.municipality_code and p.municipality_code in muni_info:
                        muni_name, dist_name = muni_info[p.municipality_code]
                        if not p.municipality_name:
                            p.municipality_name = muni_name
                        p.district_name = dist_name
                _city_parts_cache = raw_parts

            q = query.lower()
            # Match city part name, municipality name, or district name
            results = [
                p for p in _city_parts_cache
                if p.name.lower().startswith(q)
                or p.municipality_name.lower().startswith(q)
                or p.district_name.lower().startswith(q)
            ][:30]
        except CUZKApiError:
            return JsonResponse([], safe=False)

        return JsonResponse([
            {
                "code": p.code,
                "name": p.name,
                "municipality": p.municipality_name,
                "district": p.district_name,
            }
            for p in results
        ], safe=False)


# ---------------------------------------------------------------------------
#  Step 2 - Preview diff
# ---------------------------------------------------------------------------
class CUZKImportPreviewView(LoginRequiredMixin, View):
    template_name = "solomon_property/cuzk_import_preview.html"

    def _get_import_data(self, request):
        """Return (cuzk_building, cuzk_units) from session or None."""
        data = request.session.get("cuzk_import")
        if not data:
            return None, None
        cuzk_building = deserialize_building(data["building"])
        cuzk_units = [deserialize_unit(u) for u in data["units"]]
        return cuzk_building, cuzk_units

    def get(self, request):
        cuzk_building, cuzk_units = self._get_import_data(request)
        if not cuzk_building:
            messages.warning(request, _("No import data found. Please search for a building first."))
            return redirect(reverse("plugins:solomon_property:cuzk-import-search"))

        building_diffs, unit_diffs = build_import_preview(cuzk_building, cuzk_units)

        # Group unit diffs by house number for template rendering
        units_by_hn: dict[int, list] = {}
        for ud in unit_diffs:
            units_by_hn.setdefault(ud.house_number, []).append(ud)

        return render(request, self.template_name, {
            "title": _("CUZK Import - Preview"),
            "cuzk_building": cuzk_building,
            "building_diffs": building_diffs,
            "unit_diffs": unit_diffs,
            "units_by_hn": units_by_hn,
            "action_choices": ACTION_CHOICES,
        })

    def post(self, request):
        cuzk_building, cuzk_units = self._get_import_data(request)
        if not cuzk_building:
            messages.error(request, _("Session expired. Please start again."))
            return redirect(reverse("plugins:solomon_property:cuzk-import-search"))

        building_diffs, unit_diffs = build_import_preview(cuzk_building, cuzk_units)

        building_actions = {
            bdiff.house_number: request.POST.get(f"building_action_{bdiff.house_number}", ACTION_SKIP)
            for bdiff in building_diffs
        }
        unit_actions = {
            udiff.cuzk_unit.id: request.POST.get(f"unit_action_{udiff.cuzk_unit.id}", ACTION_SKIP)
            for udiff in unit_diffs
        }

        try:
            stats = execute_import(building_diffs, building_actions, unit_diffs, unit_actions)
        except Exception:
            logger.exception("CUZK building import failed")
            messages.error(request, _("Import failed. Please check the logs."))
            return redirect(reverse("plugins:solomon_property:cuzk-import-search"))

        del request.session["cuzk_import"]

        parts = []
        if stats["buildings_created"]:
            parts.append(_("%(n)d building(s) created") % {"n": stats["buildings_created"]})
        if stats["buildings_updated"]:
            parts.append(_("%(n)d building(s) updated") % {"n": stats["buildings_updated"]})
        if stats["flats_created"]:
            parts.append(_("%(n)d flat(s) created") % {"n": stats["flats_created"]})
        if stats["flats_updated"]:
            parts.append(_("%(n)d flat(s) updated") % {"n": stats["flats_updated"]})
        if stats["skipped"]:
            parts.append(_("%(n)d skipped") % {"n": stats["skipped"]})

        messages.success(request, _("Import complete: ") + ", ".join(parts) + ".")
        return redirect(reverse("plugins:solomon_property:building_list"))


# ---------------------------------------------------------------------------
#  Owners.txt import
# ---------------------------------------------------------------------------
class OwnersImportView(LoginRequiredMixin, View):
    template_name = "solomon_property/owners_import.html"

    def get(self, request):
        # If there's parsed data in session, show preview
        parsed = request.session.get("owners_import_parsed")
        if parsed:
            records = parse_owners_txt(parsed["text"])
            return render(request, self.template_name, {
                "title": _("Import Owners from Text"),
                "records": records,
                "raw_text": parsed["text"],
                "preview": True,
                "effective_from": parsed.get("effective_from", ""),
            })
        return render(request, self.template_name, {
            "title": _("Import Owners from Text"),
            "preview": False,
        })

    def post(self, request):
        action = request.POST.get("action", "preview")

        if action == "preview":
            raw_text = request.POST.get("owners_text", "").strip()
            effective_from_str = request.POST.get("effective_from", "").strip()
            if not raw_text:
                messages.error(request, _("Please paste the owners text."))
                return render(request, self.template_name, {
                    "title": _("Import Owners from Text"),
                    "preview": False,
                })
            request.session["owners_import_parsed"] = {
                "text": raw_text,
                "effective_from": effective_from_str,
            }
            return redirect(reverse("plugins:solomon_property:owners-import"))

        elif action == "import":
            parsed = request.session.get("owners_import_parsed")
            if not parsed:
                messages.error(request, _("Session expired. Please paste the text again."))
                return redirect(reverse("plugins:solomon_property:owners-import"))

            effective_from_str = parsed.get("effective_from", "")
            try:
                effective_from = datetime.date.fromisoformat(effective_from_str) if effective_from_str else None
            except ValueError:
                effective_from = None

            records = parse_owners_txt(parsed["text"])
            results = import_owners(records, effective_from=effective_from)

            del request.session["owners_import_parsed"]

            errors = [r for r in results if r.error]
            owners_created = sum(1 for r in results if r.owner and not r.error)
            persons_created = sum(len(r.persons_created) for r in results)
            flat_owners_created = sum(len(r.flat_owners) for r in results)

            if errors:
                for r in errors:
                    messages.warning(request, _("%(name)s: %(err)s") % {
                        "name": r.record.display_name, "err": r.error
                    })
            messages.success(request, _(
                "Import complete: %(o)d owner(s), %(p)d person(s), %(fo)d flat ownership(s)."
            ) % {"o": owners_created, "p": persons_created, "fo": flat_owners_created})

            return redirect(reverse("plugins:solomon_property:propertyowner_list"))

        elif action == "cancel":
            request.session.pop("owners_import_parsed", None)
            return redirect(reverse("plugins:solomon_property:owners-import"))

        return redirect(reverse("plugins:solomon_property:owners-import"))


# ---------------------------------------------------------------------------
#  Flat area auto-calculation
# ---------------------------------------------------------------------------
class FlatAreaCalculationView(LoginRequiredMixin, View):
    """
    Preview page showing calculated area for every flat that has CUZK share data.

    Calculation:
      max_denominator = largest cuzk_share_denominator across all flats
      area = round(max_denominator / denominator * numerator * 10) / 10
    """

    template_name = "solomon_property/flat_area_calculation.html"

    def _build_preview(self):
        """Return (max_denominator, rows) where rows is a list of dicts."""
        from .models import Flat

        flats = Flat.objects.filter(
            cuzk_share_numerator__isnull=False,
            cuzk_share_denominator__isnull=False,
            cuzk_share_denominator__gt=0,
        ).select_related("building").order_by("building__name", "flat_number")

        if not flats.exists():
            return None, []

        max_denominator = max(f.cuzk_share_denominator for f in flats)

        rows = []
        for flat in flats:
            calculated = max_denominator / flat.cuzk_share_denominator * flat.cuzk_share_numerator / 10
            rows.append({
                "flat": flat,
                "share": flat.cuzk_share,
                "calculated_area": calculated,
                "current_area": flat.area_m2,
                "will_change": flat.area_m2 is None or float(flat.area_m2) != calculated,
            })

        return max_denominator, rows

    def get(self, request):
        max_denominator, rows = self._build_preview()
        return render(request, self.template_name, {
            "title": _("Calculate Flat Areas"),
            "max_denominator": max_denominator,
            "rows": rows,
        })

    def post(self, request):
        if request.POST.get("action") != "apply":
            return redirect(reverse("plugins:solomon_property:flat-area-calculation"))

        max_denominator, rows = self._build_preview()
        if not rows:
            messages.warning(request, _("No flats with CUZK share data found."))
            return redirect(reverse("plugins:solomon_property:flat-area-calculation"))

        updated = 0
        for row in rows:
            if row["will_change"]:
                flat = row["flat"]
                # snapshot() captures pre-change state so NetBox's signal handler can
                # create a proper ObjectChange record (pre- and post-change diff).
                flat.snapshot()
                flat.area_m2 = row["calculated_area"]
                flat.save()
                updated += 1

        messages.success(
            request,
            _("Area updated for %(n)d flat(s).") % {"n": updated},
        )
        return redirect(reverse("plugins:solomon_property:flat_list"))
