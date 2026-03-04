"""
Solomon — Building forms.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Building


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = [
            "name", "street", "house_number", "city", "postal_code",
            "number_of_floors", "elevator", "year_built", "total_units",
            "land_plot_number", "common_rooms", "floor_plan_url",
            "common_area_rental", "note",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "street": forms.TextInput(attrs={"class": "form-control"}),
            "house_number": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "number_of_floors": forms.NumberInput(attrs={"class": "form-control"}),
            "elevator": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "year_built": forms.NumberInput(attrs={"class": "form-control"}),
            "total_units": forms.NumberInput(attrs={"class": "form-control"}),
            "land_plot_number": forms.TextInput(attrs={"class": "form-control"}),
            "common_rooms": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "floor_plan_url": forms.URLInput(attrs={"class": "form-control"}),
            "common_area_rental": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
