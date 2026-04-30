"""Solomon Property - REST API ViewSets."""

from netbox.api.viewsets import NetBoxModelViewSet

from solomon_property import filtersets, models

from .serializers import (
    BuildingSerializer,
    BuildingObjectSerializer,
    FlatOwnerSerializer,
    FlatSerializer,
    PropertyOwnerSerializer,
    PersonSerializer,
    PropertyTenantSerializer,
)


class BuildingObjectViewSet(NetBoxModelViewSet):
    queryset = models.BuildingObject.objects.all()
    serializer_class = BuildingObjectSerializer
    filterset_class = filtersets.BuildingObjectFilterSet


class BuildingViewSet(NetBoxModelViewSet):
    queryset = models.Building.objects.select_related("building_object")
    serializer_class = BuildingSerializer
    filterset_class = filtersets.BuildingFilterSet


class FlatViewSet(NetBoxModelViewSet):
    queryset = models.Flat.objects.select_related("building")
    serializer_class = FlatSerializer
    filterset_class = filtersets.FlatFilterSet


class PersonViewSet(NetBoxModelViewSet):
    queryset = models.Person.objects.all()
    serializer_class = PersonSerializer
    filterset_class = filtersets.PersonFilterSet


class PropertyOwnerViewSet(NetBoxModelViewSet):
    queryset = models.PropertyOwner.objects.prefetch_related("persons")
    serializer_class = PropertyOwnerSerializer
    filterset_class = filtersets.PropertyOwnerFilterSet


class FlatOwnerViewSet(NetBoxModelViewSet):
    queryset = models.FlatOwner.objects.select_related("flat", "owner")
    serializer_class = FlatOwnerSerializer
    filterset_class = filtersets.FlatOwnerFilterSet


class PropertyTenantViewSet(NetBoxModelViewSet):
    queryset = models.PropertyTenant.objects.select_related("flat", "person")
    serializer_class = PropertyTenantSerializer
    filterset_class = filtersets.PropertyTenantFilterSet
