"""
Solomon — Base models shared across all apps.

All domain models should inherit from BaseModel which provides:
- UUID primary key
- created_at / updated_at timestamps
- Soft delete via django-safedelete
- Automatic audit trail via django-auditlog
"""

import uuid

from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE_CASCADE


class BaseModel(SafeDeleteModel):
    """
    Abstract base model for all Solomon domain models.

    Provides:
    - ``id``: UUID primary key
    - ``created_at``: auto-set on creation
    - ``updated_at``: auto-set on every save
    - Soft delete (``is_deleted`` handled by django-safedelete)
    """

    _safedelete_policy = SOFT_DELETE_CASCADE

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return str(self.id)


def register_auditlog(model_class):
    """
    Decorator to register a model with django-auditlog.

    Usage::

        @register_auditlog
        class Building(BaseModel):
            ...
    """
    auditlog.register(model_class)
    return model_class
