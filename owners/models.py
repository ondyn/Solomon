"""
Solomon — Owner and FlatOwner models.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel, register_auditlog


@register_auditlog
class Owner(BaseModel):
    """
    Represents a flat owner (vlastník).

    An Owner may optionally be linked to a Django User account
    (for owners who log in to the system).
    """

    class PersonType(models.TextChoices):
        NATURAL = "natural", _("Natural person")
        LEGAL = "legal", _("Legal person")

    person_type = models.CharField(
        max_length=10,
        choices=PersonType.choices,
        default=PersonType.NATURAL,
        verbose_name=_("Person type"),
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name=_("First name"),
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name=_("Last name"),
    )
    email = models.EmailField(
        blank=True,
        default="",
        verbose_name=_("Email"),
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name=_("Phone"),
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date of birth"),
    )
    permanent_address = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Permanent address"),
        help_text=_("Trvalé bydliště"),
    )
    contact_address = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Contact address"),
        help_text=_("Korespondenční adresa (if different from permanent)"),
    )
    deputy_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Deputy name"),
        help_text=_("Name of deputy / authorized representative"),
    )
    deputy_contact = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Deputy contact"),
        help_text=_("Phone or email of deputy"),
    )
    # Optional link to auth.User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owner_profile",
        verbose_name=_("User account"),
    )
    note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Note"),
    )

    class Meta(BaseModel.Meta):
        verbose_name = _("Owner")
        verbose_name_plural = _("Owners")
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@register_auditlog
class FlatOwner(BaseModel):
    """
    Junction table linking Flat to Owner with ownership details.

    Tracks ownership share (as numerator/denominator) and
    effective date range.
    """

    flat = models.ForeignKey(
        "flats.Flat",
        on_delete=models.PROTECT,
        related_name="flat_owners",
        verbose_name=_("Flat"),
    )
    owner = models.ForeignKey(
        "owners.Owner",
        on_delete=models.PROTECT,
        related_name="flat_owners",
        verbose_name=_("Owner"),
    )
    share_numerator = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Share numerator"),
        help_text=_("Podíl — čitatel"),
    )
    share_denominator = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Share denominator"),
        help_text=_("Podíl — jmenovatel"),
    )
    effective_from = models.DateField(
        verbose_name=_("Effective from"),
    )
    effective_to = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Effective to"),
        help_text=_("Leave blank if still active"),
    )

    class Meta(BaseModel.Meta):
        verbose_name = _("Flat ownership")
        verbose_name_plural = _("Flat ownerships")
        ordering = ["flat", "-effective_from"]
        unique_together = [("flat", "owner", "effective_from")]

    def __str__(self) -> str:
        return f"{self.owner} → {self.flat} ({self.share_numerator}/{self.share_denominator})"

    @property
    def share_percentage(self) -> float:
        """Return ownership share as a percentage."""
        if self.share_denominator == 0:
            return 0.0
        return round((self.share_numerator / self.share_denominator) * 100, 2)
