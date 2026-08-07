"""
Solomon Property - Google Contacts CSV parser.

Parses a Google Contacts CSV export and matches rows against existing Person
records by first_name + last_name.  Produces a list of ContactRow objects
describing what data can be imported (emails, phones, addresses, birthday).
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from solomon_property.models import Person


# ---------------------------------------------------------------------------
#  Data classes
# ---------------------------------------------------------------------------


@dataclass
class ContactRow:
    """One row from the Google CSV after parsing."""

    row_number: int
    first_name: str
    last_name: str
    title_before: str = ""
    title_after: str = ""
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    address: str = ""
    birthday: str = ""
    organization: str = ""
    notes: str = ""
    # Index in the full parsed list (used for form field names)
    list_index: int = 0
    # Matching
    matched_person: Optional[Person] = None
    match_status: str = "unmatched"  # matched / ambiguous / unmatched / new
    match_note: str = ""  # human-readable explanation of how the match was made
    candidates: list[Person] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        parts = []
        if self.title_before:
            parts.append(self.title_before)
        parts.append(self.first_name)
        parts.append(self.last_name)
        if self.title_after:
            parts.append(self.title_after)
        return " ".join(parts)

    @property
    def has_useful_data(self) -> bool:
        """True if this row has at least one email or phone to import."""
        return bool(self.emails or self.phones)


# ---------------------------------------------------------------------------
#  Czech title detection
# ---------------------------------------------------------------------------

_TITLES_BEFORE = {
    "ing.",
    "mgr.",
    "mudr.",
    "judr.",
    "rndr.",
    "phdr.",
    "paeddr.",
    "mvdr.",
    "bc.",
    "doc.",
    "prof.",
    "thdr.",
    "thlic.",
    "ing.arch.",
    "akad.mal.",
    "akad.soch.",
}

_TITLES_AFTER = {
    "ph.d.",
    "csc.",
    "drsc.",
    "mba",
    "dis.",
    "bca.",
    "th.d.",
    "phd.",
}


def _strip_czech_title(name: str) -> tuple[str, str, str]:
    """
    Extract Czech academic titles from a name string.

    Returns (title_before, clean_name, title_after).
    """
    title_before_parts = []
    title_after_parts = []
    words = name.split()
    clean = []

    for w in words:
        wl = w.lower().rstrip(",")
        if wl in _TITLES_BEFORE:
            title_before_parts.append(w.rstrip(","))
        elif wl in _TITLES_AFTER:
            title_after_parts.append(w.rstrip(","))
        else:
            clean.append(w)

    return (
        " ".join(title_before_parts),
        " ".join(clean),
        " ".join(title_after_parts),
    )


# ---------------------------------------------------------------------------
#  Phone normalization
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r"[^\d+]")


def _normalize_phone(raw: str) -> str:
    """Strip whitespace/dashes, keep digits and leading +."""
    raw = raw.strip()
    if not raw:
        return ""
    # Keep the leading + if present
    if raw.startswith("+"):
        return "+" + _PHONE_RE.sub("", raw[1:])
    return _PHONE_RE.sub("", raw)


# ---------------------------------------------------------------------------
#  CSV parsing
# ---------------------------------------------------------------------------


def parse_google_csv(csv_text: str) -> list[ContactRow]:
    """
    Parse Google Contacts CSV text and return ContactRow objects.

    Only rows with a non-empty First Name or Last Name are kept.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    rows: list[ContactRow] = []

    for idx, raw in enumerate(reader, start=2):  # row 1 is header
        first = raw.get("First Name", "").strip()
        last = raw.get("Last Name", "").strip()

        if not first and not last:
            continue

        # Collect emails (up to 3 in standard Google export)
        emails = []
        for i in range(1, 4):
            val = raw.get(f"E-mail {i} - Value", "").strip()
            if val:
                emails.append(val)

        # Collect phones (up to 3 in standard Google export)
        phones = []
        for i in range(1, 4):
            val = raw.get(f"Phone {i} - Value", "").strip()
            for phone in val.split(":::"):
                norm = _normalize_phone(phone)
                if norm:
                    phones.append(norm)

        # Address - use formatted if available, else build from parts
        address = raw.get("Address 1 - Formatted", "").strip()
        if not address:
            parts = []
            for key in (
                "Address 1 - Street",
                "Address 1 - City",
                "Address 1 - Postal Code",
                "Address 1 - Country",
            ):
                v = raw.get(key, "").strip()
                if v:
                    parts.append(v)
            address = ", ".join(parts)

        birthday = raw.get("Birthday", "").strip()
        organization = raw.get("Organization Name", "").strip()
        notes = raw.get("Notes", "").strip()

        # Try to extract Czech titles from the name parts
        title_before = raw.get("Name Prefix", "").strip()
        title_after = raw.get("Name Suffix", "").strip()

        # If no prefix/suffix from explicit fields, try to detect from name
        if not title_before and not title_after:
            full = f"{first} {last}".strip()
            tb, clean, ta = _strip_czech_title(full)
            if tb or ta:
                title_before = tb
                title_after = ta
                # Re-split the clean name
                parts = clean.split(None, 1)
                if len(parts) == 2:
                    first, last = parts
                elif parts:
                    # Single word - keep as last name
                    last = parts[0]
                    first = ""

        rows.append(
            ContactRow(
                row_number=idx,
                list_index=len(rows),
                first_name=first,
                last_name=last,
                title_before=title_before,
                title_after=title_after,
                emails=emails,
                phones=phones,
                address=address,
                birthday=birthday,
                organization=organization,
                notes=notes,
            )
        )

    return rows


