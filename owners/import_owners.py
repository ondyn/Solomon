"""
Solomon — Import owners from text format.

Parses a text block where each owner entry consists of:
  - Owner line: "LastName FirstName [Title], Address"
  - Unit line: "Jednotka: BUILDING/FLAT\tNumerator/Denominator"

Special cases:
  - "SJ Name1 a Name2" — joint ownership (společné jmění)
    Uses the SJ line as the combined name, leaves address empty.
  - One owner may have multiple "Jednotka:" lines (multiple flats)
  - Two consecutive owners with the same flat → co-owners of that flat
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views import View

from buildings.models import Building
from flats.models import Flat
from owners.models import FlatOwner, Owner

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Parsed data structures
# ---------------------------------------------------------------------------
@dataclass
class ParsedUnit:
    """A flat reference parsed from the text."""

    building_number: int  # e.g. 1937
    flat_number: int  # e.g. 6
    share_numerator: int | None = None
    share_denominator: int | None = None


@dataclass
class ParsedOwner:
    """An owner entry parsed from the text."""

    name: str  # Full name as given (may include titles)
    first_name: str = ""
    last_name: str = ""
    address: str = ""
    units: list[ParsedUnit] = field(default_factory=list)
    is_joint: bool = False  # SJ = společné jmění
    person_type: str = "natural"  # natural or legal


# ---------------------------------------------------------------------------
#  Text parser
# ---------------------------------------------------------------------------
# Regex for "Jednotka: 1937/6\t73/9089" or "Jednotka: 1937/6, 1940/3\t659/27267"
_UNIT_RE = re.compile(
    r"Jednotka:\s*"
    r"([\d/,\s]+?)"  # unit references (may be comma-separated)
    r"(?:\t(\d+)/(\d+))?"  # optional share (tab-separated)
    r"\s*$",
)

# Regex for individual unit reference "1937/6"
_UNIT_REF_RE = re.compile(r"(\d+)/(\d+)")

# Patterns to detect joint ownership
_SJ_PREFIX_RE = re.compile(r"^(?:SJ|MCP)\s+")

# Patterns to detect legal entity
_LEGAL_PATTERNS = [", spol. s r.o.", ", s.r.o.", ", a.s.", "spol. s r.o."]


def parse_owners_text(text: str) -> list[ParsedOwner]:
    """
    Parse the owners text format into a list of ParsedOwner objects.

    The format is:
        OwnerName, Address
        Jednotka: building/flat\tnumerator/denominator

    For joint ownership (SJ):
        SJ Name1 a Name2
        Jednotka: building/flat\tnumerator/denominator
        Name1, Address1
        Name2, Address2

    For co-owners (two owners sharing one flat):
        Owner1, Address1
        Jednotka: flat_ref
        Owner2, Address2
        Jednotka: flat_ref  (same flat, no share = inherits from previous)
    """
    lines = text.strip().split("\n")
    owners: list[ParsedOwner] = []
    current_owner: ParsedOwner | None = None
    pending_sj: ParsedOwner | None = None
    sj_detail_count = 0
    sj_has_address = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        unit_match = _UNIT_RE.match(line)

        if unit_match:
            # This is a "Jednotka:" line
            unit_refs_str = unit_match.group(1)
            share_num_str = unit_match.group(2)
            share_den_str = unit_match.group(3)

            share_num = int(share_num_str) if share_num_str else None
            share_den = int(share_den_str) if share_den_str else None

            # Parse all unit references (may be comma-separated)
            unit_refs = _UNIT_REF_RE.findall(unit_refs_str)
            parsed_units = []
            for building_str, flat_str in unit_refs:
                parsed_units.append(
                    ParsedUnit(
                        building_number=int(building_str),
                        flat_number=int(flat_str),
                        share_numerator=share_num,
                        share_denominator=share_den,
                    )
                )

            if current_owner:
                current_owner.units.extend(parsed_units)
            elif pending_sj:
                pending_sj.units.extend(parsed_units)
                # Single-line SJ (has inline address) → close after Jednotka
                if sj_has_address:
                    owners.append(pending_sj)
                    pending_sj = None
                    sj_has_address = False

        elif _SJ_PREFIX_RE.match(line) or line.startswith("MCP "):
            # Joint ownership header line — e.g. "SJ Brtna Josef Ing. a Brtnová Pavlína Ing."
            # Finish any previous owner
            if current_owner:
                owners.append(current_owner)
                current_owner = None

            # Parse name: remove SJ/MCP prefix
            name = _SJ_PREFIX_RE.sub("", line).strip()
            if line.startswith("MCP "):
                name = line[4:].strip()

            # Try to parse comma-separated (name, address) — SJ header may have inline address
            parts = name.split(",", 1)
            owner_name = parts[0].strip()
            sj_address = parts[1].strip() if len(parts) > 1 else ""
            sj_has_address = bool(sj_address)

            pending_sj = ParsedOwner(
                name=owner_name,
                address=sj_address,
                is_joint=True,
            )
            # Parse combined name into first/last
            _parse_name_into_owner(pending_sj, owner_name)
            sj_detail_count = 0

        else:
            # This is an owner name line (possibly with address)
            if pending_sj is not None:
                # We're reading detail lines after an SJ header
                # These are individual owner details — we skip them (use combined name)
                sj_detail_count += 1

                # Check if next line is a Jednotka line for this detail person
                if i + 1 < len(lines) and _UNIT_RE.match(lines[i + 1].strip()):
                    # Skip — the unit belongs to the SJ owner already
                    pass
                elif sj_detail_count >= 2:
                    # We've seen both SJ detail lines, close the SJ owner
                    owners.append(pending_sj)
                    pending_sj = None
                    sj_detail_count = 0
            else:
                # Regular owner line
                if current_owner:
                    owners.append(current_owner)

                current_owner = _parse_owner_line(line)

        i += 1

    # Don't forget the last owner
    if current_owner:
        owners.append(current_owner)
    if pending_sj:
        owners.append(pending_sj)

    return owners


def _parse_owner_line(line: str) -> ParsedOwner:
    """Parse a single owner line like 'Bartíková Patricie Mgr., Zvěřinova 3446/3, Strašnice, 13000 Praha 3'."""
    # Check for legal entity
    is_legal = any(p in line for p in _LEGAL_PATTERNS)

    if is_legal:
        # Legal entity: name is everything before the legal suffix + the suffix
        for pattern in _LEGAL_PATTERNS:
            idx = line.find(pattern)
            if idx >= 0:
                name_part = line[: idx + len(pattern)].strip()
                rest = line[idx + len(pattern) :].strip()
                address = rest.lstrip(",").strip() if rest else ""
                return ParsedOwner(
                    name=name_part,
                    first_name="",
                    last_name=name_part,
                    address=address,
                    person_type="legal",
                )

    # Natural person: "LastName FirstName [Title], address..."
    # Split on first comma to separate name from address
    parts = line.split(",", 1)
    name_part = parts[0].strip()
    address = parts[1].strip() if len(parts) > 1 else ""

    # If there are more commas in the address, join them back
    # The address may contain district, postal code, city
    # Address = everything after the first comma
    if len(parts) > 1:
        # Re-join the rest as the full address
        address = line[len(parts[0]) + 1 :].strip()

    owner = ParsedOwner(name=name_part, address=address)
    _parse_name_into_owner(owner, name_part)
    return owner


def _parse_name_into_owner(owner: ParsedOwner, name: str) -> None:
    """Parse 'LastName FirstName Title' or 'Name1 a Name2' into first/last name."""
    # Remove common academic titles
    titles = [
        "Mgr.", "Ing.", "Bc.", "Ph.D.", "CSc.", "JUDr.", "MUDr.", "PhDr.",
        "RNDr.", "doc.", "prof.", "DiS.", "MBA", "Dr.",
    ]
    cleaned = name
    for title in titles:
        cleaned = cleaned.replace(title, "").strip()

    # Handle "Name1 a Name2" for SJ
    if " a " in cleaned:
        parts = cleaned.split(" a ", 1)
        # Use combined name: first part's last name + second part
        owner.last_name = cleaned
        owner.first_name = ""
        return

    # Regular: "LastName FirstName [MiddleName]"
    words = cleaned.split()
    if len(words) >= 2:
        owner.last_name = words[0]
        owner.first_name = " ".join(words[1:])
    elif len(words) == 1:
        owner.last_name = words[0]
        owner.first_name = ""
    else:
        owner.last_name = name
        owner.first_name = ""


# ---------------------------------------------------------------------------
#  Import execution
# ---------------------------------------------------------------------------
@dataclass
class ImportResult:
    """Result of an owners import."""

    owners_created: int = 0
    owners_updated: int = 0
    flat_owners_created: int = 0
    flats_not_found: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@transaction.atomic
def execute_owners_import(
    parsed_owners: list[ParsedOwner],
    effective_date: date | None = None,
) -> ImportResult:
    """
    Execute the import of parsed owners into the database.

    For each parsed owner:
    1. Try to find existing owner by last_name + first_name
    2. Create if not found
    3. For each unit reference, find the flat and create FlatOwner
    """
    if effective_date is None:
        effective_date = date.today()

    result = ImportResult()

    for parsed in parsed_owners:
        # Find or create owner
        owner = _find_or_create_owner(parsed, result)
        if not owner:
            continue

        # Create flat ownership links
        for unit in parsed.units:
            flat = _find_flat(unit.building_number, unit.flat_number)
            if not flat:
                ref = f"{unit.building_number}/{unit.flat_number}"
                if ref not in result.flats_not_found:
                    result.flats_not_found.append(ref)
                continue

            # Check if this ownership already exists
            existing = FlatOwner.objects.filter(
                flat=flat,
                owner=owner,
                effective_from=effective_date,
            ).first()

            if existing:
                # Update share if provided
                if unit.share_numerator and unit.share_denominator:
                    existing.share_numerator = unit.share_numerator
                    existing.share_denominator = unit.share_denominator
                    existing.save()
                continue

            FlatOwner.objects.create(
                flat=flat,
                owner=owner,
                share_numerator=unit.share_numerator or 1,
                share_denominator=unit.share_denominator or 1,
                effective_from=effective_date,
            )
            result.flat_owners_created += 1

    return result


def _find_or_create_owner(parsed: ParsedOwner, result: ImportResult) -> Owner | None:
    """Find an existing owner or create a new one."""
    # Try exact match on last_name + first_name
    filters = {"last_name": parsed.last_name}
    if parsed.first_name:
        filters["first_name"] = parsed.first_name

    existing = Owner.objects.filter(**filters).first()
    if existing:
        # Update address if provided and currently empty
        updated = False
        if parsed.address and not existing.permanent_address:
            existing.permanent_address = parsed.address
            updated = True
        if updated:
            existing.save()
            result.owners_updated += 1
        return existing

    # Create new owner
    owner = Owner.objects.create(
        first_name=parsed.first_name,
        last_name=parsed.last_name,
        permanent_address=parsed.address,
        person_type=parsed.person_type,
    )
    result.owners_created += 1
    return owner


def _find_flat(building_number: int, flat_number: int) -> Flat | None:
    """Find a flat by building house_number and flat_number."""
    return Flat.objects.filter(
        building__house_number=str(building_number),
        flat_number=str(flat_number),
    ).first()


# ---------------------------------------------------------------------------
#  Views
# ---------------------------------------------------------------------------
class OwnersImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Import owners from pasted text."""

    permission_required = "owners.add_owner"
    template_name = "owners/owners_import.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"title": _("Import Owners")},
        )

    def post(self, request):
        text = request.POST.get("owners_text", "").strip()
        action = request.POST.get("action", "preview")

        if not text:
            messages.error(request, _("Please paste the owner data."))
            return render(request, self.template_name, {"title": _("Import Owners")})

        parsed = parse_owners_text(text)

        if not parsed:
            messages.error(request, _("No owners could be parsed from the input."))
            return render(
                request,
                self.template_name,
                {"title": _("Import Owners"), "owners_text": text},
            )

        if action == "preview":
            # Show preview
            preview_data = _build_preview(parsed)
            return render(
                request,
                "owners/owners_import_preview.html",
                {
                    "title": _("Import Owners - Preview"),
                    "parsed_owners": parsed,
                    "preview_data": preview_data,
                    "owners_text": text,
                    "total_owners": len(parsed),
                    "total_units": sum(len(p.units) for p in parsed),
                },
            )

        elif action == "execute":
            effective_date_str = request.POST.get("effective_date", "")
            try:
                effective_date = date.fromisoformat(effective_date_str) if effective_date_str else date.today()
            except ValueError:
                effective_date = date.today()

            try:
                result = execute_owners_import(parsed, effective_date)
            except Exception:
                logger.exception("Owner import failed")
                messages.error(request, _("Import failed. Please check the logs."))
                return redirect(reverse("owners:owners-import"))

            # Build success message
            msg_parts = []
            if result.owners_created:
                msg_parts.append(
                    _("%(count)d owner(s) created") % {"count": result.owners_created}
                )
            if result.owners_updated:
                msg_parts.append(
                    _("%(count)d owner(s) updated") % {"count": result.owners_updated}
                )
            if result.flat_owners_created:
                msg_parts.append(
                    _("%(count)d ownership(s) assigned") % {"count": result.flat_owners_created}
                )
            if result.flats_not_found:
                msg_parts.append(
                    _("%(count)d flat(s) not found: %(flats)s")
                    % {
                        "count": len(result.flats_not_found),
                        "flats": ", ".join(result.flats_not_found),
                    }
                )

            if msg_parts:
                messages.success(
                    request,
                    _("Import completed: ") + ", ".join(msg_parts) + ".",
                )
            else:
                messages.info(request, _("Nothing to import."))

            return redirect(reverse("owners:owner-list"))

        return redirect(reverse("owners:owners-import"))


def _build_preview(parsed_owners: list[ParsedOwner]) -> list[dict]:
    """Build preview data for template display."""
    preview = []
    for owner in parsed_owners:
        units_preview = []
        for unit in owner.units:
            flat = _find_flat(unit.building_number, unit.flat_number)
            units_preview.append(
                {
                    "ref": f"{unit.building_number}/{unit.flat_number}",
                    "share": f"{unit.share_numerator}/{unit.share_denominator}"
                    if unit.share_numerator
                    else "—",
                    "flat_found": flat is not None,
                    "flat": flat,
                }
            )

        existing_owner = None
        filters = {"last_name": owner.last_name}
        if owner.first_name:
            filters["first_name"] = owner.first_name
        existing_owner = Owner.objects.filter(**filters).first()

        preview.append(
            {
                "owner": owner,
                "existing": existing_owner,
                "is_new": existing_owner is None,
                "units": units_preview,
            }
        )
    return preview
