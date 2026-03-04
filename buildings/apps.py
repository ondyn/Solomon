from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BuildingsConfig(AppConfig):
    default_auto_field = "django.db.models.UUIDField"
    name = "buildings"
    verbose_name = _("Buildings")
