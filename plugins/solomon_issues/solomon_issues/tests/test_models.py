"""Model-level tests for Solomon Issues."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from solomon_issues.choices import (
    IssueEventTypeChoices,
    IssueStatusChoices,
    VisibilityChoices,
)
from solomon_issues.models import AssetTag, Issue, IssueCategory, IssueSubscriber


class AssetTagTestCase(TestCase):
    def test_code_is_generated_and_unique(self):
        first = AssetTag.objects.create(label="Water valve B2")
        second = AssetTag.objects.create(label="Elevator A")
        self.assertTrue(first.code)
        self.assertEqual(len(first.code), 10)
        self.assertNotEqual(first.code, second.code)

    def test_explicit_code_is_preserved(self):
        tag = AssetTag.objects.create(label="Front door", code="FRONTDOOR1")
        self.assertEqual(tag.code, "FRONTDOOR1")

    def test_public_url_contains_code(self):
        tag = AssetTag.objects.create(label="Boiler")
        self.assertIn(f"/t/{tag.code}/", tag.public_url())

    def test_notification_recipients_merge_category(self):
        category = IssueCategory.objects.create(
            name="Plumbing", slug="plumbing", notify_emails="plumber@example.com"
        )
        tag = AssetTag.objects.create(
            label="Riser valve",
            category=category,
            notify_emails="manager@example.com, manager@example.com",
        )
        self.assertEqual(
            tag.notification_recipients,
            ["manager@example.com", "plumber@example.com"],
        )

    def test_retired_tag_is_not_reportable(self):
        tag = AssetTag.objects.create(label="Old meter", status="retired")
        self.assertFalse(tag.is_reportable)

    def test_invalid_recipient_list_is_rejected(self):
        tag = AssetTag(label="Bad", notify_emails="not-an-email")
        with self.assertRaises(ValidationError):
            tag.full_clean()


class IssueTestCase(TestCase):
    def setUp(self):
        self.category = IssueCategory.objects.create(name="General", slug="general")
        self.tag = AssetTag.objects.create(label="Elevator A", category=self.category)

    def test_number_and_token_are_generated(self):
        issue = Issue.objects.create(
            asset_tag=self.tag, title="Stuck door", description="Does not close"
        )
        self.assertEqual(issue.number, "ISS-000001")
        self.assertTrue(issue.access_token)

    def test_numbers_increment(self):
        Issue.objects.create(asset_tag=self.tag, title="One", description="x")
        second = Issue.objects.create(asset_tag=self.tag, title="Two", description="y")
        self.assertEqual(second.number, "ISS-000002")

    def test_creation_logs_event_and_subscriber(self):
        issue = Issue.objects.create(
            asset_tag=self.tag,
            title="Leak",
            description="Water on the floor",
            reporter_email="tenant@example.com",
            reporter_name="Tenant",
        )
        self.assertEqual(
            issue.events.filter(event_type=IssueEventTypeChoices.EVENT_CREATED).count(),
            1,
        )
        subscriber = IssueSubscriber.objects.get(issue=issue)
        self.assertEqual(subscriber.email, "tenant@example.com")
        self.assertTrue(subscriber.is_reporter)
        self.assertTrue(subscriber.token)

    def test_apply_status_sets_timestamps_and_logs(self):
        issue = Issue.objects.create(asset_tag=self.tag, title="Leak", description="x")
        event = issue.apply_status(IssueStatusChoices.STATUS_RESOLVED)
        issue.refresh_from_db()
        self.assertEqual(event.event_type, IssueEventTypeChoices.EVENT_RESOLVED)
        self.assertIsNotNone(issue.resolved_at)
        self.assertIsNotNone(issue.acknowledged_at)
        self.assertFalse(issue.is_open)

    def test_reopening_logs_reopened_event(self):
        issue = Issue.objects.create(asset_tag=self.tag, title="Leak", description="x")
        issue.apply_status(IssueStatusChoices.STATUS_CLOSED)
        event = issue.apply_status(IssueStatusChoices.STATUS_IN_PROGRESS)
        issue.refresh_from_db()
        self.assertEqual(event.event_type, IssueEventTypeChoices.EVENT_REOPENED)
        self.assertIsNone(issue.closed_at)
        self.assertTrue(issue.is_open)

    def test_apply_status_is_a_noop_when_unchanged(self):
        issue = Issue.objects.create(asset_tag=self.tag, title="Leak", description="x")
        self.assertIsNone(issue.apply_status(IssueStatusChoices.STATUS_NEW))

    def test_issue_inherits_linked_object_from_tag(self):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(IssueCategory)
        self.tag.assigned_object_type = content_type
        self.tag.assigned_object_id = self.category.pk
        self.tag.save()

        issue = Issue.objects.create(asset_tag=self.tag, title="x", description="y")
        self.assertEqual(issue.assigned_object_type, content_type)
        self.assertEqual(issue.assigned_object_id, self.category.pk)

    def test_cannot_be_duplicate_of_itself(self):
        issue = Issue.objects.create(asset_tag=self.tag, title="x", description="y")
        issue.duplicate_of = issue
        with self.assertRaises(ValidationError):
            issue.clean()

    def test_public_events_exclude_internal_entries(self):
        issue = Issue.objects.create(asset_tag=self.tag, title="x", description="y")
        issue.log_event(
            IssueEventTypeChoices.EVENT_COMMENT,
            message="internal only",
            visibility=VisibilityChoices.VISIBILITY_INTERNAL,
        )
        self.assertEqual(issue.events.count(), 2)
        self.assertEqual(issue.public_events().count(), 1)
