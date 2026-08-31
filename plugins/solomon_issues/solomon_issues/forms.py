"""Forms for Solomon Issues, covering both staff and public entry points."""

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelForm
from users.models import Group, User
from utilities.forms.fields import (
    ContentTypeChoiceField,
    DynamicModelChoiceField,
)
from utilities.forms.utils import get_field_value
from utilities.forms.widgets import DatePicker, HTMXSelect

from . import models
from .choices import IssuePriorityChoices, IssueStatusChoices, VisibilityChoices
from .utils import get_setting


def linkable_object_types():
    """Content types an asset tag may be attached to."""
    query = Q()
    for app_label, model in models.LINKABLE_MODELS:
        query |= Q(app_label=app_label, model=model)
    return ContentType.objects.filter(query)


def _apply_bootstrap(form):
    """Public pages render fields manually, so widgets need their classes here."""
    for name, field in form.fields.items():
        if name == "website":
            continue
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(widget, forms.Select):
            css = "form-select"
        elif isinstance(widget, forms.ClearableFileInput):
            css = "form-control"
        else:
            css = "form-control"
        widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class IssueCategoryForm(NetBoxModelForm):
    default_assignee = DynamicModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_("Default assignee"),
    )
    default_group = DynamicModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label=_("Default team"),
    )

    class Meta:
        model = models.IssueCategory
        fields = (
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
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notify_emails": forms.Textarea(attrs={"rows": 2}),
        }


class AssetTagForm(NetBoxModelForm):
    category = DynamicModelChoiceField(
        queryset=models.IssueCategory.objects.all(),
        required=False,
        label=_("Default category"),
    )
    assigned_group = DynamicModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label=_("Responsible team"),
    )
    assigned_object_type = ContentTypeChoiceField(
        queryset=linkable_object_types(),
        widget=HTMXSelect(),
        required=False,
        label=_("Linked object type"),
    )
    assigned_object = DynamicModelChoiceField(
        queryset=models.AssetTag.objects.none(),
        required=False,
        disabled=True,
        selector=True,
        label=_("Linked object"),
        help_text=_("Choose a type first, then pick the item it is attached to."),
    )

    class Meta:
        model = models.AssetTag
        fields = (
            "label",
            "code",
            "status",
            "category",
            "location_hint",
            "assigned_object_type",
            "assigned_group",
            "default_priority",
            "print_instructions",
            "public_description",
            "allow_public_reports",
            "show_open_issues",
            "require_reporter_contact",
            "notify_emails",
            "notes",
            "tags",
        )
        widgets = {
            "public_description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "notify_emails": forms.Textarea(attrs={"rows": 2}),
        }
        help_texts = {
            "code": _("Leave blank to generate a new code automatically."),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance is not None and instance.assigned_object:
            initial = kwargs.get("initial", {})
            initial.setdefault("assigned_object", instance.assigned_object)
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)
        self.fields["print_instructions"].initial = models.default_label_caption()
        self._bind_assigned_object_field()

    def _bind_assigned_object_field(self):
        """Point the object selector at the model chosen in assigned_object_type."""
        field = self.fields["assigned_object"]
        type_id = get_field_value(self, "assigned_object_type")
        if not type_id:
            self.initial["assigned_object"] = None
            return
        try:
            content_type = ContentType.objects.get(pk=type_id)
        except (ContentType.DoesNotExist, ObjectDoesNotExist, ValueError):
            return
        model = content_type.model_class()
        if model is None:
            return
        field.queryset = model.objects.all()
        field.widget.attrs["selector"] = model._meta.label_lower
        field.disabled = False
        field.label = model._meta.verbose_name.capitalize()
        if self.instance.pk and str(type_id) != str(
            self.instance.assigned_object_type_id
        ):
            self.initial["assigned_object"] = None

    def clean(self):
        super().clean()
        content_type = self.cleaned_data.get("assigned_object_type")
        obj = self.cleaned_data.get("assigned_object")
        if content_type and not obj:
            self.add_error(
                "assigned_object",
                _("Select a %(model)s or clear the type.")
                % {"model": content_type.model_class()._meta.verbose_name},
            )
            # Keep the generic FK pair consistent so model validation stays quiet.
            self.cleaned_data["assigned_object_type"] = None
            content_type = None
        self.instance.assigned_object_id = obj.pk if obj and content_type else None
        return self.cleaned_data


