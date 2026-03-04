"""
Solomon — Flat forms.
"""

from django import forms

from .models import Flat


class FlatForm(forms.ModelForm):
    class Meta:
        model = Flat
        fields = [
            "building", "flat_number", "floor", "area_m2", "disposition",
            "number_of_rooms", "water_outlets", "waste_outlets",
            "radiator_count", "radiator_power_kw", "gas_installed",
            "has_balcony", "cellar_unit", "ownership_cert_number", "note",
        ]
        widgets = {
            "building": forms.Select(attrs={"class": "form-select"}),
            "flat_number": forms.TextInput(attrs={"class": "form-control"}),
            "floor": forms.NumberInput(attrs={"class": "form-control"}),
            "area_m2": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "disposition": forms.TextInput(attrs={"class": "form-control"}),
            "number_of_rooms": forms.NumberInput(attrs={"class": "form-control"}),
            "water_outlets": forms.NumberInput(attrs={"class": "form-control"}),
            "waste_outlets": forms.NumberInput(attrs={"class": "form-control"}),
            "radiator_count": forms.NumberInput(attrs={"class": "form-control"}),
            "radiator_power_kw": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "gas_installed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_balcony": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cellar_unit": forms.TextInput(attrs={"class": "form-control"}),
            "ownership_cert_number": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
