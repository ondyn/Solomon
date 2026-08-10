"""NetBox forms for Solomon Facilities."""

from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelForm
from solomon_property.models import (
    Building,
    BuildingObject,
    Flat,
    Person,
    PropertyOwner,
)
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.widgets import DatePicker

from . import models


class BuildingLevelForm(NetBoxModelForm):
    building_object = DynamicModelChoiceField(
        queryset=BuildingObject.objects.all(), label=_("Building object")
    )

    class Meta:
        model = models.BuildingLevel
        fields = (
            "building_object",
            "number",
            "reference",
            "name",
            "elevation_m",
            "height_m",
            "notes",
            "tags",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class FloorPlanForm(NetBoxModelForm):
    level = DynamicModelChoiceField(queryset=models.BuildingLevel.objects.all())

    class Meta:
        model = models.FloorPlan
        fields = (
            "level",
            "name",
            "width",
            "height",
            "measurement_unit",
            "notes",
            "tags",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class PlanRevisionForm(NetBoxModelForm):
    class Meta:
        model = models.PlanRevision
        fields = (
            "source_file",
            "background_file",
            "background_rotation",
            "source_page",
            "scale_denominator",
            "source_note",
            "tags",
        )
        labels = {
            "source_file": _("Original source document"),
            "background_file": _("Drawable canvas background"),
        }
        help_texts = {
            "source_file": _(
                "Optional archival PDF or source drawing. This file is not displayed on the canvas."
            ),
            "background_file": _(
                "Optional SVG, PNG, or JPEG displayed beneath editable drawing elements."
            ),
        }
        widgets = {"source_note": forms.Textarea(attrs={"rows": 3})}


class SpaceForm(NetBoxModelForm):
    level = DynamicModelChoiceField(queryset=models.BuildingLevel.objects.all())
    building = DynamicModelChoiceField(queryset=Building.objects.all(), required=False)
    parent = DynamicModelChoiceField(
        queryset=models.Space.objects.all(), required=False
    )

    class Meta:
        model = models.Space
        fields = (
            "level",
            "building",
            "parent",
            "reference",
            "name",
            "kind",
            "status",
            "area_m2",
            "notes",
            "tags",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class SpaceFlatAssignmentForm(NetBoxModelForm):
    space = DynamicModelChoiceField(queryset=models.Space.objects.all())
    flat = DynamicModelChoiceField(queryset=Flat.objects.all())

    class Meta:
        model = models.SpaceFlatAssignment
        fields = (
            "space",
            "flat",
            "role",
            "effective_from",
            "effective_to",
            "notes",
            "tags",
        )
        widgets = {
            "effective_from": DatePicker(),
            "effective_to": DatePicker(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class SpaceUsageForm(NetBoxModelForm):
    space = DynamicModelChoiceField(queryset=models.Space.objects.all())
    person = DynamicModelChoiceField(queryset=Person.objects.all(), required=False)
    owner = DynamicModelChoiceField(
        queryset=PropertyOwner.objects.all(), required=False
    )

    class Meta:
        model = models.SpaceUsage
        fields = (
            "space",
            "person",
            "owner",
            "usage_type",
            "effective_from",
            "effective_to",
            "notes",
            "tags",
        )
        widgets = {
            "effective_from": DatePicker(),
            "effective_to": DatePicker(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class DoorForm(NetBoxModelForm):
    level = DynamicModelChoiceField(queryset=models.BuildingLevel.objects.all())
    from_space = DynamicModelChoiceField(
        queryset=models.Space.objects.all(), required=False
    )
    to_space = DynamicModelChoiceField(
        queryset=models.Space.objects.all(), required=False
    )

    class Meta:
        model = models.Door
        fields = (
            "level",
            "reference",
            "name",
            "door_type",
            "from_space",
            "to_space",
            "fire_rating",
            "emergency_exit",
            "notes",
            "tags",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class LockCylinderForm(NetBoxModelForm):
    door = DynamicModelChoiceField(queryset=models.Door.objects.all())

    class Meta:
        model = models.LockCylinder
        fields = ("door", "name", "code", "active_from", "active_to", "notes", "tags")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class KeyProfileForm(NetBoxModelForm):
    building_object = DynamicModelChoiceField(queryset=BuildingObject.objects.all())
    locks = DynamicModelMultipleChoiceField(
        queryset=models.LockCylinder.objects.all(),
        required=False,
        label=_("Locks opened"),
    )

    class Meta:
        model = models.KeyProfile
        fields = ("building_object", "code", "name", "locks", "notes", "tags")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def clean_locks(self):
        locks = self.cleaned_data["locks"]
        building_object = self.cleaned_data.get("building_object")
        if (
            building_object
            and locks.exclude(door__level__building_object=building_object).exists()
        ):
            raise forms.ValidationError(
                _("Every lock must belong to the selected building object.")
            )
        return locks

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            instance.locks.set(self.cleaned_data["locks"])
        return instance


class KeyCopyForm(NetBoxModelForm):
    profile = DynamicModelChoiceField(queryset=models.KeyProfile.objects.all())

    class Meta:
        model = models.KeyCopy
        fields = (
            "profile",
            "inventory_code",
            "serial_number",
            "status",
            "notes",
            "tags",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class KeyIssueForm(NetBoxModelForm):
    key_copy = DynamicModelChoiceField(queryset=models.KeyCopy.objects.all())
    person = DynamicModelChoiceField(queryset=Person.objects.all(), required=False)

    class Meta:
        model = models.KeyIssue
        fields = (
            "key_copy",
            "person",
            "external_holder",
            "issued_at",
            "due_at",
            "returned_at",
            "purpose",
            "notes",
            "tags",
        )
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class TechnicalSystemForm(NetBoxModelForm):
    building_object = DynamicModelChoiceField(queryset=BuildingObject.objects.all())

    class Meta:
        model = models.TechnicalSystem
        fields = ("building_object", "name", "kind", "description", "tags")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class TechnicalAssetForm(NetBoxModelForm):
    system = DynamicModelChoiceField(queryset=models.TechnicalSystem.objects.all())
    parent = DynamicModelChoiceField(
        queryset=models.TechnicalAsset.objects.all(), required=False
    )
    level = DynamicModelChoiceField(
        queryset=models.BuildingLevel.objects.all(), required=False
    )
    space = DynamicModelChoiceField(queryset=models.Space.objects.all(), required=False)
    serves_flats = DynamicModelMultipleChoiceField(
        queryset=Flat.objects.all(), required=False
    )
    serves_spaces = DynamicModelMultipleChoiceField(
        queryset=models.Space.objects.all(), required=False
    )

    class Meta:
        model = models.TechnicalAsset
        fields = (
            "system",
            "parent",
            "level",
            "space",
            "code",
            "name",
            "asset_type",
            "status",
            "serves_flats",
            "serves_spaces",
            "emergency_instructions",
            "notes",
            "tags",
        )
        widgets = {
            "emergency_instructions": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class TechnicalConnectionForm(NetBoxModelForm):
    from_asset = DynamicModelChoiceField(queryset=models.TechnicalAsset.objects.all())
    to_asset = DynamicModelChoiceField(queryset=models.TechnicalAsset.objects.all())

    class Meta:
        model = models.TechnicalConnection
        fields = ("from_asset", "to_asset", "kind", "notes", "tags")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
