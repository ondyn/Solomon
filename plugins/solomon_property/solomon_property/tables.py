"""Solomon Property - Django table definitions for list views."""

import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns

from .models import Building, BuildingObject, Flat, FlatOwner, PropertyOwner, Person, PropertyTenant


class BuildingObjectTable(NetBoxTable):
    name = tables.Column(linkify=True)
    municipality_name = tables.Column(verbose_name=_("Municipality"))
    city_part_name = tables.Column(verbose_name=_("City part"))
    house_numbers = tables.Column(orderable=False)
    usage_name = tables.Column(verbose_name=_("Usage"))
    cuzk_building_id = tables.Column(verbose_name=_("CUZK ID"))

    class Meta(NetBoxTable.Meta):
        model = BuildingObject
        fields = (
            "pk", "name", "municipality_name", "city_part_name", "house_numbers",
            "usage_name", "cuzk_building_id", "actions",
        )
        default_columns = (
            "name", "municipality_name", "city_part_name", "house_numbers", "usage_name",
        )


class BuildingTable(NetBoxTable):
    building_object = tables.Column(linkify=True, verbose_name=_("Building object"))
    name = tables.Column(linkify=True)
    street = tables.Column()
    house_number = tables.Column(verbose_name=_("House No"))
    city = tables.Column()
    total_units = tables.Column(verbose_name=_("Units"))
    elevator = columns.BooleanColumn()
    cuzk_building_id = tables.Column(verbose_name=_("CUZK ID"))

    class Meta(NetBoxTable.Meta):
        model = Building
        fields = (
            "pk", "building_object", "name", "street", "house_number", "city",
            "total_units", "elevator", "year_built", "cuzk_building_id", "actions",
        )
        default_columns = (
            "building_object", "name", "street", "house_number", "city", "total_units", "elevator",
        )


class FlatTable(NetBoxTable):
    flat_number = tables.Column(linkify=True, verbose_name=_("Flat No"))
    building = tables.Column(linkify=True)
    floor = tables.Column()
    area_m2 = tables.Column(verbose_name=_("Area m2"))
    disposition = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = Flat
        fields = (
            "pk", "flat_number", "building", "floor", "area_m2",
            "disposition", "cuzk_unit_id", "actions",
        )
        default_columns = (
            "flat_number", "building", "floor", "area_m2", "disposition",
        )


class PersonTable(NetBoxTable):
    last_name = tables.Column(linkify=True, verbose_name=_("Last name"))
    first_name = tables.Column(verbose_name=_("First name"))
    title_before = tables.Column(verbose_name=_("Title"))
    email = tables.TemplateColumn(
        template_code='{{ record.email }}',
        verbose_name=_("Email"),
        orderable=False,
    )
    phone = tables.TemplateColumn(
        template_code='{{ record.phone }}',
        verbose_name=_("Phone"),
        orderable=False,
    )
    permanent_address = tables.Column(verbose_name=_("Address"))

    class Meta(NetBoxTable.Meta):
        model = Person
        fields = (
            "pk", "last_name", "first_name", "title_before", "title_after",
            "email", "phone", "permanent_address", "actions",
        )
        default_columns = (
            "last_name", "first_name", "title_before", "email", "phone",
            "permanent_address",
        )


class PropertyOwnerTable(NetBoxTable):
    display_name = tables.Column(linkify=True, verbose_name=_("Name"))
    person_type = tables.Column(verbose_name=_("Type"))
    email = tables.Column()
    phone = tables.Column()
    permanent_address = tables.Column(verbose_name=_("Address"))
    cuzk_owner_id = tables.Column(verbose_name=_("CUZK ID"))

    class Meta(NetBoxTable.Meta):
        model = PropertyOwner
        fields = (
            "pk", "display_name", "person_type", "email", "phone",
            "permanent_address", "cuzk_owner_id", "actions",
        )
        default_columns = (
            "display_name", "person_type", "email", "phone", "permanent_address",
        )


class FlatOwnerTable(NetBoxTable):
    flat = tables.Column(linkify=True)
    owner = tables.Column(linkify=True)
    share = tables.Column(accessor="share", orderable=False, verbose_name=_("Share"))
    effective_from = tables.DateColumn()
    effective_to = tables.DateColumn()
    is_current = columns.BooleanColumn(verbose_name=_("Current"))

    class Meta(NetBoxTable.Meta):
        model = FlatOwner
        fields = (
            "pk", "flat", "owner", "share", "effective_from", "effective_to",
            "is_current", "actions",
        )
        default_columns = (
            "flat", "owner", "share", "effective_from", "effective_to", "is_current",
        )


class PropertyTenantTable(NetBoxTable):
    flat = tables.Column(linkify=True)
    person = tables.Column(linkify=True)
    effective_from = tables.DateColumn()
    effective_to = tables.DateColumn()
    is_current = columns.BooleanColumn(verbose_name=_("Current"))

    class Meta(NetBoxTable.Meta):
        model = PropertyTenant
        fields = (
            "pk", "flat", "person", "effective_from", "effective_to",
            "is_current", "actions",
        )
        default_columns = (
            "flat", "person", "effective_from", "effective_to", "is_current",
        )


# ---------------------------------------------------------------------------
#  Compact tables for use in detail view panels
# ---------------------------------------------------------------------------

class PersonCompactTable(NetBoxTable):
    """Compact person table for embedding in PropertyOwner detail view."""
    last_name = tables.Column(linkify=True, verbose_name=_("Last name"))
    first_name = tables.Column(verbose_name=_("First name"))
    title_before = tables.Column(verbose_name=_("Title"))
    email = tables.TemplateColumn(
        template_code='{{ record.email }}',
        verbose_name=_("Email"),
        orderable=False,
    )
    phone = tables.TemplateColumn(
        template_code='{{ record.phone }}',
        verbose_name=_("Phone"),
        orderable=False,
    )
    permanent_address = tables.Column(verbose_name=_("Address"))

    class Meta(NetBoxTable.Meta):
        model = Person
        fields = (
            "last_name", "first_name", "title_before", "email", "phone",
            "permanent_address",
        )
        default_columns = (
            "last_name", "first_name", "title_before", "email", "phone",
            "permanent_address",
        )


class CurrentOwnerTable(NetBoxTable):
    """Shows current owners of a flat (FlatOwner where effective_to is null)."""
    owner = tables.Column(linkify=True, verbose_name=_("Owner"))
    share = tables.Column(accessor="share", orderable=False, verbose_name=_("Share"))
    effective_from = tables.DateColumn(verbose_name=_("Since"))

    class Meta(NetBoxTable.Meta):
        model = FlatOwner
        fields = ("owner", "share", "effective_from")
        default_columns = ("owner", "share", "effective_from")


class PersonOwnershipTable(NetBoxTable):
    """Flat ownerships for the Person detail view (via the linked PropertyOwner)."""
    owner = tables.Column(
        accessor="owner", linkify=True, verbose_name=_("Owner record"),
    )
    flat = tables.Column(linkify=True, verbose_name=_("Flat"))
    share = tables.Column(accessor="share", orderable=False, verbose_name=_("Share"))
    effective_from = tables.DateColumn(verbose_name=_("From"))
    effective_to = tables.DateColumn(verbose_name=_("To"))
    is_current = columns.BooleanColumn(verbose_name=_("Current"))

    class Meta(NetBoxTable.Meta):
        model = FlatOwner
        fields = ("owner", "flat", "share", "effective_from", "effective_to", "is_current")
        default_columns = ("owner", "flat", "share", "effective_from", "effective_to", "is_current")
        order_by = ("-effective_from",)
