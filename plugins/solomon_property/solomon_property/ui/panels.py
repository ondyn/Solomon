"""Solomon Property - UI panel definitions for detail views."""

from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels


# ---------------------------------------------------------------------------
#  Building Object panel
# ---------------------------------------------------------------------------

class BuildingObjectPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    cuzk_building_id = attrs.TextAttr('cuzk_building_id', label=_('CUZK building object ID'))
    municipality_name = attrs.TextAttr('municipality_name', label=_('Municipality'))
    city_part_name = attrs.TextAttr('city_part_name', label=_('City part'))
    cadastral_territory_name = attrs.TextAttr('cadastral_territory_name', label=_('Cadastral territory'))
    house_numbers = attrs.TextAttr('house_numbers', label=_('House numbers'))


class BuildingObjectTechnicalPanel(panels.ObjectAttributesPanel):
    title = _('Type & Usage')
    building_type_name = attrs.TextAttr('building_type_name', label=_('Building type'))
    usage_name = attrs.TextAttr('usage_name', label=_('Usage'))
    lv_number = attrs.TextAttr('lv_number', label=_('Title deed (LV)'))


class BuildingObjectNotesPanel(panels.ObjectAttributesPanel):
    title = _('Notes')
    note = attrs.TextAttr('note', label=_('Note'))


# ---------------------------------------------------------------------------
#  Building panel
# ---------------------------------------------------------------------------

class BuildingPanel(panels.ObjectAttributesPanel):
    building_object = attrs.RelatedObjectAttr('building_object', label=_('Building object'), linkify=True)
    name = attrs.TextAttr('name', label=_('Name'))
    street = attrs.TextAttr('street', label=_('Street'))
    house_number = attrs.TextAttr('house_number', label=_('House number'))
    city = attrs.TextAttr('city', label=_('City'))
    postal_code = attrs.TextAttr('postal_code', label=_('Postal code'))
    number_of_floors = attrs.TextAttr('number_of_floors', label=_('Number of floors'))
    elevator = attrs.BooleanAttr('elevator', label=_('Elevator'))
    year_built = attrs.TextAttr('year_built', label=_('Year built'))
    total_units = attrs.TextAttr('total_units', label=_('Total units'))
    land_plot_number = attrs.TextAttr('land_plot_number', label=_('Land plot number'))
    floor_plan_url = attrs.TextAttr('floor_plan_url', label=_('Floor plan URL'))


class BuildingCuzkPanel(panels.ObjectAttributesPanel):
    title = _('CUZK Integration')
    cuzk_building_id = attrs.TextAttr('cuzk_building_id', label=_('CUZK building ID'))
    cuzk_lv_number = attrs.TextAttr('cuzk_lv_number', label=_('CUZK LV number'))


class BuildingNotesPanel(panels.ObjectAttributesPanel):
    title = _('Notes & Extras')
    common_rooms = attrs.TextAttr('common_rooms', label=_('Common rooms'))
    common_area_rental = attrs.TextAttr('common_area_rental', label=_('Common area rental info'))
    note = attrs.TextAttr('note', label=_('Note'))


# ---------------------------------------------------------------------------
#  Flat panel
# ---------------------------------------------------------------------------

class FlatPanel(panels.ObjectAttributesPanel):
    building = attrs.RelatedObjectAttr('building', label=_('Building'), linkify=True)
    flat_number = attrs.TextAttr('flat_number', label=_('Flat number'))
    floor = attrs.TextAttr('floor', label=_('Floor'))
    area_m2 = attrs.TextAttr('area_m2', label=_('Area (m²)'))
    disposition = attrs.ChoiceAttr('disposition', label=_('Disposition'))
    number_of_rooms = attrs.TextAttr('number_of_rooms', label=_('Number of rooms'))


class FlatInstallationsPanel(panels.ObjectAttributesPanel):
    title = _('Installations & Features')
    water_outlets = attrs.TextAttr('water_outlets', label=_('Water outlets'))
    waste_outlets = attrs.TextAttr('waste_outlets', label=_('Waste outlets'))
    radiator_count = attrs.TextAttr('radiator_count', label=_('Radiator count'))
    radiator_power_kw = attrs.TextAttr('radiator_power_kw', label=_('Radiator power (kW)'))
    gas_installed = attrs.BooleanAttr('gas_installed', label=_('Gas installed'))
    has_balcony = attrs.BooleanAttr('has_balcony', label=_('Has balcony'))
    cellar_unit = attrs.TextAttr('cellar_unit', label=_('Cellar unit'))


