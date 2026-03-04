"""
Solomon — Tenant model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel, register_auditlog


@register_auditlog
class Tenant(BaseModel):
    """
    Represents a tenant (nájemce) renting a flat.

    Tenants are linked to flats, not directly to owners.
    """

    flat = models.ForeignKey(
        "flats.Flat",
        on_delete=models.PROTECT,
        related_name="tenants",
        verbose_name=_("Flat"),
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
        help_text=_("Korespondenční adresa"),
    )
    effective_from = models.DateField(
        verbose_name=_("Lease start"),
    )
    effective_to = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Lease end"),
        help_text=_("Leave blank if still active"),
    )
    note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Note"),
    )

    class Meta(BaseModel.Meta):
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")
        ordering = ["flat", "last_name"]

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} ({self.flat})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
