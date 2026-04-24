"""
Solomon Property - Models

Hierarchy:
  Building → Flat → FlatOwner ← Owner → Person(s)
                 → Tenant → Person

Design notes:
  - Person is a universal contact data store (reusable across roles).
  - Owner is the legal ownership entity (natural/legal/SJM).
    One Owner can have multiple Persons (e.g. SJM husband + wife).
  - FlatOwner is the M:N junction: flat ↔ owner with share + effective dates.
  - Tenant links directly to a Person record and a Flat.
  - All models use NetBoxModel (UUID pk, timestamps, audit log, journaling).
"""

from decimal import Decimal
from fractions import Fraction

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import NetBoxModel


# ---------------------------------------------------------------------------
#  Building
# ---------------------------------------------------------------------------

class Building(NetBoxModel):
    """An apartment building managed under the SVJ."""

    name = models.CharField(
        max_length=200,
        verbose_name=_("Name"),
        help_text=_("Descriptive name, e.g. 'Šalounova 1937'"),
    )
    street = models.CharField(max_length=200, verbose_name=_("Street"))
    house_number = models.CharField(
        max_length=20,
        verbose_name=_("House number"),
        help_text=_("Číslo popisné"),
    )
    city = models.CharField(max_length=100, verbose_name=_("City"), default="Praha")
    postal_code = models.CharField(max_length=10, verbose_name=_("Postal code"), default="14900")
    number_of_floors = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Number of floors")
    )
    elevator = models.BooleanField(default=False, verbose_name=_("Elevator"))
    year_built = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Year built")
    )
    total_units = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Total units")
    )
    land_plot_number = models.CharField(
        max_length=50, blank=True, verbose_name=_("Land plot number"),
        help_text=_("Číslo parcely")
    )
    common_rooms = models.TextField(blank=True, verbose_name=_("Common rooms"))
    floor_plan_url = models.URLField(blank=True, verbose_name=_("Floor plan URL"))
    common_area_rental = models.TextField(
        blank=True, verbose_name=_("Common area rental info")
    )
    note = models.TextField(blank=True, verbose_name=_("Note"))

    # CUZK integration fields
    cuzk_building_id = models.BigIntegerField(
        null=True, blank=True, verbose_name=_("CUZK building ID"),
        help_text=_("ID stavby z ČÚZK katastru"),
        db_index=True,
    )
    cuzk_lv_number = models.IntegerField(
        null=True, blank=True, verbose_name=_("CUZK LV number"),
        help_text=_("Číslo listu vlastnictví"),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Building")
        verbose_name_plural = _("Buildings")

    def __str__(self):
        return f"{self.name} ({self.street} {self.house_number})"

    def get_absolute_url(self):
        return reverse("plugins:solomon_property:building", kwargs={"pk": self.pk})


# ---------------------------------------------------------------------------
#  Flat
# ---------------------------------------------------------------------------

DISPOSITION_CHOICES = [
    ("1+kk", "1+kk"),
    ("1+1", "1+1"),
    ("2+kk", "2+kk"),
    ("2+1", "2+1"),
    ("3+kk", "3+kk"),
    ("3+1", "3+1"),
    ("4+kk", "4+kk"),
    ("4+1", "4+1"),
    ("5+kk", "5+kk"),
    ("5+1", "5+1"),
    ("other", _("Other")),
]


class Flat(NetBoxModel):
    """A flat (apartment unit) belonging to a building."""

    building = models.ForeignKey(
        Building,
        on_delete=models.PROTECT,
        related_name="flats",
        verbose_name=_("Building"),
    )
    flat_number = models.CharField(
        max_length=20,
        verbose_name=_("Flat number"),
        help_text=_("Číslo jednotky, e.g. '1937/1'"),
    )
    floor = models.SmallIntegerField(
        null=True, blank=True, verbose_name=_("Floor"),
        help_text=_("0 = ground floor, negative = basement"),
    )
    area_m2 = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name=_("Area (m²)"),
    )
    disposition = models.CharField(
        max_length=10, blank=True,
        choices=DISPOSITION_CHOICES,
        verbose_name=_("Disposition"),
    )
    number_of_rooms = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Number of rooms")
    )
    water_outlets = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Water outlets")
    )
    waste_outlets = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Waste outlets")
    )
    radiator_count = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name=_("Radiator count")
    )
    radiator_power_kw = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name=_("Radiator power (kW)"),
    )
    gas_installed = models.BooleanField(default=False, verbose_name=_("Gas installed"))
    has_balcony = models.BooleanField(default=False, verbose_name=_("Has balcony"))
    cellar_unit = models.CharField(
        max_length=50, blank=True, verbose_name=_("Cellar unit")
    )
    ownership_cert_number = models.CharField(
        max_length=50, blank=True, verbose_name=_("Ownership certificate number"),
        help_text=_("Číslo LV jednotky"),
    )
    note = models.TextField(blank=True, verbose_name=_("Note"))

    # CUZK integration fields
    cuzk_unit_id = models.BigIntegerField(
        null=True, blank=True, verbose_name=_("CUZK unit ID"),
        db_index=True,
    )
    cuzk_share_numerator = models.IntegerField(
        null=True, blank=True, verbose_name=_("CUZK share numerator"),
        help_text=_("Podíl na společných částech - čitatel"),
    )
    cuzk_share_denominator = models.IntegerField(
        null=True, blank=True, verbose_name=_("CUZK share denominator"),
        help_text=_("Podíl na společných částech - jmenovatel"),
    )

    class Meta:
        ordering = ["building", "flat_number"]
        unique_together = [("building", "flat_number")]
        verbose_name = _("Flat")
        verbose_name_plural = _("Flats")

    def __str__(self):
        return f"{self.flat_number} ({self.building.name})"

    def get_absolute_url(self):
        return reverse("plugins:solomon_property:flat", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()

        has_numerator = self.cuzk_share_numerator is not None
        has_denominator = self.cuzk_share_denominator is not None

        if has_numerator != has_denominator:
            raise ValidationError(
                {
                    "cuzk_share_numerator": _("Both CUZK share values must be set together."),
                    "cuzk_share_denominator": _("Both CUZK share values must be set together."),
                }
            )

        if has_numerator and has_denominator:
            if self.cuzk_share_numerator <= 0:
                raise ValidationError(
                    {"cuzk_share_numerator": _("CUZK share numerator must be greater than zero.")}
                )
            if self.cuzk_share_denominator <= 0:
                raise ValidationError(
                    {"cuzk_share_denominator": _("CUZK share denominator must be greater than zero.")}
                )
            if self.cuzk_share_numerator > self.cuzk_share_denominator:
                raise ValidationError(
                    {"cuzk_share_numerator": _("CUZK share numerator cannot be greater than denominator.")}
                )

    @property
    def cuzk_share(self) -> str | None:
        """Return formatted share string, e.g. '73/9089'."""
        if self.cuzk_share_numerator and self.cuzk_share_denominator:
            return f"{self.cuzk_share_numerator}/{self.cuzk_share_denominator}"
        return None

    @property
    def current_ownership_share_total(self) -> float:
        """Return the summed ownership share for currently active ownership records."""
        current_owners = self.flat_owners.filter(effective_to__isnull=True)
        return sum(
            record.share_numerator / record.share_denominator
            for record in current_owners
            if record.share_denominator
        )

    @property
    def has_complete_current_ownership(self) -> bool:
        """Return True when active ownership shares sum to 100%."""
        return abs(self.current_ownership_share_total - 1.0) < 1e-9


# ---------------------------------------------------------------------------
#  Person
# ---------------------------------------------------------------------------

class Person(NetBoxModel):
    """
    A natural person - universal contact data store.

    Can be linked to:
      - Owner (via OwnerPerson, as the actual human behind an ownership)
      - Tenant (directly - the renting person)
      - Future: maintenance contacts, board members, etc.
    """

    first_name = models.CharField(max_length=100, verbose_name=_("First name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last name"))
    title_before = models.CharField(
        max_length=50, blank=True, verbose_name=_("Title before name"),
        help_text=_("e.g. Ing., Mgr., JUDr."),
    )
    title_after = models.CharField(
        max_length=50, blank=True, verbose_name=_("Title after name"),
        help_text=_("e.g. Ph.D., MBA"),
    )
    emails = ArrayField(
        base_field=models.EmailField(max_length=254),
        default=list,
        blank=True,
        verbose_name=_("Emails"),
    )
    phones = ArrayField(
        base_field=models.CharField(max_length=30),
        default=list,
        blank=True,
        verbose_name=_("Phones"),
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Date of birth"))
    permanent_address = models.TextField(blank=True, verbose_name=_("Permanent address"))
    contact_address = models.TextField(
        blank=True, verbose_name=_("Contact address"),
        help_text=_("If different from permanent address"),
    )
    note = models.TextField(blank=True, verbose_name=_("Note"))

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")

    def __str__(self):
        parts = []
        if self.title_before:
            parts.append(self.title_before)
        parts.append(self.first_name)
        parts.append(self.last_name)
        if self.title_after:
            parts.append(self.title_after)
        return " ".join(parts)

    @property
    def full_name(self) -> str:
        return str(self)

    @property
    def email(self) -> str:
        """Primary email (first in the list) for backward compatibility."""
        return self.emails[0] if self.emails else ""

    @property
    def phone(self) -> str:
        """Primary phone (first in the list) for backward compatibility."""
        return self.phones[0] if self.phones else ""

    def get_absolute_url(self):
        return reverse("plugins:solomon_property:person", kwargs={"pk": self.pk})


# ---------------------------------------------------------------------------
#  Owner
# ---------------------------------------------------------------------------

OWNER_TYPE_NATURAL = "natural"
OWNER_TYPE_LEGAL = "legal"
OWNER_TYPE_SJM = "sjm"

OWNER_TYPE_CHOICES = [
    (OWNER_TYPE_NATURAL, _("Natural person")),
    (OWNER_TYPE_LEGAL, _("Legal entity")),
    (OWNER_TYPE_SJM, _("SJM (joint ownership of spouses)")),
]


class PropertyOwner(NetBoxModel):
    """
    Legal ownership entity.

    Can be:
      - A natural person (person_type=natural, one Person linked)
      - An SJM (joint ownership of spouses, two Persons linked)
      - A legal entity (company/s.r.o., person_type=legal, one or more Persons)

    `persons` (M:N to Person) stores the actual human contacts:
      - natural: one person = the owner
      - SJM: two persons = husband and wife
      - legal: persons = company representative(s) or owner(s)

    `display_name` is the canonical name as it appears in cadastre, e.g.:
      "SJ Hnyk Ondřej a Hnykova Simona"
      "Novák Jan Ing."
      "ABC s.r.o."
    """

    display_name = models.CharField(
        max_length=300,
        verbose_name=_("Display name"),
        help_text=_("Full name as in cadastre/legal documents"),
    )
    person_type = models.CharField(
        max_length=10,
        choices=OWNER_TYPE_CHOICES,
        default=OWNER_TYPE_NATURAL,
        verbose_name=_("Person type"),
    )
    persons = models.ManyToManyField(
        "Person",
        blank=True,
        related_name="ownerships",
        verbose_name=_("Persons"),
        help_text=_("Individual persons behind this ownership (for contacts)"),
    )
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=30, blank=True, verbose_name=_("Phone"))
    permanent_address = models.TextField(blank=True, verbose_name=_("Permanent address"))
    contact_address = models.TextField(blank=True, verbose_name=_("Contact address"))
    deputy_name = models.CharField(
        max_length=200, blank=True, verbose_name=_("Deputy name"),
        help_text=_("Statutory representative (for legal entities) or authorized person"),
    )
    deputy_contact = models.CharField(
        max_length=200, blank=True, verbose_name=_("Deputy contact")
    )
    note = models.TextField(blank=True, verbose_name=_("Note"))

    # CUZK integration
    cuzk_owner_id = models.BigIntegerField(
        null=True, blank=True, verbose_name=_("CUZK owner ID"),
        db_index=True,
    )

    class Meta:
        ordering = ["display_name"]
        verbose_name = _("Property Owner")
        verbose_name_plural = _("Property Owners")

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("plugins:solomon_property:propertyowner", kwargs={"pk": self.pk})

    @property
    def current_total_share_fraction(self) -> Fraction:
        """Return summed ownership share from active FlatOwner rows."""
        total = Fraction(0, 1)
        for record in self.flat_owners.filter(effective_to__isnull=True):
            if record.share_denominator:
                total += Fraction(record.share_numerator, record.share_denominator)
        return total

    @property
    def current_total_share(self) -> str:
        total = self.current_total_share_fraction
        return f"{total.numerator}/{total.denominator}"

    @property
    def current_total_share_decimal(self) -> Decimal:
        total = self.current_total_share_fraction
        if total.denominator == 0:
            return Decimal("0")
        return Decimal(total.numerator) / Decimal(total.denominator)


# ---------------------------------------------------------------------------
#  FlatOwner  (M:N junction with share + effective dates)
# ---------------------------------------------------------------------------

class FlatOwner(NetBoxModel):
    """
    Ownership record: which PropertyOwner owns which Flat, with what share and when.

    `effective_from` is mandatory (cadastral transfer date).
    `effective_to` is null for current ownership.
    """

    flat = models.ForeignKey(
        Flat,
        on_delete=models.PROTECT,
        related_name="flat_owners",
        verbose_name=_("Flat"),
    )
    owner = models.ForeignKey(
        PropertyOwner,
        on_delete=models.PROTECT,
        related_name="flat_owners",
        verbose_name=_("Owner"),
    )
    share_numerator = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Share numerator"),
        help_text=_("Podíl vlastnictví - čitatel (e.g. 1 in 1/2)"),
    )
    share_denominator = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Share denominator"),
        help_text=_("Podíl vlastnictví - jmenovatel (e.g. 2 in 1/2)"),
    )
    effective_from = models.DateField(
        verbose_name=_("Effective from"),
        help_text=_("Date ownership began (cadastral transfer date)"),
    )
    effective_to = models.DateField(
        null=True, blank=True,
        verbose_name=_("Effective to"),
        help_text=_("Date ownership ended (null = current owner)"),
    )

    class Meta:
        ordering = ["flat", "effective_from"]
        unique_together = [("flat", "owner", "effective_from")]
        verbose_name = _("Flat ownership")
        verbose_name_plural = _("Flat ownerships")

    def __str__(self):
        share = f"{self.share_numerator}/{self.share_denominator}"
        return f"{self.owner} → {self.flat} ({share})"

    def get_absolute_url(self):
        return reverse("plugins:solomon_property:flatowner", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()

        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError(
                {"effective_to": _("Effective to cannot be before effective from.")}
            )

        if self.share_numerator > self.share_denominator:
            raise ValidationError(
                {"share_numerator": _("Share numerator cannot be greater than denominator.")}
            )

        period_end = self.effective_to
        overlapping = FlatOwner.objects.filter(flat=self.flat, owner=self.owner).exclude(pk=self.pk)

        if period_end is None:
            overlapping = overlapping.filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=self.effective_from)
            )
        else:
            overlapping = overlapping.filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=self.effective_from),
                effective_from__lte=period_end,
            )

        if overlapping.exists():
            raise ValidationError(
                _("Overlapping ownership period exists for this flat and owner.")
            )

    @property
    def share(self) -> str:
        return f"{self.share_numerator}/{self.share_denominator}"

    @property
    def is_current(self) -> bool:
        return self.effective_to is None


