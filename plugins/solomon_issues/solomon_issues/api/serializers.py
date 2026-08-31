from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from .. import models


class IssuesSerializer(NetBoxModelSerializer):
    serializer_url_name = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.serializer_url_name:
            cls._declared_fields["url"] = serializers.HyperlinkedIdentityField(
                view_name=f"plugins-api:solomon_issues-api:{cls.serializer_url_name}-detail"
            )


class IssueCategorySerializer(IssuesSerializer):
    serializer_url_name = "issuecategory"

    class Meta:
        model = models.IssueCategory
        fields = (
            "id",
            "url",
            "display",
            "name",
            "slug",
            "description",
            "color",
            "default_priority",
            "default_assignee",
            "default_group",
            "notify_emails",
            "response_sla_hours",
            "resolution_sla_hours",
            "is_active",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class AssetTagSerializer(IssuesSerializer):
    serializer_url_name = "assettag"
    public_url = serializers.SerializerMethodField()

    class Meta:
        model = models.AssetTag
        fields = (
            "id",
            "url",
            "display",
            "code",
            "label",
            "status",
            "category",
            "location_hint",
            "assigned_object_type",
            "assigned_object_id",
            "assigned_group",
            "default_priority",
            "print_instructions",
            "public_description",
            "allow_public_reports",
            "show_open_issues",
            "require_reporter_contact",
            "notify_emails",
            "notes",
            "printed_at",
            "public_url",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        read_only_fields = ("public_url",)

    def get_public_url(self, obj):
        return obj.public_url(self.context.get("request"))


class IssueSerializer(IssuesSerializer):
    serializer_url_name = "issue"

    class Meta:
        model = models.Issue
        fields = (
            "id",
            "url",
            "display",
            "number",
            "asset_tag",
            "category",
            "title",
            "description",
            "status",
            "priority",
            "source",
            "reporter_name",
            "reporter_email",
            "reporter_phone",
            "assigned_to",
            "assigned_group",
            "due_date",
            "acknowledged_at",
            "resolved_at",
            "closed_at",
            "resolution",
            "duplicate_of",
            "is_public",
            "notify_reporter",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
        read_only_fields = ("number",)


class IssueCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueComment
        fields = (
            "id",
            "issue",
            "author",
            "author_name",
            "from_reporter",
            "visibility",
            "body",
            "created",
            "last_updated",
        )


class IssueEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueEvent
        fields = (
            "id",
            "issue",
            "event_type",
            "user",
            "actor_name",
            "visibility",
            "message",
            "data",
            "created",
        )
        read_only_fields = fields
