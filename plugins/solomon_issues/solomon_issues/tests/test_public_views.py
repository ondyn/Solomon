"""Tests for the anonymous QR reporting flow."""

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from solomon_issues.choices import IssueStatusChoices
from solomon_issues.models import AssetTag, Issue, IssueCategory, IssueSubscriber

PLUGIN_SETTINGS = {
    "solomon_issues": {
        "public_base_url": "",
        "allow_anonymous_reports": True,
        "public_issue_visibility": "open",
        "manager_emails": ["manager@example.com"],
        "notifications_enabled": True,
        "async_notifications": False,
        "qr_error_correction": "M",
        "rate_limit_reports_per_hour": 10,
        "attachments_enabled": True,
        "max_attachment_size_mb": 10,
        "require_reporter_email": False,
    }
}


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS, LOGIN_REQUIRED=True)
class PublicTagViewTestCase(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox = []
        self.category = IssueCategory.objects.create(
            name="Plumbing", slug="plumbing", notify_emails="plumber@example.com"
        )
        self.tag = AssetTag.objects.create(
            label="Riser valve B2",
            code="TESTTAG001",
            category=self.category,
            location_hint="Entrance A, basement",
            print_instructions="Scan me and report a problem",
        )

    def report_url(self):
        return reverse(
            "plugins:solomon_issues:public_report", kwargs={"code": self.tag.code}
        )

    def test_tag_page_is_reachable_without_login(self):
        url = reverse(
            "plugins:solomon_issues:public_tag", kwargs={"code": self.tag.code}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Riser valve B2")
        self.assertContains(response, "Scan me and report a problem")

    def test_unknown_code_returns_404(self):
        url = reverse(
            "plugins:solomon_issues:public_tag", kwargs={"code": "NOPETHISONE"}
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_retired_tag_returns_404(self):
        self.tag.status = "retired"
        self.tag.save()
        url = reverse(
            "plugins:solomon_issues:public_tag", kwargs={"code": self.tag.code}
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_report_creates_issue_and_notifies(self):
        response = self.client.post(
            self.report_url(),
            {
                "title": "Valve is leaking",
                "description": "Water drips onto the floor.",
                "priority": "high",
                "reporter_name": "Jan Novak",
                "reporter_email": "jan@example.com",
                "website": "",
            },
        )
        issue = Issue.objects.get()
        self.assertRedirects(
            response,
            reverse(
                "plugins:solomon_issues:public_issue",
                kwargs={"token": issue.access_token},
            ),
        )
        self.assertEqual(issue.asset_tag, self.tag)
        self.assertEqual(issue.category, self.category)
        self.assertEqual(issue.status, IssueStatusChoices.STATUS_NEW)
        self.assertEqual(issue.source, "qr")

        recipients = {address for message in mail.outbox for address in message.to}
        self.assertIn("manager@example.com", recipients)
        self.assertIn("plumber@example.com", recipients)
        self.assertIn("jan@example.com", recipients)
        self.assertTrue(issue.notifications.filter(success=True).exists())

    def test_honeypot_submission_is_rejected(self):
        response = self.client.post(
            self.report_url(),
            {
                "title": "Spam",
                "description": "Spam",
                "priority": "low",
                "website": "http://spam.example.com",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Issue.objects.exists())

    def test_report_blocked_when_tag_disallows_it(self):
        self.tag.allow_public_reports = False
        self.tag.save()
        response = self.client.post(
            self.report_url(),
            {"title": "x", "description": "y", "priority": "low", "website": ""},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Issue.objects.exists())

    def test_required_contact_is_enforced(self):
        self.tag.require_reporter_contact = True
        self.tag.save()
        response = self.client.post(
            self.report_url(),
            {"title": "x", "description": "y", "priority": "low", "website": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Issue.objects.exists())

    def test_rate_limit_blocks_excessive_reports(self):
        settings_copy = {
            "solomon_issues": {
                **PLUGIN_SETTINGS["solomon_issues"],
                "rate_limit_reports_per_hour": 1,
            }
        }
        payload = {
            "title": "x",
            "description": "y",
            "priority": "low",
            "website": "",
        }
        with override_settings(PLUGINS_CONFIG=settings_copy):
            self.client.post(self.report_url(), payload)
            response = self.client.post(self.report_url(), payload)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Issue.objects.count(), 1)

    def test_open_issues_are_listed_publicly(self):
        Issue.objects.create(asset_tag=self.tag, title="Known leak", description="x")
        Issue.objects.create(
            asset_tag=self.tag,
            title="Fixed leak",
            description="x",
            status=IssueStatusChoices.STATUS_CLOSED,
        )
        url = reverse(
            "plugins:solomon_issues:public_tag", kwargs={"code": self.tag.code}
        )
        response = self.client.get(url)
        self.assertContains(response, "Known leak")
        self.assertNotContains(response, "Fixed leak")

    def test_private_issues_are_hidden_publicly(self):
        Issue.objects.create(
            asset_tag=self.tag, title="Hidden leak", description="x", is_public=False
        )
        url = reverse(
            "plugins:solomon_issues:public_tag", kwargs={"code": self.tag.code}
        )
        self.assertNotContains(self.client.get(url), "Hidden leak")


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS, LOGIN_REQUIRED=True)
class PublicIssueViewTestCase(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox = []
        self.tag = AssetTag.objects.create(label="Elevator A", code="TESTTAG002")
        self.issue = Issue.objects.create(
            asset_tag=self.tag,
            title="Door does not close",
            description="It stays open.",
            reporter_email="tenant@example.com",
        )

    def issue_url(self):
        return reverse(
            "plugins:solomon_issues:public_issue",
            kwargs={"token": self.issue.access_token},
        )

    def test_reporter_can_view_timeline_without_login(self):
        response = self.client.get(self.issue_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Door does not close")

    def test_invalid_token_returns_404(self):
        url = reverse(
            "plugins:solomon_issues:public_issue", kwargs={"token": "wrong-token"}
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_internal_notes_are_not_exposed(self):
        self.issue.log_event(
            "comment", message="Internal only note", visibility="internal"
        )
        self.assertNotContains(self.client.get(self.issue_url()), "Internal only note")

    def test_reporter_reply_creates_comment_and_notifies(self):
        mail.outbox = []
        response = self.client.post(
            self.issue_url(), {"body": "It got worse today.", "website": ""}
        )
        self.assertRedirects(response, self.issue_url())
        comment = self.issue.comments.get()
        self.assertTrue(comment.from_reporter)
        self.assertEqual(comment.visibility, "public")
        self.assertTrue(mail.outbox)

    def test_unsubscribe_deactivates_subscriber(self):
        subscriber = IssueSubscriber.objects.get(issue=self.issue)
        url = reverse(
            "plugins:solomon_issues:public_unsubscribe",
            kwargs={"token": subscriber.token},
        )
        response = self.client.get(url)
        subscriber.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(subscriber.is_active)


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class AnonymousReportingDisabledTestCase(TestCase):
    def test_global_switch_disables_reporting(self):
        cache.clear()
        tag = AssetTag.objects.create(label="Door", code="TESTTAG003")
        disabled = {
            "solomon_issues": {
                **PLUGIN_SETTINGS["solomon_issues"],
                "allow_anonymous_reports": False,
            }
        }
        with override_settings(PLUGINS_CONFIG=disabled):
            response = self.client.post(
                reverse(
                    "plugins:solomon_issues:public_report", kwargs={"code": tag.code}
                ),
                {"title": "x", "description": "y", "priority": "low", "website": ""},
            )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Issue.objects.exists())
