import importlib
import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from solomon_facilities.navigation import menu
from solomon_facilities.tables import SpaceTable


class CzechTranslationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="translation-viewer", is_superuser=True
        )

    def test_enabled_plugin_catalogs_are_discoverable_and_compiled(self):
        for app in apps.get_app_configs():
            if not app.name.startswith("solomon_"):
                continue
            with self.subTest(app=app.name):
                locale = Path(app.path) / "locale/cs/LC_MESSAGES"
                self.assertTrue((locale / "django.po").is_file())
                self.assertTrue((locale / "django.mo").is_file())

    def test_facilities_navigation_is_translated_lazily(self):
        with override("cs"):
            self.assertEqual(str(menu.label), "Správa objektu")
            labels = [
                str(item.link_text)
                for group in menu.groups
                for item in group.items
            ]
            self.assertEqual(labels, [
                "Podlaží", "Půdorysy", "Prostory", "Přiřazení prostorů",
                "Pronájmy a užívání", "Dveře", "Zámkové vložky",
                "Klíčové profily", "Fyzické klíče", "Výdeje klíčů",
                "Technické soustavy", "Technické součásti", "Technická propojení",
            ])
        with override("en"):
            self.assertEqual(str(menu.label), "Facilities")

    def test_space_headers_are_translated_including_optional_columns(self):
        expected = {
            "reference": "Označení",
            "level": "Podlaží",
            "building": "Vchod nebo budova",
            "flat_assignments": "Přiřazení prostorů",
            "usages": "Pronájmy a užívání",
            "technical_assets": "Technické součásti",
        }
        with override("cs"):
            table = SpaceTable([])
            for name, label in expected.items():
                with self.subTest(column=name):
                    self.assertEqual(str(table.columns[name].header), label)
        with override("en"):
            self.assertEqual(str(SpaceTable([]).columns["level"].header), "Level")

    def test_declared_model_columns_keep_lazy_translated_labels(self):
        for app in apps.get_app_configs():
            if not app.name.startswith("solomon_"):
                continue
            if not (Path(app.path) / "tables.py").is_file():
                continue
            module = importlib.import_module(f"{app.name}.tables")
            for table in vars(module).values():
                if not isinstance(table, type) or table.__module__ != module.__name__:
                    continue
                if not hasattr(table, "base_columns"):
                    continue
                for name, column in table.base_columns.items():
                    if name not in table._meta.fields:
                        continue
                    if name in {"pk", "actions", "id"}:
                        continue
                    with self.subTest(table=table.__name__, column=name):
                        self.assertIsNotNone(column.verbose_name)

    def test_javascript_catalog_follows_request_language(self):
        self.client.force_login(self.user)
        url = reverse("plugins:solomon_facilities:javascript_catalog")
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "cs"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for label in (
            "Změněno", "Ukládání...", "Uloženo", "Soustava",
            "Na tomto podlaží nejsou žádné propojitelné objekty",
        ):
            self.assertContains(response, json.dumps(label))
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, json.dumps("Změněno"))
