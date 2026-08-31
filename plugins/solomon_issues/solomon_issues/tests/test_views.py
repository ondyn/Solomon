"""Tests for the authenticated management views and permissions."""

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from users.models import ObjectPermission, User
from utilities.permissions import resolve_permission_type

from solomon_issues.choices import IssueEventTypeChoices, IssueStatusChoices
from solomon_issues.models import AssetTag, Issue, IssueCategory

PLUGIN_SETTINGS = {
    "solomon_issues": {
        "public_base_url": "",
        "allow_anonymous_reports": True,
        "public_issue_visibility": "open",
        "manager_emails": ["manager@example.com"],
        "notifications_enabled": True,
        "async_notifications": False,
        "qr_error_correction": "M",
        "rate_limit_reports_per_hour": 0,
        "attachments_enabled": True,
        "max_attachment_size_mb": 10,
    }
}


def grant(user, *names):
    """Assign NetBox ObjectPermissions in the form <app>.<action>_<model>."""
    for name in names:
        object_type, action = resolve_permission_type(name)
        permission = ObjectPermission.objects.create(name=name[:100], actions=[action])
        permission.users.add(user)
        permission.object_types.add(object_type)
    return User.objects.get(pk=user.pk)


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class QRRenderingTestCase(TestCase):
    def setUp(self):
        self.tag = AssetTag.objects.create(label="Boiler", code="QRTAG00001")
        self.user = User.objects.create_user("qruser", password="pass1234")

    def test_qr_requires_permission(self):
        self.client.force_login(self.user)
        url = reverse("plugins:solomon_issues:assettag_qr", kwargs={"pk": self.tag.pk})
        self.assertIn(self.client.get(url).status_code, (302, 403))

    def test_qr_returns_svg(self):
        user = grant(self.user, "solomon_issues.view_assettag")
        self.client.force_login(user)
        url = reverse("plugins:solomon_issues:assettag_qr", kwargs={"pk": self.tag.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)

    def test_label_sheet_requires_print_permission(self):
        user = grant(self.user, "solomon_issues.view_assettag")
        self.client.force_login(user)
        url = reverse("plugins:solomon_issues:assettag_labels")
        self.assertIn(self.client.get(url).status_code, (302, 403))

    def test_label_sheet_renders_selected_tags(self):
        user = grant(
            self.user,
            "solomon_issues.view_assettag",
            "solomon_issues.print_assettag",
        )
        self.client.force_login(user)
        url = reverse("plugins:solomon_issues:assettag_labels")
        response = self.client.get(url, {"pk": self.tag.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Boiler")
        self.assertContains(response, "<svg")

    def test_marking_labels_printed(self):
        user = grant(
            self.user,
            "solomon_issues.view_assettag",
            "solomon_issues.print_assettag",
        )
        self.client.force_login(user)
        self.client.post(
            reverse("plugins:solomon_issues:assettag_labels"), {"pk": [self.tag.pk]}
        )
        self.tag.refresh_from_db()
        self.assertIsNotNone(self.tag.printed_at)


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class IssueWorkflowTestCase(TestCase):
    def setUp(self):
        mail.outbox = []
        self.category = IssueCategory.objects.create(name="General", slug="general")
        self.tag = AssetTag.objects.create(
            label="Elevator A", code="MGRTAG0001", category=self.category
        )
        self.issue = Issue.objects.create(
            asset_tag=self.tag,
            category=self.category,
            title="Door does not close",
            description="Stays open",
            reporter_email="tenant@example.com",
        )
        self.user = User.objects.create_user(
            "manager", password="pass1234", email="staff@example.com"
        )

    def status_url(self):
        return reverse(
            "plugins:solomon_issues:issue_status", kwargs={"pk": self.issue.pk}
        )

    def comment_url(self):
        return reverse(
            "plugins:solomon_issues:issue_comment", kwargs={"pk": self.issue.pk}
        )

    def test_status_change_requires_permission(self):
        self.client.force_login(self.user)
        response = self.client.post(self.status_url(), {"status": "in_progress"})
        self.assertIn(response.status_code, (302, 403))
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, IssueStatusChoices.STATUS_NEW)

    def test_manager_can_resolve_and_notify(self):
        user = grant(
            self.user,
            "solomon_issues.view_issue",
            "solomon_issues.manage_issue",
        )
        self.client.force_login(user)
        mail.outbox = []
        response = self.client.post(
            self.status_url(),
            {
                "status": IssueStatusChoices.STATUS_RESOLVED,
                "priority": "high",
                "resolution": "Adjusted the door sensor.",
                "notify": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, IssueStatusChoices.STATUS_RESOLVED)
        self.assertEqual(self.issue.priority, "high")
        self.assertIsNotNone(self.issue.resolved_at)
        self.assertTrue(
            self.issue.events.filter(
                event_type=IssueEventTypeChoices.EVENT_RESOLVED
            ).exists()
        )
        recipients = {address for message in mail.outbox for address in message.to}
        self.assertIn("tenant@example.com", recipients)
        self.assertIn("manager@example.com", recipients)

    def test_public_reply_notifies_reporter(self):
        user = grant(
            self.user,
            "solomon_issues.view_issue",
            "solomon_issues.add_issuecomment",
        )
        self.client.force_login(user)
        mail.outbox = []
        self.client.post(
            self.comment_url(), {"visibility": "public", "body": "We are on it."}
        )
        comment = self.issue.comments.get()
        self.assertEqual(comment.author, user)
        recipients = {address for message in mail.outbox for address in message.to}
        self.assertIn("tenant@example.com", recipients)

    def test_internal_reply_does_not_reach_reporter(self):
        user = grant(
            self.user,
            "solomon_issues.view_issue",
            "solomon_issues.add_issuecomment",
        )
        self.client.force_login(user)
        mail.outbox = []
        self.client.post(
            self.comment_url(), {"visibility": "internal", "body": "Order the part."}
        )
        recipients = {address for message in mail.outbox for address in message.to}
        self.assertNotIn("tenant@example.com", recipients)

    def test_issue_detail_hides_internal_timeline_without_permission(self):
        self.issue.log_event(
            IssueEventTypeChoices.EVENT_COMMENT,
            message="Internal only note",
            visibility="internal",
        )
        user = grant(self.user, "solomon_issues.view_issue")
        self.client.force_login(user)
        url = reverse("plugins:solomon_issues:issue", kwargs={"pk": self.issue.pk})
        self.assertNotContains(self.client.get(url), "Internal only note")

    def test_issue_detail_shows_internal_timeline_with_permission(self):
        self.issue.log_event(
            IssueEventTypeChoices.EVENT_COMMENT,
            message="Internal only note",
            visibility="internal",
        )
        user = grant(
            self.user,
            "solomon_issues.view_issue",
            "solomon_issues.view_internal_issue",
        )
        self.client.force_login(user)
        url = reverse("plugins:solomon_issues:issue", kwargs={"pk": self.issue.pk})
        self.assertContains(self.client.get(url), "Internal only note")

    def test_issue_list_requires_permission(self):
        self.client.force_login(self.user)
        url = reverse("plugins:solomon_issues:issue_list")
        self.assertIn(self.client.get(url).status_code, (302, 403))

    def test_issue_list_visible_with_permission(self):
        user = grant(self.user, "solomon_issues.view_issue")
        self.client.force_login(user)
        url = reverse("plugins:solomon_issues:issue_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.issue.number)


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class StaffPageRenderingTestCase(TestCase):
    """Smoke test every management page so template errors surface early."""

    def setUp(self):
        self.category = IssueCategory.objects.create(name="General", slug="general")
        self.tag = AssetTag.objects.create(
            label="Elevator A", code="RENDERTAG1", category=self.category
        )
        self.issue = Issue.objects.create(
            asset_tag=self.tag, title="Door", description="Stays open"
        )
        self.user = User.objects.create_user(
            "admin", password="pass1234", is_superuser=True
        )
        self.client.force_login(self.user)

    def test_all_management_pages_render(self):
        urls = [
            reverse("plugins:solomon_issues:issue_list"),
            reverse("plugins:solomon_issues:issue_add"),
            reverse("plugins:solomon_issues:issue", kwargs={"pk": self.issue.pk}),
            reverse("plugins:solomon_issues:issue_edit", kwargs={"pk": self.issue.pk}),
            reverse("plugins:solomon_issues:assettag_list"),
            reverse("plugins:solomon_issues:assettag_add"),
            reverse("plugins:solomon_issues:assettag", kwargs={"pk": self.tag.pk}),
            reverse("plugins:solomon_issues:assettag_edit", kwargs={"pk": self.tag.pk}),
            reverse(
                "plugins:solomon_issues:assettag_issues", kwargs={"pk": self.tag.pk}
            ),
            reverse("plugins:solomon_issues:assettag_labels"),
            reverse("plugins:solomon_issues:issuecategory_list"),
            reverse("plugins:solomon_issues:issuecategory_add"),
            reverse(
                "plugins:solomon_issues:issuecategory", kwargs={"pk": self.category.pk}
            ),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_api_endpoints_respond(self):
        for path in ("tags", "issues", "categories", "comments", "events"):
            with self.subTest(path=path):
                response = self.client.get(f"/api/plugins/issues/{path}/")
                self.assertEqual(response.status_code, 200)

    def test_badges_use_contrast_aware_classes(self):
        for url in (
            reverse("plugins:solomon_issues:assettag", kwargs={"pk": self.tag.pk}),
            reverse("plugins:solomon_issues:issue", kwargs={"pk": self.issue.pk}),
        ):
            with self.subTest(url=url):
                content = self.client.get(url).content.decode()
                self.assertIn("badge text-bg-", content)
                self.assertNotIn('class="badge bg-', content)

    def test_public_code_avoids_low_contrast_code_element(self):
        url = reverse("plugins:solomon_issues:assettag", kwargs={"pk": self.tag.pk})
        content = self.client.get(url).content.decode()
        self.assertIn('<span class="issues-code">RENDERTAG1</span>', content)

    def test_tag_form_offers_an_object_selector(self):
        url = reverse("plugins:solomon_issues:assettag_add")
        content = self.client.get(url).content.decode()
        self.assertIn("id_assigned_object", content)
        self.assertNotIn("id_assigned_object_id", content)


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class ReportPermissionTestCase(TestCase):
    """`report_issue` lets trusted users bypass the anonymous reporting switch."""

    def setUp(self):
        self.tag = AssetTag.objects.create(
            label="Elevator A", code="PERMTAG001", allow_public_reports=False
        )
        self.user = User.objects.create_user("resident", password="pass1234")
        self.payload = {
            "title": "Door does not close",
            "description": "Stays open",
            "priority": "normal",
            "website": "",
        }

    def report_url(self):
        return reverse(
            "plugins:solomon_issues:public_report", kwargs={"code": self.tag.code}
        )

    def test_signed_in_user_without_permission_is_blocked(self):
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.post(self.report_url(), self.payload).status_code, 404
        )
        self.assertFalse(Issue.objects.exists())

    def test_signed_in_user_with_permission_can_report(self):
        user = grant(self.user, "solomon_issues.report_issue")
        self.client.force_login(user)
        self.assertEqual(
            self.client.post(self.report_url(), self.payload).status_code, 302
        )
        issue = Issue.objects.get()
        self.assertEqual(issue.source, "portal")
        self.assertEqual(issue.reporter_user, user)

    def test_retired_tag_blocks_even_privileged_users(self):
        self.tag.status = "retired"
        self.tag.save()
        user = grant(self.user, "solomon_issues.report_issue")
        self.client.force_login(user)
        self.assertEqual(
            self.client.post(self.report_url(), self.payload).status_code, 404
        )
