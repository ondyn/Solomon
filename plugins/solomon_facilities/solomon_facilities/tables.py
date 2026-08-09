"""Tables for Solomon Facilities list and detail views."""

import django_tables2 as tables
from django.utils.translation import gettext_lazy as _
from netbox.tables import NetBoxTable, columns

from . import models


class BuildingLevelTable(NetBoxTable):
    reference = tables.Column(linkify=True)
    building_object = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.BuildingLevel
        fields = (
            "pk",
            "building_object",
            "number",
            "reference",
            "name",
            "elevation_m",
            "actions",
        )


class FloorPlanTable(NetBoxTable):
    name = tables.Column(linkify=True)
    level = tables.Column(linkify=True)
    active_revision = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = models.FloorPlan
        fields = (
            "pk",
            "name",
            "level",
            "width",
            "height",
            "measurement_unit",
            "active_revision",
            "actions",
        )


class SpaceTable(NetBoxTable):
    reference = tables.Column(linkify=True)
    level = tables.Column(linkify=True)
    building = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.Space
        fields = (
            "pk",
            "reference",
            "name",
            "kind",
            "level",
            "building",
            "area_m2",
            "status",
            "actions",
        )


class SpaceFlatAssignmentTable(NetBoxTable):
    space = tables.Column(linkify=True)
    flat = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.SpaceFlatAssignment
        fields = (
            "pk",
            "space",
            "flat",
            "role",
            "effective_from",
            "effective_to",
            "actions",
        )


class SpaceUsageTable(NetBoxTable):
    space = tables.Column(linkify=True)
    holder = tables.Column(empty_values=(), orderable=False, verbose_name=_("Holder"))

    def render_holder(self, record):
        return record.person or record.owner

    class Meta(NetBoxTable.Meta):
        model = models.SpaceUsage
        fields = (
            "pk",
            "space",
            "holder",
            "usage_type",
            "effective_from",
            "effective_to",
            "actions",
        )


class DoorTable(NetBoxTable):
    reference = tables.Column(linkify=True)
    level = tables.Column(linkify=True)
    emergency_exit = columns.BooleanColumn()

    class Meta(NetBoxTable.Meta):
        model = models.Door
        fields = (
            "pk",
            "reference",
            "name",
            "door_type",
            "level",
            "from_space",
            "to_space",
            "emergency_exit",
            "actions",
        )


class LockCylinderTable(NetBoxTable):
    door = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.LockCylinder
        fields = ("pk", "door", "name", "code", "active_from", "active_to", "actions")


class KeyProfileTable(NetBoxTable):
    code = tables.Column(linkify=True)
    building_object = tables.Column(linkify=True)
    copy_count = tables.Column(
        empty_values=(), orderable=False, verbose_name=_("Copies")
    )

    def render_copy_count(self, record):
        return record.copies.count()

    class Meta(NetBoxTable.Meta):
        model = models.KeyProfile
        fields = ("pk", "code", "name", "building_object", "copy_count", "actions")


class KeyProfileLockTable(NetBoxTable):
    key_profile = tables.Column(linkify=True)
    lock = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.KeyProfileLock
        fields = ("pk", "key_profile", "lock")


class KeyCopyTable(NetBoxTable):
    inventory_code = tables.Column(linkify=True)
    profile = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.KeyCopy
        fields = (
            "pk",
            "inventory_code",
            "profile",
            "serial_number",
            "status",
            "actions",
        )


class KeyIssueTable(NetBoxTable):
    key_copy = tables.Column(linkify=True)
    holder = tables.Column(empty_values=(), orderable=False, verbose_name=_("Holder"))

    def render_holder(self, record):
        return record.person or record.external_holder

    class Meta(NetBoxTable.Meta):
        model = models.KeyIssue
        fields = (
            "pk",
            "key_copy",
            "holder",
            "issued_at",
            "due_at",
            "returned_at",
            "purpose",
            "actions",
        )


class TechnicalSystemTable(NetBoxTable):
    name = tables.Column(linkify=True)
    building_object = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.TechnicalSystem
        fields = ("pk", "name", "kind", "building_object", "actions")


class TechnicalAssetTable(NetBoxTable):
    code = tables.Column(linkify=True)
    system = tables.Column(linkify=True)
    level = tables.Column(linkify=True)
    space = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.TechnicalAsset
        fields = (
            "pk",
            "code",
            "name",
            "asset_type",
            "system",
            "level",
            "space",
            "status",
            "actions",
        )


class TechnicalConnectionTable(NetBoxTable):
    from_asset = tables.Column(linkify=True)
    to_asset = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        model = models.TechnicalConnection
        fields = ("pk", "from_asset", "kind", "to_asset", "actions")
