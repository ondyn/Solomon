"""Solomon Property - FilterSets for list view filtering."""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from netbox.filtersets import NetBoxModelFilterSet

from .models import (
    Building,
    BuildingObject,
    Flat,
    FlatOwner,
    PropertyOwner,
    Person,
    PropertyTenant,
)


class BuildingObjectFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    name = django_filters.CharFilter(lookup_expr="icontains", label=_("Name"))
    municipality_name = django_filters.CharFilter(
        lookup_expr="icontains", label=_("Municipality")
    )
    city_part_name = django_filters.CharFilter(
        lookup_expr="icontains", label=_("City part")
    )
    cuzk_building_id = django_filters.NumberFilter()

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(municipality_name__icontains=value)
            | Q(city_part_name__icontains=value)
            | Q(cadastral_territory_name__icontains=value)
        )

    class Meta:
        model = BuildingObject
        fields = ["name", "municipality_name", "city_part_name", "cuzk_building_id"]


class BuildingFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    name = django_filters.CharFilter(lookup_expr="icontains", label=_("Name"))
    city = django_filters.CharFilter(lookup_expr="icontains", label=_("City"))
    house_number = django_filters.CharFilter(lookup_expr="icontains")
    building_object_id = django_filters.ModelChoiceFilter(
        queryset=BuildingObject.objects.all(),
        label=_("Building object"),
    )
    cuzk_building_id = django_filters.NumberFilter()

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(building_object__name__icontains=value)
            | Q(street__icontains=value)
            | Q(house_number__icontains=value)
            | Q(city__icontains=value)
        )

    class Meta:
        model = Building
        fields = [
            "name",
            "city",
            "house_number",
            "building_object_id",
            "cuzk_building_id",
        ]


class FlatFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    flat_number = django_filters.CharFilter(
        lookup_expr="icontains", label=_("Flat number")
    )
    building_id = django_filters.ModelChoiceFilter(
        queryset=Building.objects.all(), label=_("Building")
    )
    floor = django_filters.NumberFilter()
    disposition = django_filters.CharFilter(lookup_expr="icontains")

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(flat_number__icontains=value)
            | Q(building__name__icontains=value)
            | Q(building__house_number__icontains=value)
        )

    class Meta:
        model = Flat
        fields = ["flat_number", "building_id", "floor", "disposition"]


class PersonFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(method="filter_email", label=_("Email"))

    def filter_email(self, queryset, name, value):
        """Filter by email - search across all emails in the array."""
        return queryset.filter(emails__icontains=value)

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(emails__icontains=value)
            | Q(phones__icontains=value)
        )

    class Meta:
        model = Person
        fields = ["last_name", "first_name", "email"]


class PropertyOwnerFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    display_name = django_filters.CharFilter(lookup_expr="icontains")
    person_type = django_filters.MultipleChoiceFilter(
        choices=[
            ("natural", _("Natural person")),
            ("legal", _("Legal entity")),
            ("sjm", _("SJM")),
        ]
    )

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(display_name__icontains=value)
            | Q(persons__first_name__icontains=value)
            | Q(persons__last_name__icontains=value)
            | Q(persons__emails__icontains=value)
            | Q(persons__phones__icontains=value)
        ).distinct()

    class Meta:
        model = PropertyOwner
        fields = ["display_name", "person_type"]


class FlatOwnerFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    flat_id = django_filters.ModelChoiceFilter(
        queryset=Flat.objects.all(), label=_("Flat")
    )
    owner_id = django_filters.ModelChoiceFilter(
        queryset=PropertyOwner.objects.all(), label=_("Owner")
    )
    effective_from = django_filters.DateFilter()
    effective_to = django_filters.DateFilter()
    is_current = django_filters.BooleanFilter(
        method="filter_is_current", label=_("Current owner")
    )

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(owner__display_name__icontains=value)
            | Q(flat__flat_number__icontains=value)
            | Q(flat__building__name__icontains=value)
        )

    def filter_is_current(self, queryset, name, value):
        if value:
            return queryset.filter(effective_to__isnull=True)
        return queryset.filter(effective_to__isnull=False)

    class Meta:
        model = FlatOwner
        fields = ["flat_id", "owner_id"]


class PropertyTenantFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label=_("Search"))
    flat_id = django_filters.ModelChoiceFilter(
        queryset=Flat.objects.all(), label=_("Flat")
    )
    person_id = django_filters.ModelChoiceFilter(
        queryset=Person.objects.all(), label=_("Person")
    )
    is_current = django_filters.BooleanFilter(
        method="filter_is_current", label=_("Current tenant")
    )

    def search(self, queryset, name, value):
        return queryset.filter(
            Q(person__first_name__icontains=value)
            | Q(person__last_name__icontains=value)
            | Q(flat__flat_number__icontains=value)
            | Q(flat__building__name__icontains=value)
        )

    def filter_is_current(self, queryset, name, value):
        if value:
            return queryset.filter(effective_to__isnull=True)
        return queryset.filter(effective_to__isnull=False)

    class Meta:
        model = PropertyTenant
        fields = ["flat_id", "person_id"]
