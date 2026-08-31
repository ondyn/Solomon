"""Tests for notification routing and delivery logging."""

from django.core import mail
from django.test import TestCase, override_settings

from solomon_issues import notifications
from solomon_issues.choices import IssueEventTypeChoices
from solomon_issues.models import AssetTag, Issue, IssueCategory, IssueSubscriber

PLUGIN_SETTINGS = {
    "solomon_issues": {
        "public_base_url": "https://solo-mon.site",
        "manager_emails": ["board@example.com"],
        "notifications_enabled": True,
        "async_notifications": False,
    }
}


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class NotificationTestCase(TestCase):
    def setUp(self):
        mail.outbox = []
        self.category = IssueCategory.objects.create(
            name="Plumbing", slug="plumbing", notify_emails="plumber@example.com"
        )
        self.tag = AssetTag.objects.create(
            label="Riser valve",
            code="NOTIFTAG01",
            category=self.category,
            notify_emails="caretaker@example.com",
        )
        self.issue = Issue.objects.create(
            asset_tag=self.tag,
            category=self.category,
            title="Leak",
            description="Water on the floor",
            reporter_email="tenant@example.com",
            reporter_name="Tenant",
        )

    def test_manager_and_reporter_are_notified(self):
        notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        recipients = {address for message in mail.outbox for address in message.to}
        self.assertEqual(
            recipients,
            {
                "board@example.com",
                "caretaker@example.com",
                "plumber@example.com",
                "tenant@example.com",
            },
        )

    def test_subject_contains_issue_number(self):
        notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        self.assertTrue(
            all(self.issue.number in message.subject for message in mail.outbox)
        )

    def test_public_base_url_setting_is_used_in_links(self):
        notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        bodies = "\n".join(message.body for message in mail.outbox)
        self.assertIn("https://solo-mon.site/plugins/issues/", bodies)

    def test_delivery_is_logged(self):
        notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        self.assertEqual(self.issue.notifications.count(), 4)
        self.assertTrue(self.issue.notifications.filter(success=True).exists())

    def test_opted_out_reporter_is_skipped(self):
        self.issue.notify_reporter = False
        self.issue.save()
        notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        recipients = {address for message in mail.outbox for address in message.to}
        self.assertNotIn("tenant@example.com", recipients)

    def test_unsubscribed_reporter_still_skipped_when_no_direct_email(self):
        IssueSubscriber.objects.filter(issue=self.issue).update(is_active=False)
        self.issue.reporter_email = ""
        self.issue.save()
        notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        recipients = {address for message in mail.outbox for address in message.to}
        self.assertNotIn("tenant@example.com", recipients)

    def test_notifications_can_be_disabled_globally(self):
        disabled = {
            "solomon_issues": {
                **PLUGIN_SETTINGS["solomon_issues"],
                "notifications_enabled": False,
            }
        }
        with override_settings(PLUGINS_CONFIG=disabled):
            notifications.notify(self.issue, IssueEventTypeChoices.EVENT_CREATED)
        self.assertEqual(mail.outbox, [])

    def test_missing_issue_is_handled(self):
        self.assertEqual(
            notifications.send_notification(
                issue_pk=999999, event_type=IssueEventTypeChoices.EVENT_CREATED
            ),
            0,
        )