class IssueForm(NetBoxModelForm):
    asset_tag = DynamicModelChoiceField(
        queryset=models.AssetTag.objects.all(), required=False, label=_("Asset tag")
    )
    category = DynamicModelChoiceField(
        queryset=models.IssueCategory.objects.all(),
        required=False,
        label=_("Category"),
    )
    assigned_to = DynamicModelChoiceField(
        queryset=User.objects.all(), required=False, label=_("Assigned to")
    )
    assigned_group = DynamicModelChoiceField(
        queryset=Group.objects.all(), required=False, label=_("Assigned team")
    )
    duplicate_of = DynamicModelChoiceField(
        queryset=models.Issue.objects.all(), required=False, label=_("Duplicate of")
    )

    class Meta:
        model = models.Issue
        fields = (
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
            "duplicate_of",
            "resolution",
            "is_public",
            "notify_reporter",
            "tags",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "resolution": forms.Textarea(attrs={"rows": 3}),
            "due_date": DatePicker(),
        }


class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = models.IssueComment
        fields = ("visibility", "body")
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}
        labels = {"body": _("Message")}


class IssueStatusForm(forms.Form):
    """Quick status change with an optional note pushed to the timeline."""

    status = forms.ChoiceField(choices=IssueStatusChoices, label=_("New status"))
    priority = forms.ChoiceField(
        choices=IssuePriorityChoices, required=False, label=_("Priority")
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False, label=_("Assign to")
    )
    resolution = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Resolution or note"),
    )
    notify = forms.BooleanField(
        required=False, initial=True, label=_("Send notifications")
    )


class IssueAttachmentForm(forms.ModelForm):
    class Meta:
        model = models.IssueAttachment
        fields = ("file", "caption", "is_public")


class PublicIssueReportForm(forms.Form):
    """The form shown to anyone who scanned an asset tag QR code."""

    title = forms.CharField(
        max_length=200,
        label=_("What is wrong?"),
        widget=forms.TextInput(attrs={"placeholder": _("Short summary")}),
    )
    description = forms.CharField(
        label=_("Describe the problem"),
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    priority = forms.ChoiceField(
        choices=IssuePriorityChoices,
        initial=IssuePriorityChoices.PRIORITY_NORMAL,
        label=_("Urgency"),
    )
    category = forms.ModelChoiceField(
        queryset=models.IssueCategory.objects.filter(is_active=True),
        required=False,
        label=_("Category"),
    )
    reporter_name = forms.CharField(
        max_length=120, required=False, label=_("Your name")
    )
    reporter_email = forms.EmailField(required=False, label=_("Your e-mail"))
    reporter_phone = forms.CharField(
        max_length=40, required=False, label=_("Your phone")
    )
    attachment = forms.FileField(required=False, label=_("Photo or document"))
    # Bots fill every field; humans never see this one.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
        label=_("Leave this field empty"),
    )

    def __init__(self, *args, asset_tag=None, **kwargs):
        self.asset_tag = asset_tag
        super().__init__(*args, **kwargs)
        if asset_tag is not None:
            self.fields["priority"].initial = asset_tag.default_priority
            if asset_tag.category_id:
                self.fields["category"].initial = asset_tag.category_id
        if not get_setting("attachments_enabled", True):
            self.fields.pop("attachment")
        _apply_bootstrap(self)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError(_("Submission rejected."))
        return ""

    def clean_reporter_email(self):
        email = self.cleaned_data.get("reporter_email", "")
        requires_contact = get_setting("require_reporter_email", False) or (
            self.asset_tag is not None and self.asset_tag.require_reporter_contact
        )
        if requires_contact and not email:
            raise forms.ValidationError(
                _("An e-mail address is required so we can reply to you.")
            )
        return email

    def clean_attachment(self):
        upload = self.cleaned_data.get("attachment")
        if not upload:
            return upload
        limit = int(get_setting("max_attachment_size_mb", 10)) * 1024 * 1024
        if upload.size > limit:
            raise forms.ValidationError(
                _("The file is larger than the %(limit)s MB limit.")
                % {"limit": get_setting("max_attachment_size_mb", 10)}
            )
        return upload


class PublicIssueReplyForm(forms.Form):
    """Reporter reply posted from the tokenised public issue page."""

    body = forms.CharField(
        label=_("Add information"), widget=forms.Textarea(attrs={"rows": 4})
    )
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
        label=_("Leave this field empty"),
    )

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError(_("Submission rejected."))
        return ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)

    def as_comment_kwargs(self, issue):
        return {
            "issue": issue,
            "body": self.cleaned_data["body"],
            "visibility": VisibilityChoices.VISIBILITY_PUBLIC,
            "from_reporter": True,
            "author_name": issue.reporter_name,
        }
