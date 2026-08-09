"""Object detail panels for Solomon Facilities."""

from django.utils.translation import gettext_lazy as _
from netbox.ui import attrs, panels


class SpacePanel(panels.ObjectAttributesPanel):
    level = attrs.RelatedObjectAttr("level", label=_("Level"), linkify=True)
    building = attrs.RelatedObjectAttr(
        "building", label=_("Entrance or building"), linkify=True
    )
    parent = attrs.RelatedObjectAttr("parent", label=_("Parent space"), linkify=True)
    reference = attrs.TextAttr("reference", label=_("Reference"))
    name = attrs.TextAttr("name", label=_("Name"))
    kind = attrs.ChoiceAttr("kind", label=_("Type"))
    status = attrs.ChoiceAttr("status", label=_("Status"))
    area_m2 = attrs.TextAttr("area_m2", label=_("Area (m²)"))
    notes = attrs.TextAttr("notes", label=_("Notes"))


class DoorPanel(panels.ObjectAttributesPanel):
    level = attrs.RelatedObjectAttr("level", label=_("Level"), linkify=True)
    reference = attrs.TextAttr("reference", label=_("Reference"))
    name = attrs.TextAttr("name", label=_("Name"))
    door_type = attrs.ChoiceAttr("door_type", label=_("Type"))
    from_space = attrs.RelatedObjectAttr("from_space", label=_("Space A"), linkify=True)
    to_space = attrs.RelatedObjectAttr("to_space", label=_("Space B"), linkify=True)
    fire_rating = attrs.TextAttr("fire_rating", label=_("Fire rating"))
    emergency_exit = attrs.BooleanAttr("emergency_exit", label=_("Emergency exit"))
    notes = attrs.TextAttr("notes", label=_("Notes"))


class KeyProfilePanel(panels.ObjectAttributesPanel):
    building_object = attrs.RelatedObjectAttr(
        "building_object", label=_("Building object"), linkify=True
    )
    code = attrs.TextAttr("code", label=_("Profile code"))
    name = attrs.TextAttr("name", label=_("Name"))
    notes = attrs.TextAttr("notes", label=_("Notes"))


class KeyCopyPanel(panels.ObjectAttributesPanel):
    profile = attrs.RelatedObjectAttr("profile", label=_("Key profile"), linkify=True)
    inventory_code = attrs.TextAttr("inventory_code", label=_("Inventory code"))
    serial_number = attrs.TextAttr("serial_number", label=_("Serial number"))
    status = attrs.ChoiceAttr("status", label=_("Status"))
    notes = attrs.TextAttr("notes", label=_("Notes"))


class TechnicalSystemPanel(panels.ObjectAttributesPanel):
    building_object = attrs.RelatedObjectAttr(
        "building_object", label=_("Building object"), linkify=True
    )
    name = attrs.TextAttr("name", label=_("Name"))
    kind = attrs.ChoiceAttr("kind", label=_("System type"))
    description = attrs.TextAttr("description", label=_("Description"))


class TechnicalAssetPanel(panels.ObjectAttributesPanel):
    system = attrs.RelatedObjectAttr("system", label=_("System"), linkify=True)
    parent = attrs.RelatedObjectAttr(
        "parent", label=_("Parent component"), linkify=True
    )
    level = attrs.RelatedObjectAttr("level", label=_("Level"), linkify=True)
    space = attrs.RelatedObjectAttr("space", label=_("Space"), linkify=True)
    code = attrs.TextAttr("code", label=_("Asset code"))
    name = attrs.TextAttr("name", label=_("Name"))
    asset_type = attrs.TextAttr("asset_type", label=_("Component type"))
    status = attrs.ChoiceAttr("status", label=_("Status"))
    emergency_instructions = attrs.TextAttr(
        "emergency_instructions", label=_("Emergency instructions")
    )
    notes = attrs.TextAttr("notes", label=_("Notes"))