class FlatCuzkPanel(panels.ObjectAttributesPanel):
    title = _('CUZK / Ownership')
    ownership_cert_number = attrs.TextAttr('ownership_cert_number', label=_('Ownership certificate number'))
    cuzk_unit_id = attrs.TextAttr('cuzk_unit_id', label=_('CUZK unit ID'))
    cuzk_share = attrs.TextAttr('cuzk_share', label=_('CUZK common parts share'))


class FlatNotesPanel(panels.ObjectAttributesPanel):
    title = _('Notes')
    note = attrs.TextAttr('note', label=_('Note'))


# ---------------------------------------------------------------------------
#  Person panel
# ---------------------------------------------------------------------------

class PersonPanel(panels.ObjectAttributesPanel):
    title_before = attrs.TextAttr('title_before', label=_('Title before name'))
    first_name = attrs.TextAttr('first_name', label=_('First name'))
    last_name = attrs.TextAttr('last_name', label=_('Last name'))
    title_after = attrs.TextAttr('title_after', label=_('Title after name'))
    emails = attrs.TemplatedAttr(
        'emails',
        label=_('Emails'),
        template_name='solomon_property/attrs/array_list.html',
    )
    phones = attrs.TemplatedAttr(
        'phones',
        label=_('Phones'),
        template_name='solomon_property/attrs/array_list.html',
    )
    date_of_birth = attrs.TextAttr('date_of_birth', label=_('Date of birth'))


class PersonAddressPanel(panels.ObjectAttributesPanel):
    title = _('Addresses')
    permanent_address = attrs.TextAttr('permanent_address', label=_('Permanent address'))
    contact_address = attrs.TextAttr('contact_address', label=_('Contact address'))


class PersonNotesPanel(panels.ObjectAttributesPanel):
    title = _('Notes')
    note = attrs.TextAttr('note', label=_('Note'))


# ---------------------------------------------------------------------------
#  PropertyOwner panel
# ---------------------------------------------------------------------------

class PropertyOwnerPanel(panels.ObjectAttributesPanel):
    display_name = attrs.TextAttr('display_name', label=_('Display name'))
    person_type = attrs.ChoiceAttr('person_type', label=_('Person type'))
    current_total_share = attrs.TextAttr('current_total_share', label=_('Total active share'))
    email = attrs.TextAttr('email', label=_('Email'))
    phone = attrs.TextAttr('phone', label=_('Phone'))


class PropertyOwnerAddressPanel(panels.ObjectAttributesPanel):
    title = _('Addresses')
    permanent_address = attrs.TextAttr('permanent_address', label=_('Permanent address'))
    contact_address = attrs.TextAttr('contact_address', label=_('Contact address'))


class PropertyOwnerDeputyPanel(panels.ObjectAttributesPanel):
    title = _('Deputy / Representative')
    deputy_name = attrs.TextAttr('deputy_name', label=_('Deputy name'))
    deputy_contact = attrs.TextAttr('deputy_contact', label=_('Deputy contact'))


class PropertyOwnerCuzkPanel(panels.ObjectAttributesPanel):
    title = _('CUZK Integration')
    cuzk_owner_id = attrs.TextAttr('cuzk_owner_id', label=_('CUZK owner ID'))


class PropertyOwnerNotesPanel(panels.ObjectAttributesPanel):
    title = _('Notes')
    note = attrs.TextAttr('note', label=_('Note'))


# ---------------------------------------------------------------------------
#  FlatOwner panel
# ---------------------------------------------------------------------------

class FlatOwnerPanel(panels.ObjectAttributesPanel):
    flat = attrs.RelatedObjectAttr('flat', label=_('Flat'), linkify=True)
    owner = attrs.RelatedObjectAttr('owner', label=_('Owner'), linkify=True)
    share = attrs.TextAttr('share', label=_('Ownership share'))
    effective_from = attrs.TextAttr('effective_from', label=_('Effective from'))
    effective_to = attrs.TextAttr('effective_to', label=_('Effective to'))
    is_current = attrs.BooleanAttr('is_current', label=_('Current'))


# ---------------------------------------------------------------------------
#  PropertyTenant panel
# ---------------------------------------------------------------------------

class PropertyTenantPanel(panels.ObjectAttributesPanel):
    flat = attrs.RelatedObjectAttr('flat', label=_('Flat'), linkify=True)
    person = attrs.RelatedObjectAttr('person', label=_('Person'), linkify=True)
    effective_from = attrs.TextAttr('effective_from', label=_('Effective from'))
    effective_to = attrs.TextAttr('effective_to', label=_('Effective to'))
    is_current = attrs.BooleanAttr('is_current', label=_('Current'))


class PropertyTenantNotesPanel(panels.ObjectAttributesPanel):
    title = _('Notes')
    note = attrs.TextAttr('note', label=_('Note'))
