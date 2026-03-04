from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FlatsConfig(AppConfig):
    default_auto_field = "django.db.models.UUIDField"
    name = "flats"
    verbose_name = _("Flats")
