"""
Solomon — Building model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel, register_auditlog


@register_auditlog
class Building(BaseModel):
    """
    Represents an apartment building managed by the SVJ.

    One SVJ manages multiple buildings; each building contains many flats.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Building name or label, e.g. 'Salounova 1'"),
    )
    street = models.CharField(
        max_length=255,
        verbose_name=_("Street"),
    )
    house_number = models.CharField(
        max_length=20,
        verbose_name=_("House number"),
        help_text=_("Číslo popisné / orientační"),
    )
    city = models.CharField(
        max_length=255,
        default="Brno",
        verbose_name=_("City"),
    )
    postal_code = models.CharField(
        max_length=10,
        verbose_name=_("Postal code"),
    )
    number_of_floors = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Number of floors"),
    )
    elevator = models.BooleanField(
        default=False,
        verbose_name=_("Elevator"),
    )
    year_built = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Year built"),
    )
    total_units = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Total units"),
        help_text=_("Total number of flats/units in the building"),
    )
    land_plot_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Land plot number"),
        help_text=_("Číslo pozemku"),
    )
    common_rooms = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Common rooms"),
        help_text=_("Description of common areas (e.g. laundry, bike storage)"),
    )
    floor_plan_url = models.URLField(
        blank=True,
        default="",
        verbose_name=_("Floor plan URL"),
    )
    common_area_rental = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Common area rental"),
        help_text=_("Information about rented common areas"),
    )
    note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Note"),
    )

    class Meta(BaseModel.Meta):
        verbose_name = _("Building")
        verbose_name_plural = _("Buildings")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.street} {self.house_number})"
