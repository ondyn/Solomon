from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer

from solomon_property.api.serializers import FlatOwnerSerializer, PropertyOwnerSerializer

from solomon_meetings.models import (
    AgendaItem,
    Meeting,
    MeetingAttendance,
    MeetingInvitation,
    MeetingMinutes,
    MeetingType,
    Vote,
    VoteWeightStyle,
)


class MeetingTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:meetingtype-detail"
    )

    class Meta:
        model = MeetingType
        fields = [
            "id",
            "url",
            "display",
            "name",
            "quorum_type",
            "default_quorum_threshold",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name"]


class MeetingSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:meeting-detail"
    )
    meeting_type = MeetingTypeSerializer(nested=True)

    class Meta:
        model = Meeting
        fields = [
            "id",
            "url",
            "display",
            "meeting_type",
            "title",
            "date_time",
            "location",
            "status",
            "phase",
            "quorum_threshold",
            "quorum_achieved",
            "quorum_updated_at",
            "started_at",
            "ended_at",
            "invitation_pdf_generated_at",
            "invitation_published_at",
            "owner_snapshot_taken_at",
            "moderator",
            "note",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "title", "status"]


class AgendaItemSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:agendaitem-detail"
    )
    meeting = MeetingSerializer(nested=True)

    class Meta:
        model = AgendaItem
        fields = [
            "id",
            "url",
            "display",
            "meeting",
            "order",
            "title",
            "description",
            "presenter",
            "voting_required",
            "voting_method",
            "quorum_threshold",
            "minimum_pass_percentage",
            "result",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "order", "title"]


class MeetingAttendanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:meetingattendance-detail"
    )
    owner = PropertyOwnerSerializer(nested=True)
    flat_owner = FlatOwnerSerializer(nested=True)

    class Meta:
        model = MeetingAttendance
        fields = [
            "id",
            "url",
            "display",
            "meeting",
            "owner",
            "flat_owner",
            "representation",
            "proxy_name",
            "arrived_at",
            "left_at",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "representation"]


class VoteSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:vote-detail"
    )
    agenda_item = AgendaItemSerializer(nested=True)
    attendance = MeetingAttendanceSerializer(nested=True)

    class Meta:
        model = Vote
        fields = [
            "id",
            "url",
            "display",
            "agenda_item",
            "attendance",
            "vote",
            "vote_weight",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "vote", "vote_weight"]


class VoteWeightStyleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:voteweightstyle-detail"
    )

    class Meta:
        model = VoteWeightStyle
        fields = [
            "id",
            "url",
            "display",
            "voting_method",
            "weight_value",
            "label",
            "color",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "label", "weight_value"]


class MeetingMinutesSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:meetingminutes-detail"
    )
    meeting = MeetingSerializer(nested=True)

    class Meta:
        model = MeetingMinutes
        fields = [
            "id",
            "url",
            "display",
            "meeting",
            "content",
            "approved_by",
            "approved_at",
            "cms_published",
            "cms_published_at",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "cms_published"]


class MeetingInvitationSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_meetings-api:meetinginvitation-detail"
    )
    owner = PropertyOwnerSerializer(nested=True)

    class Meta:
        model = MeetingInvitation
        fields = [
            "id",
            "url",
            "display",
            "meeting",
            "owner",
            "sent_at",
            "delivery_method",
            "confirmed",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "delivery_method", "confirmed"]
