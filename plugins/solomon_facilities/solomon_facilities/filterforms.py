"""Filter forms for Solomon Facilities list views."""

from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelFilterSetForm
from solomon_property.models import Building
from utilities.forms import add_blank_choice
from utilities.forms.fields import DynamicModelChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from . import models


class SpaceFilterForm(NetBoxModelFilterSetForm):
    model = models.Space
    fieldsets = (
        FieldSet("q", "filter_id", "tag"),
        FieldSet("level", "building", "kind", "status", name=_("Space")),
    )
    level = DynamicModelChoiceField(
        queryset=models.BuildingLevel.objects.all(), required=False
    )
    building = DynamicModelChoiceField(queryset=Building.objects.all(), required=False)
    kind = forms.ChoiceField(
        choices=add_blank_choice(models.SPACE_KIND_CHOICES),
        required=False,
        label=_("Type"),
    )
    status = forms.ChoiceField(
        choices=add_blank_choice(models.SPACE_STATUS_CHOICES),
        required=False,
        label=_("Status"),
    )
    tag = TagFilterField(models.Space)
