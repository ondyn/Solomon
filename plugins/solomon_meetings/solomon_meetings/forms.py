from decimal import Decimal
from fractions import Fraction

from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField

from solomon_property.models import Building, FlatOwner, PropertyOwner

from .models import (
    AgendaItem,
    MeetingAttendanceEvent,
    MeetingOwnerSnapshot,
    Meeting,
    MeetingAttendance,
    MeetingInvitation,
    MeetingMinutes,
    MeetingType,
    QUORUM_TYPE_CHOICES,
    Vote,
    VoteWeightStyle,
    quantize_weight_fraction,
)


class MeetingTypeForm(NetBoxModelForm):
    class Meta:
        model = MeetingType
        fields = [
            "name",
            "quorum_type",
            "default_quorum_threshold",
            "attendance_threshold_50",
            "attendance_threshold_two_thirds",
            "tags",
        ]


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
    weight_numerator = forms.IntegerField(
        min_value=1,
        label=_("Weight numerator"),
        help_text=_("Numerator of the ownership share fraction, e.g. 779"),
    )
    weight_denominator = forms.IntegerField(
        min_value=1,
        label=_("Weight denominator"),
        help_text=_("Denominator of the ownership share fraction, e.g. 54534"),
    )

    class Meta:
        model = VoteWeightStyle
        fields = ["voting_method", "weight_value", "label", "color", "tags"]
        widgets = {
            "weight_value": forms.HiddenInput(),
            "color": forms.TextInput(attrs={"type": "color", "style": "width:6rem;height:2.5rem;padding:0.2rem;cursor:pointer;"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.weight_value:
            numerator, denominator = self.instance.weight_fraction_pair
            self.fields["weight_numerator"].initial = numerator
            self.fields["weight_denominator"].initial = denominator

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        num = cleaned.get("weight_numerator")
        den = cleaned.get("weight_denominator")
        if num is not None and den is not None:
            cleaned["weight_value"] = quantize_weight_fraction(num, den)
            cleaned["weight_numerator"] = num
            cleaned["weight_denominator"] = den
        return cleaned


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


class MeetingAttendanceEventForm(NetBoxModelForm):
    owner_snapshot = DynamicModelChoiceField(queryset=MeetingOwnerSnapshot.objects.all())

    class Meta:
        model = MeetingAttendanceEvent
        fields = ["owner_snapshot", "event_type", "event_time", "source", "note", "tags"]
        widgets = {
            "event_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class MeetingAgendaInlineForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    presenter = forms.CharField(max_length=255, required=False)
    voting_required = forms.BooleanField(required=False, initial=True)
    voting_method = forms.ChoiceField(choices=QUORUM_TYPE_CHOICES)
    quorum_threshold = forms.DecimalField(max_digits=5, decimal_places=4, initial="0.5000")
    minimum_pass_percentage = forms.DecimalField(max_digits=5, decimal_places=4, initial="0.5000")


class MeetingExportForm(forms.Form):
    include_attendance = forms.BooleanField(required=False, initial=True)
    include_voting = forms.BooleanField(required=False, initial=True)
    include_agenda_texts = forms.BooleanField(required=False, initial=True)


class AgendaVoteBallotInputForm(forms.Form):
    label = forms.CharField(required=False)
    color = forms.CharField(required=False)
    share_value = forms.DecimalField(max_digits=12, decimal_places=6)
    issued_count = forms.IntegerField(min_value=0)
    for_count = forms.IntegerField(min_value=0, required=False)
    against_count = forms.IntegerField(min_value=0, required=False)
    abstain_count = forms.IntegerField(min_value=0, required=False)


class AgendaVoteSessionForm(forms.Form):
    rows = forms.IntegerField(min_value=0, widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()
        rows = cleaned_data.get("rows", 0)
        parsed_rows = []
        for index in range(rows):
            row_form = AgendaVoteBallotInputForm(
                {
                    "label": self.data.get(f"row-{index}-label", ""),
                    "color": self.data.get(f"row-{index}-color", ""),
                    "share_value": self.data.get(f"row-{index}-share_value"),
                    "issued_count": self.data.get(f"row-{index}-issued_count"),
                    "for_count": self.data.get(f"row-{index}-for_count"),
                    "against_count": self.data.get(f"row-{index}-against_count"),
                    "abstain_count": self.data.get(f"row-{index}-abstain_count"),
                }
            )
            if not row_form.is_valid():
                raise forms.ValidationError(row_form.errors.as_text())

            row_data = row_form.cleaned_data
            issued = row_data["issued_count"]
            values = [row_data.get("for_count"), row_data.get("against_count"), row_data.get("abstain_count")]
            provided = [value for value in values if value is not None]
            total = sum(provided)

            if total > issued:
                raise forms.ValidationError(
                    f"Row {index + 1}: vote totals cannot exceed issued ballots."
                )

            if len(provided) >= 2 and total < issued:
                missing = issued - total
                if row_data.get("for_count") is None:
                    row_data["for_count"] = missing
                elif row_data.get("against_count") is None:
                    row_data["against_count"] = missing
                elif row_data.get("abstain_count") is None:
                    row_data["abstain_count"] = missing

            row_data["for_count"] = row_data.get("for_count") or 0
            row_data["against_count"] = row_data.get("against_count") or 0
            row_data["abstain_count"] = row_data.get("abstain_count") or 0

            total_votes = row_data["for_count"] + row_data["against_count"] + row_data["abstain_count"]
            if total_votes > issued:
                raise forms.ValidationError(
                    f"Row {index + 1}: vote totals cannot exceed issued ballots."
                )

            if total_votes != issued:
                raise forms.ValidationError(
                    f"Row {index + 1}: for + against + abstain must equal issued ballots."
                )

            parsed_rows.append(row_data)

        cleaned_data["parsed_rows"] = parsed_rows
        return cleaned_data
