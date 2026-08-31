"""Choice sets for Solomon Issues."""

from django.utils.translation import gettext_lazy as _
from utilities.choices import ChoiceSet


class AssetTagStatusChoices(ChoiceSet):
    key = "AssetTag.status"

    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_RETIRED = "retired"

    CHOICES = [
        (STATUS_ACTIVE, _("Active"), "green"),
        (STATUS_INACTIVE, _("Inactive"), "orange"),
        (STATUS_RETIRED, _("Retired"), "red"),
    ]


class IssueStatusChoices(ChoiceSet):
    key = "Issue.status"

    STATUS_NEW = "new"
    STATUS_TRIAGED = "triaged"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_WAITING_PARTS = "waiting_parts"
    STATUS_WAITING_REPORTER = "waiting_reporter"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_REJECTED = "rejected"
    STATUS_DUPLICATE = "duplicate"

    CHOICES = [
        (STATUS_NEW, _("New"), "blue"),
        (STATUS_TRIAGED, _("Triaged"), "cyan"),
        (STATUS_IN_PROGRESS, _("In progress"), "purple"),
        (STATUS_WAITING_PARTS, _("Waiting for parts"), "orange"),
        (STATUS_WAITING_REPORTER, _("Waiting for reporter"), "yellow"),
        (STATUS_RESOLVED, _("Resolved"), "green"),
        (STATUS_CLOSED, _("Closed"), "gray"),
        (STATUS_REJECTED, _("Rejected"), "red"),
        (STATUS_DUPLICATE, _("Duplicate"), "gray"),
    ]

    #: Statuses that still require attention from the maintenance team.
    OPEN_STATUSES = (
        STATUS_NEW,
        STATUS_TRIAGED,
        STATUS_IN_PROGRESS,
        STATUS_WAITING_PARTS,
        STATUS_WAITING_REPORTER,
    )
    TERMINAL_STATUSES = (
        STATUS_RESOLVED,
        STATUS_CLOSED,
        STATUS_REJECTED,
        STATUS_DUPLICATE,
    )


class IssuePriorityChoices(ChoiceSet):
    key = "Issue.priority"

    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"

    CHOICES = [
        (PRIORITY_LOW, _("Low"), "gray"),
        (PRIORITY_NORMAL, _("Normal"), "blue"),
        (PRIORITY_HIGH, _("High"), "orange"),
        (PRIORITY_CRITICAL, _("Critical"), "red"),
    ]


class IssueSourceChoices(ChoiceSet):
    key = "Issue.source"

    SOURCE_QR = "qr"
    SOURCE_PORTAL = "portal"
    SOURCE_STAFF = "staff"
    SOURCE_EMAIL = "email"
    SOURCE_PHONE = "phone"

    CHOICES = [
        (SOURCE_QR, _("QR scan"), "teal"),
        (SOURCE_PORTAL, _("Signed-in portal"), "blue"),
        (SOURCE_STAFF, _("Staff entry"), "purple"),
        (SOURCE_EMAIL, _("E-mail"), "gray"),
        (SOURCE_PHONE, _("Phone"), "gray"),
    ]


class VisibilityChoices(ChoiceSet):
    key = "Issue.visibility"

    VISIBILITY_PUBLIC = "public"
    VISIBILITY_INTERNAL = "internal"

    CHOICES = [
        (VISIBILITY_PUBLIC, _("Public"), "green"),
        (VISIBILITY_INTERNAL, _("Internal"), "red"),
    ]


class IssueEventTypeChoices(ChoiceSet):
    key = "IssueEvent.event_type"

    EVENT_CREATED = "created"
    EVENT_STATUS_CHANGED = "status_changed"
    EVENT_PRIORITY_CHANGED = "priority_changed"
    EVENT_ASSIGNED = "assigned"
    EVENT_COMMENT = "comment"
    EVENT_ATTACHMENT = "attachment"
    EVENT_RESOLVED = "resolved"
    EVENT_CLOSED = "closed"
    EVENT_REOPENED = "reopened"
    EVENT_NOTIFICATION = "notification"
    EVENT_UPDATED = "updated"

    CHOICES = [
        (EVENT_CREATED, _("Reported"), "blue"),
        (EVENT_STATUS_CHANGED, _("Status changed"), "cyan"),
        (EVENT_PRIORITY_CHANGED, _("Priority changed"), "orange"),
        (EVENT_ASSIGNED, _("Assigned"), "purple"),
        (EVENT_COMMENT, _("Comment"), "gray"),
        (EVENT_ATTACHMENT, _("Attachment added"), "gray"),
        (EVENT_RESOLVED, _("Resolved"), "green"),
        (EVENT_CLOSED, _("Closed"), "gray"),
        (EVENT_REOPENED, _("Reopened"), "yellow"),
        (EVENT_NOTIFICATION, _("Notification sent"), "gray"),
        (EVENT_UPDATED, _("Updated"), "gray"),
    ]


class PublicIssueVisibilityChoices(ChoiceSet):
    """Controls what anonymous visitors see on a public asset tag page."""

    VISIBILITY_NONE = "none"
    VISIBILITY_OPEN = "open"
    VISIBILITY_ALL = "all"

    CHOICES = [
        (VISIBILITY_NONE, _("Hide all issues")),
        (VISIBILITY_OPEN, _("Show open issues")),
        (VISIBILITY_ALL, _("Show all issues")),
    ]
