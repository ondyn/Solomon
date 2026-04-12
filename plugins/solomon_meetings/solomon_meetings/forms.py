from django import forms

from netbox.forms import NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField

from solomon_property.models import Building, FlatOwner, PropertyOwner

from .models import (
    AgendaItem,
    Meeting,
    MeetingAttendance,
    MeetingInvitation,
    MeetingMinutes,
    MeetingType,
    Vote,
    VoteWeightStyle,
)


class MeetingTypeForm(NetBoxModelForm):
    class Meta:
        model = MeetingType
        fields = ["name", "quorum_type", "default_quorum_threshold", "tags"]


class MeetingForm(NetBoxModelForm):
    meeting_type = DynamicModelChoiceField(queryset=MeetingType.objects.all())
    buildings = DynamicModelMultipleChoiceField(queryset=Building.objects.all())

    class Meta:
        model = Meeting
        fields = [
            "meeting_type",
            "title",
            "buildings",
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
        ]
        widgets = {
            "date_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "quorum_updated_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ended_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "invitation_pdf_generated_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "invitation_published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "owner_snapshot_taken_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class AgendaItemForm(NetBoxModelForm):
    meeting = DynamicModelChoiceField(queryset=Meeting.objects.all())

    class Meta:
        model = AgendaItem
        fields = [
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
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class MeetingAttendanceForm(NetBoxModelForm):
    meeting = DynamicModelChoiceField(queryset=Meeting.objects.all())
    owner = DynamicModelChoiceField(queryset=PropertyOwner.objects.all())
    flat_owner = DynamicModelChoiceField(queryset=FlatOwner.objects.all())

    class Meta:
        model = MeetingAttendance
        fields = [
            "meeting",
            "owner",
            "flat_owner",
            "representation",
            "proxy_name",
            "arrived_at",
            "left_at",
            "tags",
        ]
        widgets = {
            "arrived_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "left_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class VoteForm(NetBoxModelForm):
    meeting = DynamicModelChoiceField(queryset=Meeting.objects.all(), required=False)
    agenda_item = DynamicModelChoiceField(queryset=AgendaItem.objects.all())
    attendance = DynamicModelChoiceField(queryset=MeetingAttendance.objects.all())

    class Meta:
        model = Vote
        fields = ["agenda_item", "attendance", "vote", "tags"]


class VoteWeightStyleForm(NetBoxModelForm):
    class Meta:
        model = VoteWeightStyle
        fields = ["voting_method", "weight_value", "label", "color", "tags"]


class MeetingMinutesForm(NetBoxModelForm):
    meeting = DynamicModelChoiceField(queryset=Meeting.objects.all())

    class Meta:
        model = MeetingMinutes
        fields = [
            "meeting",
            "content",
            "approved_by",
            "approved_at",
            "cms_published",
            "cms_published_at",
            "tags",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8}),
            "approved_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "cms_published_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class MeetingInvitationForm(NetBoxModelForm):
    meeting = DynamicModelChoiceField(queryset=Meeting.objects.all())
    owner = DynamicModelChoiceField(queryset=PropertyOwner.objects.all())

    class Meta:
        model = MeetingInvitation
        fields = ["meeting", "owner", "sent_at", "delivery_method", "confirmed", "tags"]
        widgets = {
            "sent_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
