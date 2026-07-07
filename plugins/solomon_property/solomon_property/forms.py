"""Solomon Property - ModelForms for create/edit views."""

import datetime

from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.forms.models import construct_instance
from django.utils.translation import gettext_lazy as _

from netbox.forms import NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField

from .models import Building, BuildingObject, Flat, FlatOwner, PropertyOwner, Person, PropertyTenant


class BuildingObjectForm(NetBoxModelForm):
    class Meta:
        model = BuildingObject
        fields = [
            "name",
            "cuzk_building_id",
            "building_type_name",
            "usage_name",
            "municipality_name",
            "city_part_name",
            "lv_number",
            "cadastral_territory_name",
            "house_numbers",
            "note",
            "tags",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class BuildingForm(NetBoxModelForm):
    building_object = DynamicModelChoiceField(
        queryset=BuildingObject.objects.all(),
        label=_("Building object"),
    )

    class Meta:
        model = Building
        fields = [
            "building_object",
            "name", "street", "house_number", "city", "postal_code",
            "number_of_floors", "elevator", "year_built", "total_units",
            "land_plot_number", "common_rooms", "floor_plan_url",
            "common_area_rental", "note",
            "cuzk_building_id", "cuzk_lv_number",
            "tags",
        ]
        widgets = {
            "common_rooms": forms.Textarea(attrs={"rows": 3}),
            "common_area_rental": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "name": _("Name"),
            "street": _("Street"),
            "house_number": _("House number"),
        }


class FlatForm(NetBoxModelForm):
    building = DynamicModelChoiceField(queryset=Building.objects.all(), label=_("Building"))

    class Meta:
        model = Flat
        fields = [
            "building", "flat_number", "floor", "area_m2", "disposition",
            "number_of_rooms", "water_outlets", "waste_outlets",
            "radiator_count", "radiator_power_kw",
            "gas_installed", "has_balcony", "cellar_unit",
            "ownership_cert_number", "note",
            "cuzk_unit_id", "cuzk_share_numerator", "cuzk_share_denominator",
            "tags",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class PersonForm(NetBoxModelForm):
    emails = SimpleArrayField(
        base_field=forms.EmailField(),
        required=False,
        label=_("Emails"),
        help_text=_("Comma-separated list of email addresses"),
    )
    phones = SimpleArrayField(
        base_field=forms.CharField(max_length=30),
        required=False,
        label=_("Phones"),
        help_text=_("Comma-separated list of phone numbers"),
    )

    class Meta:
        model = Person
        fields = [
            "title_before", "first_name", "last_name", "title_after",
            "emails", "phones",
            "date_of_birth",
            "permanent_address", "contact_address",
            "note", "tags",
        ]
        widgets = {
            "permanent_address": forms.Textarea(attrs={"rows": 2}),
            "contact_address": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class PropertyOwnerForm(NetBoxModelForm):
    persons = DynamicModelMultipleChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label=_("Persons"),
        help_text=_("Individual persons behind this ownership entity"),
    )

    class Meta:
        model = PropertyOwner
        fields = [
            "display_name", "person_type", "persons",
            "email", "phone",
            "permanent_address", "contact_address",
            "deputy_name", "deputy_contact",
            "note", "cuzk_owner_id",
            "tags",
        ]
        widgets = {
            "permanent_address": forms.Textarea(attrs={"rows": 2}),
            "contact_address": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class FlatOwnerForm(NetBoxModelForm):
    flat = DynamicModelChoiceField(queryset=Flat.objects.all(), label=_("Flat"))
    owner = DynamicModelChoiceField(queryset=PropertyOwner.objects.all(), label=_("Owner"))

    class Meta:
        model = FlatOwner
        fields = [
            "flat", "owner",
            "share_numerator", "share_denominator",
            "effective_from", "effective_to",
            "tags",
        ]
        widgets = {
            "effective_from": forms.DateInput(attrs={"type": "date"}),
            "effective_to": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        if self.instance.pk and commit:
            original = FlatOwner.objects.get(pk=self.instance.pk)
            history_fields = ("flat", "owner", "share_numerator", "share_denominator", "effective_from")
            history_changed = any(
                getattr(original, field) != self.cleaned_data[field]
                for field in history_fields
            )

            if original.effective_to is None and history_changed:
                new_effective_from = self.cleaned_data["effective_from"]
                original.effective_to = max(
                    original.effective_from,
                    new_effective_from - datetime.timedelta(days=1),
                )
                original.snapshot()
                original.save(update_fields=["effective_to"])

                m2m_values = getattr(self.instance, "_m2m_values", {}).copy()
                custom_field_data = self.instance.custom_field_data.copy()
                self.instance = self._meta.model()
                self.instance = construct_instance(self, self.instance, self._meta.fields, self._meta.exclude)
                self.instance._m2m_values = m2m_values
                self.instance.custom_field_data = custom_field_data

        return super().save(commit=commit)


class PropertyTenantForm(NetBoxModelForm):
    flat = DynamicModelChoiceField(queryset=Flat.objects.all(), label=_("Flat"))
    person = DynamicModelChoiceField(queryset=Person.objects.all(), label=_("Person"))

    class Meta:
        model = PropertyTenant
        fields = [
            "flat", "person",
            "effective_from", "effective_to",
            "note", "tags",
        ]
        widgets = {
            "effective_from": forms.DateInput(attrs={"type": "date"}),
            "effective_to": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }
