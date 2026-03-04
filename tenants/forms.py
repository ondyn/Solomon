"""
Solomon — Tenant forms.
"""

from django import forms

from .models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            "flat", "first_name", "last_name", "email", "phone",
            "permanent_address", "contact_address",
            "effective_from", "effective_to", "note",
        ]
        widgets = {
            "flat": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "permanent_address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "contact_address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "effective_from": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "effective_to": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
