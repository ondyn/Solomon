"""Solomon Property - Filter forms for the Filters tab on list views."""

from django import forms
from django.utils.translation import gettext_lazy as _

from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from .models import Building, Flat, FlatOwner, Person, PropertyOwner, PropertyTenant


class BuildingFilterForm(NetBoxModelFilterSetForm):
    model = Building
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('name', 'city', 'house_number', name=_('Building')),
    )
    name = forms.CharField(required=False, label=_('Name'))
    city = forms.CharField(required=False, label=_('City'))
    house_number = forms.CharField(required=False, label=_('House number'))
    tag = TagFilterField(model)


class FlatFilterForm(NetBoxModelFilterSetForm):
    model = Flat
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('building_id', 'flat_number', 'floor', 'disposition', name=_('Flat')),
    )
    building_id = DynamicModelChoiceField(
        queryset=Building.objects.all(),
        required=False,
        label=_('Building'),
    )
    flat_number = forms.CharField(required=False, label=_('Flat number'))
    floor = forms.IntegerField(required=False, label=_('Floor'))
    disposition = forms.CharField(required=False, label=_('Disposition'))
    tag = TagFilterField(model)


class PersonFilterForm(NetBoxModelFilterSetForm):
    model = Person
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('last_name', 'first_name', 'email', name=_('Person')),
    )
    last_name = forms.CharField(required=False, label=_('Last name'))
    first_name = forms.CharField(required=False, label=_('First name'))
    email = forms.CharField(required=False, label=_('Email'))
    tag = TagFilterField(model)


class PropertyOwnerFilterForm(NetBoxModelFilterSetForm):
    model = PropertyOwner
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('display_name', 'person_type', name=_('Owner')),
    )
    display_name = forms.CharField(required=False, label=_('Name'))
    person_type = forms.MultipleChoiceField(
        choices=[
            ('natural', _('Natural person')),
            ('legal', _('Legal entity')),
            ('sjm', _('SJM')),
        ],
        required=False,
        label=_('Type'),
    )
    tag = TagFilterField(model)


class FlatOwnerFilterForm(NetBoxModelFilterSetForm):
    model = FlatOwner
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('flat_id', 'owner_id', 'is_current', name=_('Ownership')),
    )
    flat_id = DynamicModelChoiceField(
        queryset=Flat.objects.all(),
        required=False,
        label=_('Flat'),
    )
    owner_id = DynamicModelChoiceField(
        queryset=PropertyOwner.objects.all(),
        required=False,
        label=_('Owner'),
    )
    is_current = forms.NullBooleanField(
        required=False,
        label=_('Current owner'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    tag = TagFilterField(model)


class PropertyTenantFilterForm(NetBoxModelFilterSetForm):
    model = PropertyTenant
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('flat_id', 'person_id', 'is_current', name=_('Tenancy')),
    )
    flat_id = DynamicModelChoiceField(
        queryset=Flat.objects.all(),
        required=False,
        label=_('Flat'),
    )
    person_id = DynamicModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label=_('Person'),
    )
    is_current = forms.NullBooleanField(
        required=False,
        label=_('Current tenant'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    tag = TagFilterField(model)
