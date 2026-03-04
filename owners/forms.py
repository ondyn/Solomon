"""
Solomon — Owner forms.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import FlatOwner, Owner


class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = [
            "person_type", "first_name", "last_name", "email", "phone",
            "date_of_birth", "permanent_address", "contact_address",
            "deputy_name", "deputy_contact", "note",
        ]
        widgets = {
            "person_type": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "permanent_address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "contact_address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "deputy_name": forms.TextInput(attrs={"class": "form-control"}),
            "deputy_contact": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


class FlatOwnerForm(forms.ModelForm):
    class Meta:
        model = FlatOwner
        fields = ["flat", "owner", "share_numerator", "share_denominator", "effective_from", "effective_to"]
        widgets = {
            "flat": forms.Select(attrs={"class": "form-select"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "share_numerator": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "share_denominator": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "effective_from": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "effective_to": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        flat = cleaned.get("flat")
        if flat:
            self._share_warning = self._check_share_sum(flat, cleaned)
        return cleaned

    def _check_share_sum(self, flat, cleaned):
        """
        Check if ownership shares for the flat sum to 100% after this save.
        Returns a warning message or None.
        """
        numerator = cleaned.get("share_numerator", 0)
        denominator = cleaned.get("share_denominator", 1) or 1

        # Get existing shares for this flat, excluding current instance if editing
        existing = FlatOwner.objects.filter(flat=flat)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        total_pct = sum(
            fo.share_numerator / fo.share_denominator * 100
            for fo in existing
        )
        total_pct += numerator / denominator * 100

        if abs(total_pct - 100.0) > 0.01:
            return _(
                "Warning: Total ownership shares for this flat sum to %(pct).1f%%, not 100%%."
            ) % {"pct": total_pct}
        return None
