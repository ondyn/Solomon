"""Tests for the language switcher on public pages."""

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from solomon_issues.models import AssetTag, Issue

PLUGIN_SETTINGS = {
    "solomon_issues": {
        "allow_anonymous_reports": True,
        "public_languages": ["en", "cs"],
        "notifications_enabled": False,
    }
}


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class PublicLanguageTestCase(TestCase):
    def setUp(self):
        self.tag = AssetTag.objects.create(label="Riser valve", code="LANGTAG001")
        self.issue = Issue.objects.create(
            asset_tag=self.tag, title="Leak", description="Water on the floor"
        )

    def tag_url(self):
        return reverse(
            "plugins:solomon_issues:public_tag", kwargs={"code": self.tag.code}
        )

    def issue_url(self):
        return reverse(
            "plugins:solomon_issues:public_issue",
            kwargs={"token": self.issue.access_token},
        )

    def test_switcher_offers_both_languages(self):
        response = self.client.get(self.tag_url(), HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "?lang=cs")
        self.assertContains(response, "?lang=en")

    def test_english_is_rendered_by_default(self):
        response = self.client.get(self.tag_url(), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(response, "Describe the problem")
        self.assertContains(response, "Send report")

    def test_czech_is_rendered_on_request(self):
        response = self.client.get(
            self.tag_url(), {"lang": "cs"}, HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, "Popište problém")
        self.assertContains(response, "Odeslat hlášení")

    def test_choice_is_remembered_in_a_cookie(self):
        response = self.client.get(
            self.tag_url(), {"lang": "cs"}, HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "cs")

        follow_up = self.client.get(self.tag_url(), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(follow_up, "Popište problém")

    def test_issue_page_switches_language_too(self):
        response = self.client.get(
            self.issue_url(), {"lang": "cs"}, HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, "Časová osa")

    def test_unknown_language_is_ignored(self):
        response = self.client.get(
            self.tag_url(), {"lang": "de"}, HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)
        self.assertContains(response, "Describe the problem")

    def test_switcher_can_be_limited_by_configuration(self):
        single = {
            "solomon_issues": {
                **PLUGIN_SETTINGS["solomon_issues"],
                "public_languages": ["en"],
            }
        }
        with override_settings(PLUGINS_CONFIG=single):
            response = self.client.get(self.tag_url(), HTTP_ACCEPT_LANGUAGE="en")
            self.assertNotContains(response, "?lang=cs")
