"""QR asset tags, issue tracking, and public reporting models for Solomon."""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from netbox.models import ChangeLoggedModel, NetBoxModel
from utilities.fields import ColorField

from .choices import (
    AssetTagStatusChoices,
    IssueEventTypeChoices,
    IssuePriorityChoices,
    IssueSourceChoices,
    IssueStatusChoices,
    VisibilityChoices,
)
from .utils import (
    build_public_url,
    generate_code,
    generate_token,
    get_setting,
    split_emails,
    validate_email_list,
)

ISSUE_NUMBER_PREFIX = "ISS"

#: Object types an asset tag may be attached to, offered in the tag form.
LINKABLE_MODELS = (
    ("solomon_property", "flat"),
    ("solomon_property", "building"),
    ("solomon_property", "buildingobject"),
    ("solomon_facilities", "buildinglevel"),
    ("solomon_facilities", "space"),
    ("solomon_facilities", "door"),
    ("solomon_facilities", "lockcylinder"),
    ("solomon_facilities", "technicalsystem"),
    ("solomon_facilities", "technicalasset"),
)


def default_label_caption():
    """The caption printed next to a QR code when a tag defines none."""
    return get_setting("default_label_caption") or _("Scan me and report a problem")


def attachment_upload_path(instance, filename):
    return f"solomon-issues/{instance.issue.number}/{filename}"


