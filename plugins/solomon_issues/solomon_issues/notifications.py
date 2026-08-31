"""Outbound e-mail notifications for Solomon Issues."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from .choices import IssueEventTypeChoices, VisibilityChoices
from .utils import get_public_base_url, get_setting, split_emails

logger = logging.getLogger("solomon_issues.notifications")

MANAGER_TEMPLATE = "solomon_issues/email/manager_notification.txt"
REPORTER_TEMPLATE = "solomon_issues/email/reporter_notification.txt"


def _from_address():
    return (
        settings.SERVER_EMAIL
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or "solomon@localhost"
    )


def _manager_recipients(issue):
    recipients = set(issue.notification_recipients())
    recipients.update(split_emails(get_setting("manager_emails")))
    if issue.reporter_email:
        recipients.discard(issue.reporter_email)
    return sorted(address for address in recipients if address)


def _reporter_recipients(issue):
    if not issue.notify_reporter:
        return []
    recipients = {
        subscriber.email for subscriber in issue.subscribers.filter(is_active=True)
    }
    if issue.reporter_email:
        recipients.add(issue.reporter_email)
    if issue.reporter_user and issue.reporter_user.email:
        recipients.add(issue.reporter_user.email)
    return sorted(address for address in recipients if address)


def _subject(issue, event_type):
    labels = {
        IssueEventTypeChoices.EVENT_CREATED: _("New problem reported"),
        IssueEventTypeChoices.EVENT_STATUS_CHANGED: _("Status updated"),
        IssueEventTypeChoices.EVENT_ASSIGNED: _("Assignment updated"),
        IssueEventTypeChoices.EVENT_COMMENT: _("New reply"),
        IssueEventTypeChoices.EVENT_RESOLVED: _("Problem resolved"),
        IssueEventTypeChoices.EVENT_CLOSED: _("Problem closed"),
        IssueEventTypeChoices.EVENT_REOPENED: _("Problem reopened"),
    }
    action = labels.get(event_type, _("Update"))
    return f"[{issue.number}] {action}: {issue.title}"


def _render_and_send(issue, recipients, template, context, event_type):
    from .models import IssueNotification

    if not recipients:
        return 0

    subject = _subject(issue, event_type)
    body = render_to_string(template, context)
    sent = 0
    for recipient in recipients:
        log = IssueNotification(
            issue=issue,
            recipient=recipient,
            subject=subject[:255],
            event_type=event_type,
        )
        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=_from_address(),
                to=[recipient],
            )
            message.send(fail_silently=False)
            log.success = True
            sent += 1
        except Exception as exc:  # noqa: BLE001 - delivery failures must not break the request
            log.success = False
            log.error = str(exc)[:2000]
            logger.warning(
                "Failed to notify %s about %s: %s", recipient, issue.number, exc
            )
        log.save()
    return sent


def send_notification(issue_pk, event_type, message="", base_url=None, comment_pk=None):
    """Deliver manager and reporter e-mails for one issue event."""
    from .models import Issue, IssueComment

    if not get_setting("notifications_enabled", True):
        return 0

    try:
        issue = Issue.objects.select_related(
            "asset_tag", "category", "assigned_to"
        ).get(pk=issue_pk)
    except Issue.DoesNotExist:
        logger.warning("Issue %s no longer exists; skipping notification", issue_pk)
        return 0

    comment = None
    if comment_pk:
        comment = IssueComment.objects.filter(pk=comment_pk).first()

    base_url = base_url or get_public_base_url()
    context = {
        "issue": issue,
        "event_type": event_type,
        "message": message,
        "comment": comment,
        "manager_url": f"{base_url}{issue.get_absolute_url()}",
        "public_url": f"{base_url}{issue.public_path}",
        "tag_url": f"{base_url}{issue.asset_tag.public_path}"
        if issue.asset_tag
        else "",
    }

    sent = _render_and_send(
        issue, _manager_recipients(issue), MANAGER_TEMPLATE, context, event_type
    )

    # Internal-only comments never reach the reporter.
    if comment is None or comment.visibility == VisibilityChoices.VISIBILITY_PUBLIC:
        sent += _render_and_send(
            issue, _reporter_recipients(issue), REPORTER_TEMPLATE, context, event_type
        )
    return sent


def notify(issue, event_type, message="", request=None, comment=None):
    """Queue (or directly send) notifications for an issue event."""
    if not get_setting("notifications_enabled", True):
        return

    base_url = get_public_base_url(request)
    kwargs = {
        "issue_pk": issue.pk,
        "event_type": event_type,
        "message": message,
        "base_url": base_url,
        "comment_pk": comment.pk if comment else None,
    }

    if get_setting("async_notifications", True):
        try:
            import django_rq

            django_rq.get_queue("default").enqueue(send_notification, **kwargs)
            return
        except Exception as exc:  # noqa: BLE001 - fall back to inline delivery
            logger.warning("Falling back to inline notification delivery: %s", exc)

    send_notification(**kwargs)
