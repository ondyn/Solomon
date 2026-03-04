"""
Solomon — Flat model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel, register_auditlog


@register_auditlog
class Flat(BaseModel):
    """
    Represents an individual flat (unit) within a building.

    Each flat belongs to exactly one building. Owners are linked
    via the FlatOwner junction table in the owners app.
    """

    building = models.ForeignKey(
        "buildings.Building",
        on_delete=models.PROTECT,
        related_name="flats",
        verbose_name=_("Building"),
    )
    flat_number = models.CharField(
        max_length=20,
        verbose_name=_("Flat number"),
        help_text=_("Apartment number within the building"),
    )
    floor = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Floor"),
    )
    area_m2 = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Area (m²)"),
    )
    disposition = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name=_("Disposition"),
        help_text=_("e.g. 2+1, 3+kk"),
    )
    number_of_rooms = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Number of rooms"),
    )
    water_outlets = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Water outlets"),
    )
    waste_outlets = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Waste outlets"),
    )
    radiator_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Radiator count"),
    )
    radiator_power_kw = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Radiator power (kW)"),
    )
    gas_installed = models.BooleanField(
        default=False,
        verbose_name=_("Gas installed"),
    )
    has_balcony = models.BooleanField(
        default=False,
        verbose_name=_("Has balcony"),
    )
    cellar_unit = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Cellar unit"),
        help_text=_("Cellar / storage unit number"),
    )
    ownership_cert_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Ownership certificate number"),
        help_text=_("Číslo listu vlastnictví"),
    )
    note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Note"),
    )

    class Meta(BaseModel.Meta):
        verbose_name = _("Flat")
        verbose_name_plural = _("Flats")
        ordering = ["building", "flat_number"]
        unique_together = [("building", "flat_number")]

    def __str__(self) -> str:
        return f"{self.building.name} — {self.flat_number}"
