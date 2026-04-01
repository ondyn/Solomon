"""
Solomon - owners.txt import execution.

Takes ParsedOwnerRecord list and creates/updates PropertyOwner, Person, FlatOwner records.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass

from django.db import transaction

from solomon_property.models import Building, Flat, FlatOwner, Person, PropertyOwner

from .owners_parser import ParsedOwnerRecord, ParsedPerson

logger = logging.getLogger(__name__)


@dataclass
class OwnerImportResult:
    record: ParsedOwnerRecord
    owner: PropertyOwner | None = None
    flat_owners: list[FlatOwner] = None  # type: ignore[assignment]
    persons_created: list[Person] = None  # type: ignore[assignment]
    error: str = ""

    def __post_init__(self):
        if self.flat_owners is None:
            self.flat_owners = []
        if self.persons_created is None:
            self.persons_created = []


def _get_or_create_person(pp: ParsedPerson, fallback_address: str = "") -> tuple[Person, bool]:
    """
    Find existing Person by name or create new one.

    `fallback_address` is used when the parsed person has no individual address
    (e.g. SJM spouses sharing the owner record address).
    For existing persons, the address is updated if it was previously empty.
    """
    address = pp.address or fallback_address

    # Try exact match first
    existing = Person.objects.filter(
        first_name=pp.first_name,
        last_name=pp.last_name,
    ).first()
    if existing:
        # Fill in address if the stored one is empty and we now have one
        if not existing.permanent_address and address:
            existing.permanent_address = address
            existing.save(update_fields=["permanent_address"])
        return existing, False

    p = Person.objects.create(
        first_name=pp.first_name,
        last_name=pp.last_name,
        title_before=pp.title_before,
        title_after=pp.title_after,
        permanent_address=address,
    )
    return p, True


def _find_flat(flat_number_str: str) -> Flat | None:
    """
    Find a Flat by flat_number string like "1937/6".

    house_number = "1937", flat_number = "6" in DB is stored as flat_number = "6"
    within a Building with house_number = "1937".
    """
    parts = flat_number_str.split("/")
    if len(parts) != 2:
        return None
    house_num, flat_num = parts[0].strip(), parts[1].strip()
    return Flat.objects.filter(
        building__house_number=house_num,
        flat_number=flat_num,
    ).first()


@transaction.atomic
def import_owners(
    records: list[ParsedOwnerRecord],
    effective_from: datetime.date | None = None,
) -> list[OwnerImportResult]:
    """
    Import a list of ParsedOwnerRecord into the database.

    - Creates or updates PropertyOwner records (matched by display_name).
    - Creates Person records for each person in the owner.
    - Creates FlatOwner records linking owners to their flats.

    Returns a list of OwnerImportResult with per-record outcome.
    """
    if effective_from is None:
        effective_from = datetime.date.today()

    results: list[OwnerImportResult] = []

    for rec in records:
        result = OwnerImportResult(record=rec)
        try:
            # Find or create PropertyOwner
            owner = PropertyOwner.objects.filter(display_name=rec.display_name).first()
            if not owner:
                owner = PropertyOwner.objects.create(
                    display_name=rec.display_name,
                    person_type=rec.person_type,
                    permanent_address=rec.address,
                )

            result.owner = owner

            # Create/link Persons
            for pp in rec.persons:
                if not pp.last_name:
                    continue
                person, created = _get_or_create_person(pp, fallback_address=rec.address)
                owner.persons.add(person)
                if created:
                    result.persons_created.append(person)

            # Link to flats via FlatOwner
            for flat_num_str in rec.flat_numbers:
                flat = _find_flat(flat_num_str)
                if not flat:
                    logger.warning("Flat not found for %s (owner: %s)", flat_num_str, rec.display_name)
                    continue

                # Check if FlatOwner already exists for this flat+owner+date
                existing_fo = FlatOwner.objects.filter(
                    flat=flat,
                    owner=owner,
                    effective_from=effective_from,
                ).first()
                if existing_fo:
                    result.flat_owners.append(existing_fo)
                    continue

                fo = FlatOwner.objects.create(
                    flat=flat,
                    owner=owner,
                    share_numerator=rec.share_numerator or 1,
                    share_denominator=rec.share_denominator or 1,
                    effective_from=effective_from,
                )
                result.flat_owners.append(fo)

        except Exception as exc:
            logger.exception("Error importing owner record %s", rec.display_name)
            result.error = str(exc)

        results.append(result)

    return results