# ---------------------------------------------------------------------------
#  Fuzzy name matching helpers
# ---------------------------------------------------------------------------


def _strip_diacritics(s: str) -> str:
    """Remove diacritical marks: 'Jiří' -> 'Jiri', 'Čermáková' -> 'Cermakova'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    ).lower()


# Czech diminutive / informal -> canonical first name mapping
# Key is the stripped (no diacritics, lowercase) informal form.
_DIMINUTIVES: dict[str, set[str]] = {
    # -ka / -ek forms
    "jirka": {"jiri"},
    "jiri": {"jiri", "jirka"},
    "pepa": {"josef"},
    "pepik": {"josef"},
    "ferda": {"ferdinand"},
    "tonda": {"antonin"},
    "tonik": {"antonin"},
    "mirek": {"miroslav"},
    "milos": {"milos", "miloslav"},
    "radek": {"radoslav", "radek"},
    "lada": {"ladislav"},
    "franta": {"frantisek"},
    "fanda": {"frantisek"},
    "zdenek": {"zdenek", "zdenko"},
    "ales": {"ales", "alois"},
    "honza": {"jan"},
    "janek": {"jan"},
    "jenda": {"jan"},
    "jan": {"jan", "honza"},
    "karlik": {"karel"},
    "karol": {"karel"},
    "vojta": {"vojtech"},
    "marek": {"marek"},
    "ondra": {"ondrej"},
    "venda": {"vaclav"},
    "vasek": {"vaclav"},
    # Female
    "lenka": {"lenka", "lena"},
    "hanka": {"hana"},
    "anka": {"anna", "anezka"},
    "anicka": {"anna"},
    "katka": {"katerina"},
    "kaca": {"katerina"},
    "ivka": {"ivana", "iva"},
    "pavla": {"pavla"},
    "pavlina": {"pavlina"},
    "marketa": {"marketa"},
    "petra": {"petra"},
    "lucie": {"lucie"},
    "lucka": {"lucie"},
    "alena": {"alena"},
    "alenka": {"alena"},
    "milena": {"milena"},
    "milka": {"miloslava", "milena"},
    "jarka": {"jaroslava", "jarka"},
    "sarka": {"sarka"},
    "zuzka": {"zuzana"},
    "zuza": {"zuzana"},
    "evka": {"eva"},
    "vera": {"vera"},
    "verka": {"vera"},
    "bozena": {"bozena"},
    "boza": {"bozena"},
    "olga": {"olga"},
    "olgicka": {"olga"},
    "dagmar": {"dagmar"},
    "dasa": {"dagmar"},
    "blanka": {"blanka"},
    "renata": {"renata"},
    "renka": {"renata"},
    "libuska": {"libuse"},
    "libuse": {"libuse"},
    "vladka": {"vladimira"},
    "vlad": {"vladislav", "vladimir"},
    "vlada": {"vladislav", "vladimira"},
    "stanislava": {"stanislava"},
    "stana": {"stanislava", "stanislav"},
    "stanicka": {"stanislava"},
    "bohumila": {"bohumila"},
    "mila": {"bohumila", "miloslava", "ludmila"},
    "ludmila": {"ludmila"},
    "miluska": {"miluse", "miloslava"},
}


def _first_name_matches(csv_first: str, db_first: str) -> bool:
    """
    Return True if the CSV first name plausibly matches the DB first name.

    Strategy:
    1. Exact match (after stripping diacritics, lowercasing)
    2. csv_first is a diminutive/informal form that maps to db_first
    3. db_first is a diminutive/informal form that maps to csv_first
    """
    csv_norm = _strip_diacritics(csv_first)
    db_norm = _strip_diacritics(db_first)

    # 1. Exact
    if csv_norm == db_norm:
        return True

    # 2. csv is informal -> canonical set includes db_norm
    for canonical in _DIMINUTIVES.get(csv_norm, set()):
        if canonical == db_norm:
            return True

    # 3. db is informal -> canonical set includes csv_norm
    for canonical in _DIMINUTIVES.get(db_norm, set()):
        if canonical == csv_norm:
            return True

    return False


def _last_name_matches(csv_last: str, db_last: str) -> bool:
    """Exact last name match after stripping diacritics."""
    return _strip_diacritics(csv_last) == _strip_diacritics(db_last)


def _last_name_variants(raw_last: str) -> list[str]:
    """
    Return plausible surname variants from a Google CSV last-name field.

    Some exported contacts use the last-name column to store extra apartment or
    role notes, for example "Pejsar 1939 byt 4 3+1". In those cases the first
    token is still the real surname, so we keep both the full string and that
    leading token as match candidates.

    We only fall back to the first token after trying the full field, so
    appended notes do not block a match but genuine multi-word surnames still
    get the first chance to match exactly.
    """
    cleaned = raw_last.strip()
    if not cleaned:
        return []

    variants = [cleaned]
    words = cleaned.split()
    if len(words) > 1:
        variants.append(words[0])

    return variants


def _extract_first_word(name: str) -> str:
    """Return the first whitespace-delimited word of a name string."""
    parts = name.strip().split()
    return parts[0] if parts else ""


# ---------------------------------------------------------------------------
#  Person matching
# ---------------------------------------------------------------------------


def match_contacts_to_persons(rows: list[ContactRow]) -> list[ContactRow]:
    """
    For each ContactRow, try to find a matching Person in the database.

    Matching is done in two passes, most specific first:

    Pass 1 - exact (diacritic-stripped) first + last name:
      - Uses exact iexact DB query, falls back to normalised comparison.

    Pass 2 - fuzzy first name:
      - Candidate pool = all Persons with matching last name (diacritic-stripped).
      - For each candidate check _first_name_matches(), which handles:
          * diminutives / informal forms (Jirka -> Jiri)
          * csv first name may be multi-word ("Alena BD Salounova") - we try
            EACH word of the csv first name field against the db first name.

    Sets match_status to:
      - "matched"   - exactly one Person found
      - "ambiguous"  - multiple Persons found (shown to user for manual pick)
      - "unmatched"  - no Person found
    """
    # Pre-load all persons once to avoid N+1 queries
    all_persons: list[Person] = list(Person.objects.all())

    # Build lookup: stripped_last_name -> list of persons
    last_name_index: dict[str, list[Person]] = {}
    for p in all_persons:
        key = _strip_diacritics(p.last_name)
        last_name_index.setdefault(key, []).append(p)

    for row in rows:
        if not row.first_name and not row.last_name:
            row.match_status = "unmatched"
            continue

        csv_last_variants = _last_name_variants(row.last_name)

        # Persons with a matching last name, including rows where Google CSV
        # stored flat metadata after the real surname.
        last_candidates: list[Person] = []
        seen_last_candidate_pks: set[int] = set()
        for csv_last in csv_last_variants:
            csv_last_norm = _strip_diacritics(csv_last)
            for person in last_name_index.get(csv_last_norm, []):
                if person.pk in seen_last_candidate_pks:
                    continue
                seen_last_candidate_pks.add(person.pk)
                last_candidates.append(person)

        if not last_candidates:
            row.match_status = "unmatched"
            continue

        # Pass 1: exact first name match
        exact = [
            p
            for p in last_candidates
            if _strip_diacritics(p.first_name) == _strip_diacritics(row.first_name)
        ]
        if len(exact) == 1:
            row.matched_person = exact[0]
            row.match_status = "matched"
            row.match_note = "exact"
            row.candidates = exact
            continue
        if len(exact) > 1:
            row.match_status = "ambiguous"
            row.candidates = exact
            row.match_note = "exact-ambiguous"
            continue

        # Pass 2: fuzzy first name - try each word from csv first_name field
        csv_first_words = row.first_name.strip().split()
        fuzzy_matches: set[int] = set()  # person pks
        matched_persons: list[Person] = []

        for p in last_candidates:
            for word in csv_first_words:
                if _first_name_matches(word, p.first_name):
                    if p.pk not in fuzzy_matches:
                        fuzzy_matches.add(p.pk)
                        matched_persons.append(p)
                    break

        if len(matched_persons) == 1:
            row.matched_person = matched_persons[0]
            row.match_status = "matched"
            row.match_note = "fuzzy"
            row.candidates = matched_persons
        elif len(matched_persons) > 1:
            row.match_status = "ambiguous"
            row.candidates = matched_persons
            row.match_note = "fuzzy-ambiguous"
        else:
            row.match_status = "unmatched"

    return rows


# ---------------------------------------------------------------------------
#  Import execution
# ---------------------------------------------------------------------------


@dataclass
class ContactImportResult:
    """Result of importing one contact row."""

    row: ContactRow
    person: Optional[Person] = None
    emails_added: int = 0
    phones_added: int = 0
    error: str = ""


def execute_contacts_import(
    rows: list[ContactRow],
    selected_indices: set[int],
    person_overrides: dict[int, int],
    merge_mode: str = "append",
) -> list[ContactImportResult]:
    """
    Import contact data into Person records.

    Args:
        rows: Parsed ContactRow list (full list, not just preview subset)
        selected_indices: Set of list_index values that user selected
        person_overrides: Map of list_index -> person_pk for ambiguous matches
            where user picked a specific person
        merge_mode: "append" adds new emails/phones, "replace" overwrites
    """
    results = []

    for row in rows:
        idx = row.list_index
        if idx not in selected_indices:
            continue

        person = row.matched_person
        if person is None and idx in person_overrides:
            try:
                person = Person.objects.get(pk=person_overrides[idx])
            except Person.DoesNotExist:
                results.append(
                    ContactImportResult(row=row, error="Selected person not found")
                )
                continue

        if person is None:
            results.append(ContactImportResult(row=row, error="No matching person"))
            continue

        result = ContactImportResult(row=row, person=person)

        # Merge emails
        if merge_mode == "replace":
            if row.emails:
                person.emails = row.emails
                result.emails_added = len(row.emails)
        else:  # append
            existing = set(e.lower() for e in person.emails)
            for email in row.emails:
                if email.lower() not in existing:
                    person.emails.append(email)
                    existing.add(email.lower())
                    result.emails_added += 1

        # Merge phones
        if merge_mode == "replace":
            if row.phones:
                person.phones = row.phones
                result.phones_added = len(row.phones)
        else:  # append
            existing = set(person.phones)
            for phone in row.phones:
                if phone not in existing:
                    person.phones.append(phone)
                    existing.add(phone)
                    result.phones_added += 1

        if result.emails_added or result.phones_added:
            person.save()

        results.append(result)

    return results


# ---------------------------------------------------------------------------
#  Export to Google Contacts CSV
# ---------------------------------------------------------------------------


def _build_person_role_notes(person) -> str:
    """
    Build a role description string for a person, listing all their
    ownership and tenancy records (building + flat number).

    Returns an empty string if the person has no roles.
    """
    parts = []

    # Ownerships: person -> PropertyOwner -> FlatOwner -> Flat -> Building
    for ownership in person.ownerships.prefetch_related(
        "flat_owners__flat__building"
    ).all():
        for flat_owner in ownership.flat_owners.all():
            flat = flat_owner.flat
            building = flat.building
            status = "" if flat_owner.is_current else " (former)"
            parts.append(f"Owner: {building.name}, flat {flat.flat_number}{status}")

    # Tenancies: person -> PropertyTenant -> Flat -> Building
    for tenancy in person.tenancies.select_related("flat__building").all():
        flat = tenancy.flat
        building = flat.building
        status = "" if tenancy.is_current else " (former)"
        parts.append(f"Tenant: {building.name}, flat {flat.flat_number}{status}")

    return "; ".join(parts)


def export_persons_to_google_csv(persons) -> str:
    """
    Export a queryset (or iterable) of Person objects to Google Contacts CSV format.
    Ownership and tenancy info is appended to the Notes field.
    Returns the CSV as a string.
    """
    output = io.StringIO()
    fieldnames = [
        "First Name",
        "Middle Name",
        "Last Name",
        "Phonetic First Name",
        "Phonetic Middle Name",
        "Phonetic Last Name",
        "Name Prefix",
        "Name Suffix",
        "Nickname",
        "File As",
        "Organization Name",
        "Organization Title",
        "Organization Department",
        "Birthday",
        "Notes",
        "Photo",
        "Labels",
        "E-mail 1 - Label",
        "E-mail 1 - Value",
        "E-mail 2 - Label",
        "E-mail 2 - Value",
        "E-mail 3 - Label",
        "E-mail 3 - Value",
        "Phone 1 - Label",
        "Phone 1 - Value",
        "Phone 2 - Label",
        "Phone 2 - Value",
        "Phone 3 - Label",
        "Phone 3 - Value",
        "Address 1 - Label",
        "Address 1 - Formatted",
        "Address 1 - Street",
        "Address 1 - City",
        "Address 1 - PO Box",
        "Address 1 - Region",
        "Address 1 - Postal Code",
        "Address 1 - Country",
        "Address 1 - Extended Address",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for person in persons:
        row = {f: "" for f in fieldnames}
        row["First Name"] = person.first_name
        row["Last Name"] = person.last_name
        row["Name Prefix"] = person.title_before
        row["Name Suffix"] = person.title_after
        row["Labels"] = "* myContacts"

        # Emails (up to 3)
        for i, email in enumerate(person.emails[:3], start=1):
            row[f"E-mail {i} - Label"] = "* Other"
            row[f"E-mail {i} - Value"] = email

        # Phones (up to 3)
        for i, phone in enumerate(person.phones[:3], start=1):
            row[f"Phone {i} - Label"] = "Mobile"
            row[f"Phone {i} - Value"] = phone

        # Address
        if person.permanent_address:
            row["Address 1 - Label"] = "Home"
            row["Address 1 - Formatted"] = person.permanent_address

        if person.date_of_birth:
            row["Birthday"] = person.date_of_birth.strftime("%Y-%m-%d")

        # Notes: combine personal note with role description
        role_notes = _build_person_role_notes(person)
        note_parts = []
        if person.note:
            note_parts.append(person.note)
        if role_notes:
            note_parts.append(role_notes)
        if note_parts:
            row["Notes"] = " | ".join(note_parts)

        writer.writerow(row)

    return output.getvalue()


# ---------------------------------------------------------------------------
#  Export queryset builder
# ---------------------------------------------------------------------------


def build_export_queryset(
    building_ids, include_owners, include_tenants, include_others
):
    """
    Build a deduplicated Person queryset for the CSV export based on filter params.

    Args:
        building_ids: list of Building PKs to filter by (empty = all buildings)
        include_owners: bool - include persons linked via PropertyOwner/FlatOwner
        include_tenants: bool - include persons linked via PropertyTenant
        include_others: bool - include persons with no ownership or tenancy (global)

    Returns an ordered queryset of distinct Person objects.
    """
    from django.db.models import Q, Exists, OuterRef
    from solomon_property.models import Person, PropertyTenant, PropertyOwner

    # Building-scoped sub-queries (used for owners/tenants when building filter active)
    owner_qs = PropertyOwner.objects.filter(
        persons=OuterRef("pk"),
        flat_owners__isnull=False,
    )
    tenant_qs = PropertyTenant.objects.filter(person=OuterRef("pk"))

    if building_ids:
        owner_qs = owner_qs.filter(flat_owners__flat__building__in=building_ids)
        tenant_qs = tenant_qs.filter(flat__building__in=building_ids)

    has_ownership = Exists(owner_qs.values("pk"))
    has_tenancy = Exists(tenant_qs.values("pk"))

    # Global sub-queries (used for "others" - persons with no role at all)
    global_owner_qs = PropertyOwner.objects.filter(
        persons=OuterRef("pk"),
        flat_owners__isnull=False,
    )
    global_tenant_qs = PropertyTenant.objects.filter(person=OuterRef("pk"))
    has_any_ownership = Exists(global_owner_qs.values("pk"))
    has_any_tenancy = Exists(global_tenant_qs.values("pk"))

    conditions = Q(pk=None)  # start with empty set
    if include_owners:
        conditions |= Q(has_ownership=True)
    if include_tenants:
        conditions |= Q(has_tenancy=True)
    if include_others:
        conditions |= Q(has_any_ownership=False, has_any_tenancy=False)

    persons = (
        Person.objects.annotate(
            has_ownership=has_ownership,
            has_tenancy=has_tenancy,
            has_any_ownership=has_any_ownership,
            has_any_tenancy=has_any_tenancy,
        )
        .filter(conditions)
        .order_by("last_name", "first_name")
        .distinct()
    )
    return persons
