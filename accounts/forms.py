"""
Solomon — User management forms.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserForm(forms.ModelForm):
    """Form for creating / updating users (without password)."""

    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label=_("Role"),
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text=_("Assign the user to a role group."),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            groups = self.instance.groups.all()
            if groups.exists():
                self.fields["role"].initial = groups.first()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            role = self.cleaned_data.get("role")
            user.groups.clear()
            if role:
                user.groups.add(role)
        return user


class UserCreateForm(UserForm):
    """Form for creating a new user with password."""

    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta(UserForm.Meta):
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("Passwords do not match."))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            role = self.cleaned_data.get("role")
            user.groups.clear()
            if role:
                user.groups.add(role)
        return user
