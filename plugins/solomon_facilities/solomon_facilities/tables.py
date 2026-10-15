"""Tables for Solomon Facilities list and detail views."""

import django_tables2 as tables
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from netbox.tables import NetBoxTable, columns

from . import models


class BuildingLevelTable(NetBoxTable):
    reference = tables.Column(linkify=True, verbose_name=_("Displayed reference"))
    building_object = tables.Column(linkify=True, verbose_name=_("Building object"))

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
    name = tables.Column(linkify=True, verbose_name=_("Name"))
    level = tables.Column(linkify=True, verbose_name=pgettext_lazy("building floor", "Level"))
    active_revision = tables.Column(verbose_name=_("Active revision"))

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
    reference = tables.Column(linkify=True, verbose_name=_("Reference"))
    level = tables.Column(linkify=True, verbose_name=pgettext_lazy("building floor", "Level"))
    building = tables.Column(linkify=True, verbose_name=_("Entrance or building"))
    flat_assignments = columns.TemplateColumn(
        template_name="solomon_facilities/columns/space_flat_assignments.html",
        accessor="current_flat_assignments",
        verbose_name=_("Flat assignments"),
        order_by=("_flat_assignment_count",),
    )
    usages = columns.TemplateColumn(
        template_name="solomon_facilities/columns/space_usages.html",
        accessor="current_usages",
        verbose_name=_("Rentals and occupancy"),
        order_by=("_usage_count",),
    )
    technical_assets = columns.TemplateColumn(
        template_name="solomon_facilities/columns/space_technical_assets.html",
        accessor="visible_technical_assets",
        verbose_name=_("Technical assets"),
        order_by=("_technical_asset_count",),
    )

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
            "flat_assignments",
            "usages",
            "technical_assets",
            "actions",
        )
        default_columns = (
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
    space = tables.Column(linkify=True, verbose_name=_("Space"))
    flat = tables.Column(linkify=True, verbose_name=_("Flat"))

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
    space = tables.Column(linkify=True, verbose_name=_("Space"))
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
    reference = tables.Column(linkify=True, verbose_name=_("Reference"))
    level = tables.Column(linkify=True, verbose_name=pgettext_lazy("building floor", "Level"))
    emergency_exit = columns.BooleanColumn(verbose_name=_("Emergency exit"))

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
    door = tables.Column(linkify=True, verbose_name=_("Door"))

    class Meta(NetBoxTable.Meta):
        model = models.LockCylinder
        fields = ("pk", "door", "name", "code", "active_from", "active_to", "actions")


class KeyProfileTable(NetBoxTable):
    code = tables.Column(linkify=True, verbose_name=_("Profile code"))
    building_object = tables.Column(linkify=True, verbose_name=_("Building object"))
    copy_count = tables.Column(
        empty_values=(), orderable=False, verbose_name=_("Copies")
    )

    def render_copy_count(self, record):
        return record.copies.count()

    class Meta(NetBoxTable.Meta):
        model = models.KeyProfile
        fields = ("pk", "code", "name", "building_object", "copy_count", "actions")


class KeyProfileLockTable(NetBoxTable):
    key_profile = tables.Column(linkify=True, verbose_name=_("Key profile"))
    lock = tables.Column(linkify=True, verbose_name=_("Lock cylinder"))

    class Meta(NetBoxTable.Meta):
        model = models.KeyProfileLock
        fields = ("pk", "key_profile", "lock")


class KeyCopyTable(NetBoxTable):
    inventory_code = tables.Column(linkify=True, verbose_name=_("Inventory code"))
    profile = tables.Column(linkify=True, verbose_name=_("Key profile"))

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
    key_copy = tables.Column(linkify=True, verbose_name=_("Physical key"))
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
    name = tables.Column(linkify=True, verbose_name=_("Name"))
    building_object = tables.Column(linkify=True, verbose_name=_("Building object"))

    class Meta(NetBoxTable.Meta):
        model = models.TechnicalSystem
        fields = ("pk", "name", "kind", "building_object", "actions")


class TechnicalAssetTable(NetBoxTable):
    code = tables.Column(linkify=True, verbose_name=_("Asset code"))
    system = tables.Column(linkify=True, verbose_name=_("System"))
    level = tables.Column(linkify=True, verbose_name=pgettext_lazy("building floor", "Level"))
    space = tables.Column(linkify=True, verbose_name=_("Space"))

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
    from_asset = tables.Column(linkify=True, verbose_name=_("From component"))
    to_asset = tables.Column(linkify=True, verbose_name=_("To component"))

    class Meta(NetBoxTable.Meta):
        model = models.TechnicalConnection
        fields = ("pk", "from_asset", "kind", "to_asset", "actions")
