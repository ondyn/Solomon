"""Search filters for Solomon Facilities."""

import django_filters
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from . import models


class SearchFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")
    search_fields = ()

    def search(self, queryset, name, value):
        query = Q()
        for field in self.search_fields:
            query |= Q(**{f"{field}__icontains": value})
        return queryset.filter(query).distinct()


class BuildingLevelFilterSet(SearchFilterSet):
    search_fields = ("reference", "name", "building_object__name")

    class Meta:
        model = models.BuildingLevel
        fields = ("building_object", "number", "reference")


class FloorPlanFilterSet(SearchFilterSet):
    search_fields = ("name", "level__reference", "level__building_object__name")

    class Meta:
        model = models.FloorPlan
        fields = ("level",)


class SpaceFilterSet(SearchFilterSet):
    search_fields = ("reference", "name", "building__name", "level__reference")

    class Meta:
        model = models.Space
        fields = ("level", "building", "kind", "status")


class DoorFilterSet(SearchFilterSet):
    search_fields = ("reference", "name", "level__reference")

    class Meta:
        model = models.Door
        fields = ("level", "door_type", "emergency_exit")


class KeyProfileFilterSet(SearchFilterSet):
    search_fields = ("code", "name", "building_object__name")

    class Meta:
        model = models.KeyProfile
        fields = ("building_object",)


class KeyCopyFilterSet(SearchFilterSet):
    search_fields = (
        "inventory_code",
        "serial_number",
        "profile__code",
        "profile__name",
    )

    class Meta:
        model = models.KeyCopy
        fields = ("profile", "status")


class TechnicalSystemFilterSet(SearchFilterSet):
    search_fields = ("name", "description", "building_object__name")

    class Meta:
        model = models.TechnicalSystem
        fields = ("building_object", "kind")


class TechnicalAssetFilterSet(SearchFilterSet):
    search_fields = ("code", "name", "asset_type", "system__name", "space__name")

    class Meta:
        model = models.TechnicalAsset
        fields = ("system", "level", "space", "status")
