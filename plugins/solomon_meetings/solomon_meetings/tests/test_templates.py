from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import reverse


class MeetingTemplatesTest(SimpleTestCase):
    def test_all_object_templates_exist(self):
        expected_templates = [
            "solomon_meetings/meetingtype.html",
            "solomon_meetings/meeting.html",
            "solomon_meetings/agendaitem.html",
            "solomon_meetings/meetingattendance.html",
            "solomon_meetings/vote.html",
            "solomon_meetings/voteweightstyle.html",
            "solomon_meetings/meetingminutes.html",
            "solomon_meetings/meetinginvitation.html",
        ]

        for template_name in expected_templates:
            with self.subTest(template_name=template_name):
                template = get_template(template_name)
                self.assertIsNotNone(template)

    def test_all_changelog_routes_reverse(self):
        expected_routes = [
            "plugins:solomon_meetings:meetingtype_changelog",
            "plugins:solomon_meetings:meeting_changelog",
            "plugins:solomon_meetings:agendaitem_changelog",
            "plugins:solomon_meetings:meetingattendance_changelog",
            "plugins:solomon_meetings:vote_changelog",
            "plugins:solomon_meetings:voteweightstyle_changelog",
            "plugins:solomon_meetings:meetingminutes_changelog",
            "plugins:solomon_meetings:meetinginvitation_changelog",
        ]

        for route_name in expected_routes:
            with self.subTest(route_name=route_name):
                url = reverse(route_name, kwargs={"pk": 1})
                self.assertIn("/changelog/", url)
