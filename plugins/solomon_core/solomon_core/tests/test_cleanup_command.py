from io import StringIO

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from django.apps import apps


class CleanupNetBoxLeftoversCommandTests(TestCase):
    def setUp(self):
        self.stale_ct = ContentType.objects.create(app_label="obsolete_app", model="oldmodel")
        self.safe_ct = ContentType.objects.create(app_label="solomon_legacy", model="keptmodel")
        Permission.objects.create(
            name="Can view old model",
            codename="view_oldmodel",
            content_type=self.stale_ct,
        )

    def test_dry_run_does_not_delete(self):
        out = StringIO()
        call_command("cleanup_netbox_leftovers", stdout=out)
        self.assertTrue(ContentType.objects.filter(pk=self.stale_ct.pk).exists())
        self.assertIn("Dry run", out.getvalue())

    def test_execute_deletes_stale_content_types_and_permissions(self):
        out = StringIO()
        call_command("cleanup_netbox_leftovers", "--execute", stdout=out)
        self.assertFalse(ContentType.objects.filter(pk=self.stale_ct.pk).exists())
        self.assertFalse(Permission.objects.filter(content_type=self.stale_ct).exists())
        self.assertTrue(ContentType.objects.filter(pk=self.safe_ct.pk).exists())
        self.assertIn("Cleanup completed", out.getvalue())

    def test_execute_normalizes_disabled_module_object_types(self):
        object_type_model = apps.get_model("core", "ObjectType")
        object_type = object_type_model.objects.filter(app_label="dcim").first()
        self.assertIsNotNone(object_type)

        object_type.features = ["custom_fields", "export_templates"]
        object_type.public = True
        object_type.save(update_fields=["features", "public"])

        out = StringIO()
        call_command("cleanup_netbox_leftovers", "--execute", stdout=out)

        object_type.refresh_from_db()
        self.assertNotIn("custom_fields", object_type.features)
        self.assertFalse(object_type.public)
        self.assertIn("Normalized disabled object types", out.getvalue())
