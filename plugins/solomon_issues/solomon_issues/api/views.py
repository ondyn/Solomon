from netbox.api.viewsets import NetBoxModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet

from .. import filtersets, models
from . import serializers


class IssueCategoryViewSet(NetBoxModelViewSet):
    queryset = models.IssueCategory.objects.all()
    serializer_class = serializers.IssueCategorySerializer
    filterset_class = filtersets.IssueCategoryFilterSet


class AssetTagViewSet(NetBoxModelViewSet):
    queryset = models.AssetTag.objects.all()
    serializer_class = serializers.AssetTagSerializer
    filterset_class = filtersets.AssetTagFilterSet


class IssueViewSet(NetBoxModelViewSet):
    queryset = models.Issue.objects.all()
    serializer_class = serializers.IssueSerializer
    filterset_class = filtersets.IssueFilterSet


class IssueCommentViewSet(NetBoxModelViewSet):
    queryset = models.IssueComment.objects.all()
    serializer_class = serializers.IssueCommentSerializer


class IssueEventViewSet(ReadOnlyModelViewSet):
    queryset = models.IssueEvent.objects.all()
    serializer_class = serializers.IssueEventSerializer