# ---------------------------------------------------------------------------
#  Tenant
# ---------------------------------------------------------------------------

class PropertyTenant(NetBoxModel):
    """
    A tenant renting a flat.

    Multiple tenants can be linked to one flat (e.g. a couple).
    Each tenant links to a Person record for contact details.
    """

    flat = models.ForeignKey(
        Flat,
        on_delete=models.PROTECT,
        related_name="tenants",
        verbose_name=_("Flat"),
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="tenancies",
        verbose_name=_("Person"),
    )
    effective_from = models.DateField(
        verbose_name=_("Effective from"),
        help_text=_("Move-in date"),
    )
    effective_to = models.DateField(
        null=True, blank=True,
        verbose_name=_("Effective to"),
        help_text=_("Move-out date (null = current tenant)"),
    )
    note = models.TextField(blank=True, verbose_name=_("Note"))

    class Meta:
        ordering = ["flat", "effective_from"]
        verbose_name = _("Property Tenant")
        verbose_name_plural = _("Property Tenants")

    def __str__(self):
        return f"{self.person} @ {self.flat}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_property:propertytenant", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()

        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError(
                {"effective_to": _("Effective to cannot be before effective from.")}
            )

        period_end = self.effective_to
        overlapping = PropertyTenant.objects.filter(flat=self.flat, person=self.person).exclude(pk=self.pk)

        if period_end is None:
            overlapping = overlapping.filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=self.effective_from)
            )
        else:
            overlapping = overlapping.filter(
                models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=self.effective_from),
                effective_from__lte=period_end,
            )

        if overlapping.exists():
            raise ValidationError(
                _("Overlapping tenancy period exists for this flat and person.")
            )

    @property
    def is_current(self) -> bool:
        return self.effective_to is None