class IssueCategory(NetBoxModel):
    """A class of problem, carrying routing and SLA defaults."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    color = ColorField(default="9e9e9e", verbose_name=_("Color"))
    default_priority = models.CharField(
        max_length=20,
        choices=IssuePriorityChoices,
        default=IssuePriorityChoices.PRIORITY_NORMAL,
        verbose_name=_("Default priority"),
    )
    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="default_issue_categories",
        verbose_name=_("Default assignee"),
    )
    default_group = models.ForeignKey(
        "users.Group",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="default_issue_categories",
        verbose_name=_("Default team"),
    )
    notify_emails = models.TextField(
        blank=True,
        validators=[validate_email_list],
        verbose_name=_("Notification recipients"),
        help_text=_(
            "Comma-separated addresses notified about issues in this category."
        ),
    )
    response_sla_hours = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        verbose_name=_("Response SLA (hours)"),
    )
    resolution_sla_hours = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        verbose_name=_("Resolution SLA (hours)"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("Issue category")
        verbose_name_plural = _("Issue categories")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:solomon_issues:issuecategory", args=[self.pk])

    def get_default_priority_color(self):
        return IssuePriorityChoices.colors.get(self.default_priority)

    @property
    def notification_recipients(self):
        return split_emails(self.notify_emails)


class AssetTag(NetBoxModel):
    """A printable QR label bound to a physical item."""

    code = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        verbose_name=_("Public code"),
        help_text=_(
            "Opaque code used in the public QR URL. Generated when left blank."
        ),
    )
    label = models.CharField(max_length=200, verbose_name=_("Item name"))
    assigned_object_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        verbose_name=_("Linked object type"),
    )
    assigned_object_id = models.PositiveBigIntegerField(blank=True, null=True)
    assigned_object = GenericForeignKey(
        ct_field="assigned_object_type", fk_field="assigned_object_id"
    )
    category = models.ForeignKey(
        IssueCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="asset_tags",
        verbose_name=_("Default category"),
    )
    location_hint = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Location"),
        help_text=_(
            "Where the label is physically placed, for example 'Entrance A, basement'."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=AssetTagStatusChoices,
        default=AssetTagStatusChoices.STATUS_ACTIVE,
        verbose_name=_("Status"),
    )
    print_instructions = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Label caption"),
        help_text=_(
            "Text printed next to the QR code, for example 'Scan me and report a problem'."
        ),
    )
    public_description = models.TextField(
        blank=True,
        verbose_name=_("Public description"),
        help_text=_("Shown to anyone who scans the code."),
    )
    allow_public_reports = models.BooleanField(
        default=True,
        verbose_name=_("Allow anonymous reports"),
    )
    show_open_issues = models.BooleanField(
        default=True,
        verbose_name=_("Show open issues publicly"),
    )
    require_reporter_contact = models.BooleanField(
        default=False,
        verbose_name=_("Require reporter contact"),
        help_text=_("Anonymous reporters must supply an e-mail address."),
    )
    default_priority = models.CharField(
        max_length=20,
        choices=IssuePriorityChoices,
        default=IssuePriorityChoices.PRIORITY_NORMAL,
        verbose_name=_("Default priority"),
    )
    notify_emails = models.TextField(
        blank=True,
        validators=[validate_email_list],
        verbose_name=_("Notification recipients"),
        help_text=_(
            "Comma-separated addresses notified in addition to the category recipients."
        ),
    )
    assigned_group = models.ForeignKey(
        "users.Group",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="asset_tags",
        verbose_name=_("Responsible team"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Internal notes"))
    printed_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Last printed")
    )

    class Meta:
        ordering = ["label", "code"]
        verbose_name = _("Asset tag")
        verbose_name_plural = _("Asset tags")
        indexes = [
            models.Index(fields=["assigned_object_type", "assigned_object_id"]),
        ]
        permissions = (("print_assettag", "Can render and print QR labels"),)

    def __str__(self):
        return f"{self.label} ({self.code})" if self.code else self.label

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_code():
        for _attempt in range(20):
            candidate = generate_code()
            if not AssetTag.objects.filter(code=candidate).exists():
                return candidate
        raise RuntimeError("Unable to allocate a unique asset tag code")

    def get_absolute_url(self):
        return reverse("plugins:solomon_issues:assettag", args=[self.pk])

    def get_status_color(self):
        return AssetTagStatusChoices.colors.get(self.status)

    def get_default_priority_color(self):
        return IssuePriorityChoices.colors.get(self.default_priority)

    @property
    def public_path(self):
        return reverse("plugins:solomon_issues:public_tag", args=[self.code])

    def public_url(self, request=None):
        return build_public_url(self.public_path, request=request)

    @property
    def label_caption(self):
        return self.print_instructions or default_label_caption()

    @property
    def is_reportable(self):
        return (
            self.status == AssetTagStatusChoices.STATUS_ACTIVE
            and self.allow_public_reports
        )

    @property
    def notification_recipients(self):
        recipients = split_emails(self.notify_emails)
        if self.category:
            recipients += self.category.notification_recipients
        return sorted(set(recipients))

    def open_issues(self):
        return self.issues.filter(status__in=IssueStatusChoices.OPEN_STATUSES)


class Issue(NetBoxModel):
    """A reported problem on a tagged item."""

    number = models.CharField(
        max_length=20, unique=True, blank=True, verbose_name=_("Number")
    )
    asset_tag = models.ForeignKey(
        AssetTag,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="issues",
        verbose_name=_("Asset tag"),
    )
    assigned_object_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        verbose_name=_("Linked object type"),
    )
    assigned_object_id = models.PositiveBigIntegerField(blank=True, null=True)
    assigned_object = GenericForeignKey(
        ct_field="assigned_object_type", fk_field="assigned_object_id"
    )
    category = models.ForeignKey(
        IssueCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="issues",
        verbose_name=_("Category"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Summary"))
    description = models.TextField(verbose_name=_("Description"))
    status = models.CharField(
        max_length=20,
        choices=IssueStatusChoices,
        default=IssueStatusChoices.STATUS_NEW,
        verbose_name=_("Status"),
    )
    priority = models.CharField(
        max_length=20,
        choices=IssuePriorityChoices,
        default=IssuePriorityChoices.PRIORITY_NORMAL,
        verbose_name=_("Priority"),
    )
    source = models.CharField(
        max_length=20,
        choices=IssueSourceChoices,
        default=IssueSourceChoices.SOURCE_QR,
        verbose_name=_("Source"),
    )
    reporter_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reported_issues",
        verbose_name=_("Reporting user"),
    )
    reporter_name = models.CharField(
        max_length=120, blank=True, verbose_name=_("Reporter name")
    )
    reporter_email = models.EmailField(blank=True, verbose_name=_("Reporter e-mail"))
    reporter_phone = models.CharField(
        max_length=40, blank=True, verbose_name=_("Reporter phone")
    )
    access_token = models.CharField(
        max_length=64, unique=True, blank=True, verbose_name=_("Access token")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_issues",
        verbose_name=_("Assigned to"),
    )
    assigned_group = models.ForeignKey(
        "users.Group",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_issues",
        verbose_name=_("Assigned team"),
    )
    due_date = models.DateField(blank=True, null=True, verbose_name=_("Due date"))
    acknowledged_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Acknowledged")
    )
    resolved_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Resolved")
    )
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Closed"))
    resolution = models.TextField(blank=True, verbose_name=_("Resolution"))
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="duplicates",
        verbose_name=_("Duplicate of"),
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_("Visible on public page"),
        help_text=_("Uncheck to hide this issue from anyone scanning the QR code."),
    )
    notify_reporter = models.BooleanField(
        default=True, verbose_name=_("Notify reporter")
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assigned_object_type", "assigned_object_id"]),
        ]
        permissions = (
            ("manage_issue", "Can change issue status, assignment and resolution"),
            ("view_internal_issue", "Can view internal notes on issues"),
            (
                "report_issue",
                "Can report problems even when anonymous reporting is disabled",
            ),
        )

    def __str__(self):
        return f"{self.number}: {self.title}" if self.number else self.title

    def clean(self):
        super().clean()
        if self.duplicate_of_id and self.duplicate_of_id == self.pk:
            raise ValidationError(
                {"duplicate_of": _("An issue cannot be a duplicate of itself.")}
            )

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        if not self.access_token:
            self.access_token = generate_token()
        if self.asset_tag and not self.assigned_object_id:
            self.assigned_object_type = self.asset_tag.assigned_object_type
            self.assigned_object_id = self.asset_tag.assigned_object_id
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        with transaction.atomic():
            last = (
                Issue.objects.select_for_update()
                .filter(number__startswith=f"{ISSUE_NUMBER_PREFIX}-")
                .aggregate(Max("number"))["number__max"]
            )
        sequence = 0
        if last:
            try:
                sequence = int(last.split("-")[-1])
            except (ValueError, IndexError):
                sequence = 0
        return f"{ISSUE_NUMBER_PREFIX}-{sequence + 1:06d}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_issues:issue", args=[self.pk])

    def get_status_color(self):
        return IssueStatusChoices.colors.get(self.status)

    def get_priority_color(self):
        return IssuePriorityChoices.colors.get(self.priority)

    def get_source_color(self):
        return IssueSourceChoices.colors.get(self.source)

    @property
    def public_path(self):
        return reverse("plugins:solomon_issues:public_issue", args=[self.access_token])

    def public_url(self, request=None):
        return build_public_url(self.public_path, request=request)

    def manager_url(self, request=None):
        return build_public_url(self.get_absolute_url(), request=request)

    @property
    def is_open(self):
        return self.status in IssueStatusChoices.OPEN_STATUSES

    @property
    def reporter_display(self):
        if self.reporter_user:
            return self.reporter_user.get_full_name() or self.reporter_user.username
        return self.reporter_name or _("Anonymous")

    def public_events(self):
        return self.events.filter(visibility=VisibilityChoices.VISIBILITY_PUBLIC)

    def public_comments(self):
        return self.comments.filter(visibility=VisibilityChoices.VISIBILITY_PUBLIC)

    def notification_recipients(self):
        """Addresses of everyone responsible for acting on this issue."""
        recipients = []
        if self.asset_tag:
            recipients += self.asset_tag.notification_recipients
        elif self.category:
            recipients += self.category.notification_recipients
        if self.assigned_to and self.assigned_to.email:
            recipients.append(self.assigned_to.email)
        return sorted({address for address in recipients if address})

    def log_event(
        self,
        event_type,
        message="",
        user=None,
        actor_name="",
        visibility=VisibilityChoices.VISIBILITY_PUBLIC,
        data=None,
    ):
        return IssueEvent.objects.create(
            issue=self,
            event_type=event_type,
            message=message,
            user=user if user and user.is_authenticated else None,
            actor_name=actor_name,
            visibility=visibility,
            data=data or {},
        )

    def apply_status(self, new_status, user=None, note=""):
        """Move the issue to a new status and keep the derived timestamps in sync."""
        previous = self.status
        if previous == new_status:
            return None
        self.status = new_status
        now = timezone.now()
        if new_status == IssueStatusChoices.STATUS_RESOLVED:
            self.resolved_at = now
        elif new_status == IssueStatusChoices.STATUS_CLOSED:
            self.closed_at = now
            if not self.resolved_at:
                self.resolved_at = now
        elif new_status in IssueStatusChoices.OPEN_STATUSES:
            self.resolved_at = None
            self.closed_at = None
        if new_status != IssueStatusChoices.STATUS_NEW and self.acknowledged_at is None:
            self.acknowledged_at = now
        self.save()

        if previous in IssueStatusChoices.TERMINAL_STATUSES and self.is_open:
            event_type = IssueEventTypeChoices.EVENT_REOPENED
        elif new_status == IssueStatusChoices.STATUS_RESOLVED:
            event_type = IssueEventTypeChoices.EVENT_RESOLVED
        elif new_status == IssueStatusChoices.STATUS_CLOSED:
            event_type = IssueEventTypeChoices.EVENT_CLOSED
        else:
            event_type = IssueEventTypeChoices.EVENT_STATUS_CHANGED

        return self.log_event(
            event_type,
            message=note,
            user=user,
            data={"from": previous, "to": new_status},
        )


class IssueComment(ChangeLoggedModel):
    """A reply on an issue, either visible to the reporter or internal only."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Issue"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="issue_comments",
        verbose_name=_("Author"),
    )
    author_name = models.CharField(
        max_length=120, blank=True, verbose_name=_("Author name")
    )
    from_reporter = models.BooleanField(
        default=False, verbose_name=_("Posted by the reporter")
    )
    visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices,
        default=VisibilityChoices.VISIBILITY_PUBLIC,
        verbose_name=_("Visibility"),
    )
    body = models.TextField(verbose_name=_("Message"))

    class Meta:
        ordering = ["created", "pk"]
        verbose_name = _("Issue comment")
        verbose_name_plural = _("Issue comments")

    def __str__(self):
        return f"{self.issue.number} - {self.get_visibility_display()}"

    def get_absolute_url(self):
        return f"{self.issue.get_absolute_url()}#comment-{self.pk}"

    def get_visibility_color(self):
        return VisibilityChoices.colors.get(self.visibility)

    @property
    def display_author(self):
        if self.author:
            return self.author.get_full_name() or self.author.username
        return self.author_name or _("Anonymous")


