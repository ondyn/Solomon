"""Search filters for Solomon Issues."""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from netbox.filtersets import NetBoxModelFilterSet

from . import models
from .choices import (
    AssetTagStatusChoices,
    IssuePriorityChoices,
    IssueSourceChoices,
    IssueStatusChoices,
)


class SearchFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search")
    search_fields = ()

    def search(self, queryset, name, value):
        query = Q()
        for field in self.search_fields:
            query |= Q(**{f"{field}__icontains": value})
        return queryset.filter(query).distinct()


class IssueCategoryFilterSet(SearchFilterSet):
    search_fields = ("name", "slug", "description")

    class Meta:
        model = models.IssueCategory
        fields = ("name", "slug", "is_active", "default_priority")


class AssetTagFilterSet(SearchFilterSet):
    search_fields = ("label", "code", "location_hint", "public_description")
    status = django_filters.MultipleChoiceFilter(choices=AssetTagStatusChoices)

    class Meta:
        model = models.AssetTag
        fields = ("code", "status", "category", "allow_public_reports")


class IssueFilterSet(SearchFilterSet):
    search_fields = (
        "number",
        "title",
        "description",
        "reporter_name",
        "reporter_email",
        "asset_tag__label",
        "asset_tag__code",
    )
    status = django_filters.MultipleChoiceFilter(choices=IssueStatusChoices)
    priority = django_filters.MultipleChoiceFilter(choices=IssuePriorityChoices)
    source = django_filters.MultipleChoiceFilter(choices=IssueSourceChoices)
    is_open = django_filters.BooleanFilter(
        method="filter_is_open", label=_("Open only")
    )

    class Meta:
        model = models.Issue
        fields = (
            "number",
            "status",
            "priority",
            "source",
            "category",
            "asset_tag",
            "assigned_to",
            "assigned_group",
            "is_public",
        )

    def filter_is_open(self, queryset, name, value):
        if value is None:
            return queryset
        if value:
            return queryset.filter(status__in=IssueStatusChoices.OPEN_STATUSES)
        return queryset.exclude(status__in=IssueStatusChoices.OPEN_STATUSES)
