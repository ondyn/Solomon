"""Tables for Solomon Issues list and detail views."""

import django_tables2 as tables
from django.utils.translation import gettext_lazy as _
from netbox.tables import NetBoxTable, columns

from . import models


class IssueCategoryTable(NetBoxTable):
    name = tables.Column(linkify=True)
    color = columns.ColorColumn()
    default_priority = columns.ChoiceFieldColumn()
    is_active = columns.BooleanColumn()
    issue_count = tables.Column(verbose_name=_("Issues"))

    class Meta(NetBoxTable.Meta):
        model = models.IssueCategory
        fields = (
            "pk",
            "name",
            "slug",
            "color",
            "default_priority",
            "default_assignee",
            "default_group",
            "response_sla_hours",
            "resolution_sla_hours",
            "is_active",
            "issue_count",
            "actions",
        )
        default_columns = (
            "name",
            "color",
            "default_priority",
            "default_assignee",
            "is_active",
            "issue_count",
        )


class AssetTagTable(NetBoxTable):
    label = tables.Column(linkify=True)
    code = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    category = tables.Column(linkify=True)
    open_issue_count = tables.Column(verbose_name=_("Open issues"))
    allow_public_reports = columns.BooleanColumn(verbose_name=_("Public reports"))

    class Meta(NetBoxTable.Meta):
        model = models.AssetTag
        fields = (
            "pk",
            "label",
            "code",
            "status",
            "category",
            "location_hint",
            "assigned_group",
            "default_priority",
            "allow_public_reports",
            "open_issue_count",
            "printed_at",
            "actions",
        )
        default_columns = (
            "label",
            "code",
            "status",
            "category",
            "location_hint",
            "open_issue_count",
        )


class IssueTable(NetBoxTable):
    number = tables.Column(linkify=True)
    title = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    priority = columns.ChoiceFieldColumn()
    source = columns.ChoiceFieldColumn()
    asset_tag = tables.Column(linkify=True)
    category = tables.Column(linkify=True)
    created = columns.DateTimeColumn()

    class Meta(NetBoxTable.Meta):
        model = models.Issue
        fields = (
            "pk",
            "number",
            "title",
            "status",
            "priority",
            "source",
            "asset_tag",
            "category",
            "reporter_name",
            "reporter_email",
            "assigned_to",
            "assigned_group",
            "due_date",
            "created",
            "resolved_at",
            "closed_at",
            "actions",
        )
        default_columns = (
            "number",
            "title",
            "status",
            "priority",
            "asset_tag",
            "assigned_to",
            "created",
        )


class IssueCommentTable(NetBoxTable):
    issue = tables.Column(linkify=True)
    visibility = columns.ChoiceFieldColumn()
    created = columns.DateTimeColumn()

    class Meta(NetBoxTable.Meta):
        model = models.IssueComment
        fields = ("pk", "issue", "author", "visibility", "created", "actions")
        default_columns = ("issue", "author", "visibility", "created")


class IssueNotificationTable(tables.Table):
    issue = tables.Column(linkify=True, verbose_name=_("Issue"))
    recipient = tables.Column(verbose_name=_("Recipient"))
    subject = tables.Column(verbose_name=_("Subject"))
    success = tables.BooleanColumn(verbose_name=_("Delivered"))
    sent_at = tables.DateTimeColumn(verbose_name=_("Sent"))

    class Meta:
        model = models.IssueNotification
        fields = ("issue", "recipient", "subject", "event_type", "success", "sent_at")
        attrs = {"class": "table table-hover object-list"}