class IssueAttachment(ChangeLoggedModel):
    """A photo or document attached to an issue."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Issue"),
    )
    file = models.FileField(upload_to=attachment_upload_path, verbose_name=_("File"))
    caption = models.CharField(max_length=200, blank=True, verbose_name=_("Caption"))
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="issue_attachments",
        verbose_name=_("Uploaded by"),
    )
    uploader_name = models.CharField(
        max_length=120, blank=True, verbose_name=_("Uploader name")
    )
    is_public = models.BooleanField(default=True, verbose_name=_("Public"))

    class Meta:
        ordering = ["created", "pk"]
        verbose_name = _("Issue attachment")
        verbose_name_plural = _("Issue attachments")

    def __str__(self):
        return self.caption or self.file.name

    def get_absolute_url(self):
        return self.issue.get_absolute_url()


class IssueEvent(models.Model):
    """An immutable timeline entry describing what happened to an issue."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Issue"),
    )
    event_type = models.CharField(
        max_length=30, choices=IssueEventTypeChoices, verbose_name=_("Event")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="issue_events",
        verbose_name=_("User"),
    )
    actor_name = models.CharField(
        max_length=120, blank=True, verbose_name=_("Actor name")
    )
    visibility = models.CharField(
        max_length=20,
        choices=VisibilityChoices,
        default=VisibilityChoices.VISIBILITY_PUBLIC,
        verbose_name=_("Visibility"),
    )
    message = models.TextField(blank=True, verbose_name=_("Message"))
    data = models.JSONField(default=dict, blank=True, verbose_name=_("Details"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))

    objects = models.Manager()

    class Meta:
        ordering = ["created", "pk"]
        verbose_name = _("Issue event")
        verbose_name_plural = _("Issue events")

    def __str__(self):
        return f"{self.issue_id} {self.event_type}"

    def get_event_type_color(self):
        return IssueEventTypeChoices.colors.get(self.event_type)

    @property
    def display_actor(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.actor_name or _("System")


class IssueSubscriber(models.Model):
    """An e-mail address following an issue."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name=_("Issue"),
    )
    email = models.EmailField(verbose_name=_("E-mail"))
    name = models.CharField(max_length=120, blank=True, verbose_name=_("Name"))
    is_reporter = models.BooleanField(default=False, verbose_name=_("Reporter"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    token = models.CharField(max_length=64, unique=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        ordering = ["email"]
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "email"], name="solomon_issues_subscriber_unique"
            )
        ]
        verbose_name = _("Issue subscriber")
        verbose_name_plural = _("Issue subscribers")

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = generate_token()
        super().save(*args, **kwargs)

    def unsubscribe_path(self):
        return reverse("plugins:solomon_issues:public_unsubscribe", args=[self.token])


class IssueNotification(models.Model):
    """Delivery log for outbound issue e-mails."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Issue"),
    )
    recipient = models.EmailField(verbose_name=_("Recipient"))
    subject = models.CharField(max_length=255, verbose_name=_("Subject"))
    event_type = models.CharField(max_length=30, blank=True, verbose_name=_("Trigger"))
    success = models.BooleanField(default=False, verbose_name=_("Delivered"))
    error = models.TextField(blank=True, verbose_name=_("Error"))
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Sent"))

    objects = models.Manager()

    class Meta:
        ordering = ["-sent_at", "pk"]
        verbose_name = _("Issue notification")
        verbose_name_plural = _("Issue notifications")

    def __str__(self):
        return f"{self.recipient} <- {self.subject}"
