from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets, models
from . import serializers


class BuildingLevelViewSet(NetBoxModelViewSet):
    queryset = models.BuildingLevel.objects.all()
    serializer_class = serializers.BuildingLevelSerializer
    filterset_class = filtersets.BuildingLevelFilterSet


class FloorPlanViewSet(NetBoxModelViewSet):
    queryset = models.FloorPlan.objects.all()
    serializer_class = serializers.FloorPlanSerializer
    filterset_class = filtersets.FloorPlanFilterSet


class PlanRevisionViewSet(NetBoxModelViewSet):
    queryset = models.PlanRevision.objects.all()
    serializer_class = serializers.PlanRevisionSerializer


class SpaceViewSet(NetBoxModelViewSet):
    queryset = models.Space.objects.all()
    serializer_class = serializers.SpaceSerializer
    filterset_class = filtersets.SpaceFilterSet


class SpaceFlatAssignmentViewSet(NetBoxModelViewSet):
    queryset = models.SpaceFlatAssignment.objects.all()
    serializer_class = serializers.SpaceFlatAssignmentSerializer


class SpaceUsageViewSet(NetBoxModelViewSet):
    queryset = models.SpaceUsage.objects.all()
    serializer_class = serializers.SpaceUsageSerializer


class DoorViewSet(NetBoxModelViewSet):
    queryset = models.Door.objects.all()
    serializer_class = serializers.DoorSerializer
    filterset_class = filtersets.DoorFilterSet


class LockCylinderViewSet(NetBoxModelViewSet):
    queryset = models.LockCylinder.objects.all()
    serializer_class = serializers.LockCylinderSerializer


class KeyProfileViewSet(NetBoxModelViewSet):
    queryset = models.KeyProfile.objects.all()
    serializer_class = serializers.KeyProfileSerializer
    filterset_class = filtersets.KeyProfileFilterSet


class KeyCopyViewSet(NetBoxModelViewSet):
    queryset = models.KeyCopy.objects.all()
    serializer_class = serializers.KeyCopySerializer
    filterset_class = filtersets.KeyCopyFilterSet


class KeyIssueViewSet(NetBoxModelViewSet):
    queryset = models.KeyIssue.objects.all()
    serializer_class = serializers.KeyIssueSerializer


class TechnicalSystemViewSet(NetBoxModelViewSet):
    queryset = models.TechnicalSystem.objects.all()
    serializer_class = serializers.TechnicalSystemSerializer
    filterset_class = filtersets.TechnicalSystemFilterSet


class TechnicalAssetViewSet(NetBoxModelViewSet):
    queryset = models.TechnicalAsset.objects.all()
    serializer_class = serializers.TechnicalAssetSerializer
    filterset_class = filtersets.TechnicalAssetFilterSet


class TechnicalConnectionViewSet(NetBoxModelViewSet):
    queryset = models.TechnicalConnection.objects.all()
    serializer_class = serializers.TechnicalConnectionSerializer


class PlanElementViewSet(NetBoxModelViewSet):
    queryset = models.PlanElement.objects.all()
    serializer_class = serializers.PlanElementSerializer
