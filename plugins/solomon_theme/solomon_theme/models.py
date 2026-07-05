from django.db import models
from django.utils.translation import gettext_lazy as _


class ThemeAccess(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("use_solomon_theme", _("Can use Solomon theme")),
        )
