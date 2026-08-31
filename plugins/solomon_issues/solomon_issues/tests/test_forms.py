"""Tests for the asset tag linked-object selector and label caption."""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from solomon_property.models import BuildingObject

from solomon_issues.forms import AssetTagForm
from solomon_issues.models import AssetTag, default_label_caption

PLUGIN_SETTINGS = {"solomon_issues": {"default_label_caption": ""}}


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class AssetTagFormTestCase(TestCase):
    def setUp(self):
        self.building_object = BuildingObject.objects.create(name="Salounova 1937")
        self.content_type = ContentType.objects.get_for_model(BuildingObject)

    def base_data(self, **overrides):
        data = {
            "label": "Riser valve",
            "status": "active",
            "default_priority": "normal",
        }
        data.update(overrides)
        return data

    def test_selector_is_disabled_until_a_type_is_chosen(self):
        form = AssetTagForm()
        self.assertTrue(form.fields["assigned_object"].disabled)
        self.assertNotIn("assigned_object_id", form.fields)

    def test_selector_targets_the_chosen_type(self):
        form = AssetTagForm(
            data=self.base_data(assigned_object_type=self.content_type.pk)
        )
        self.assertFalse(form.fields["assigned_object"].disabled)
        self.assertEqual(form.fields["assigned_object"].queryset.model, BuildingObject)

    def test_saving_links_the_selected_object(self):
        form = AssetTagForm(
            data=self.base_data(
                assigned_object_type=self.content_type.pk,
                assigned_object=self.building_object.pk,
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        tag = form.save()
        self.assertEqual(tag.assigned_object, self.building_object)

    def test_type_without_object_is_rejected(self):
        form = AssetTagForm(
            data=self.base_data(assigned_object_type=self.content_type.pk)
        )
        self.assertFalse(form.is_valid())
        self.assertIn("assigned_object", form.errors)

    def test_clearing_the_type_clears_the_link(self):
        tag = AssetTag.objects.create(
            label="Riser valve",
            assigned_object_type=self.content_type,
            assigned_object_id=self.building_object.pk,
        )
        form = AssetTagForm(data=self.base_data(), instance=tag)
        self.assertTrue(form.is_valid(), form.errors)
        tag = form.save()
        self.assertIsNone(tag.assigned_object_id)
        self.assertIsNone(tag.assigned_object_type)

    def test_existing_link_prefills_the_selector(self):
        tag = AssetTag.objects.create(
            label="Riser valve",
            assigned_object_type=self.content_type,
            assigned_object_id=self.building_object.pk,
        )
        form = AssetTagForm(instance=tag)
        self.assertEqual(form.initial["assigned_object"], self.building_object)
        self.assertFalse(form.fields["assigned_object"].disabled)


@override_settings(PLUGINS_CONFIG=PLUGIN_SETTINGS)
class LabelCaptionTestCase(TestCase):
    def test_caption_falls_back_to_the_default(self):
        tag = AssetTag.objects.create(label="Boiler")
        self.assertEqual(str(tag.label_caption), str(default_label_caption()))

    def test_caption_uses_the_tag_value(self):
        tag = AssetTag.objects.create(label="Boiler", print_instructions="Report here")
        self.assertEqual(tag.label_caption, "Report here")

    def test_default_caption_is_configurable(self):
        configured = {"solomon_issues": {"default_label_caption": "Nahlaste zavadu"}}
        with override_settings(PLUGINS_CONFIG=configured):
            tag = AssetTag.objects.create(label="Boiler")
            self.assertEqual(tag.label_caption, "Nahlaste zavadu")

    def test_new_tag_form_prefills_the_caption(self):
        form = AssetTagForm()
        self.assertEqual(
            str(form.fields["print_instructions"].initial),
            str(default_label_caption()),
        )
