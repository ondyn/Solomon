from django.utils.translation import gettext_lazy as _

from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms.rendering import FieldSet

from .models import AgendaItem, Meeting, MeetingAttendance, MeetingType, VoteWeightStyle


class MeetingTypeFilterForm(NetBoxModelFilterSetForm):
    model = MeetingType
    fieldsets = (FieldSet("q", "quorum_type", name=_("Filters")),)


class MeetingFilterForm(NetBoxModelFilterSetForm):
    model = Meeting
    fieldsets = (FieldSet("q", "meeting_type", "status", "phase", name=_("Filters")),)


class AgendaItemFilterForm(NetBoxModelFilterSetForm):
    model = AgendaItem
    fieldsets = (
        FieldSet("q", "meeting", "voting_method", "result", name=_("Filters")),
    )


class MeetingAttendanceFilterForm(NetBoxModelFilterSetForm):
    model = MeetingAttendance
    fieldsets = (FieldSet("meeting", "owner", "representation", name=_("Filters")),)


class VoteWeightStyleFilterForm(NetBoxModelFilterSetForm):
    model = VoteWeightStyle
    fieldsets = (
        FieldSet(
            "voting_method", "weight_value", "label", "is_current", name=_("Filters")
        ),
    )
