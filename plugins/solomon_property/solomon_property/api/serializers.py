"""Solomon Property - REST API serializers."""

from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer

from solomon_property.models import Building, Flat, FlatOwner, PropertyOwner, Person, PropertyTenant


class BuildingSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_property-api:building-detail"
    )

    class Meta:
        model = Building
        fields = [
            "id", "url", "display", "name", "street", "house_number",
            "city", "postal_code", "number_of_floors", "elevator",
            "year_built", "total_units", "land_plot_number",
            "common_rooms", "floor_plan_url", "common_area_rental",
            "note", "cuzk_building_id", "cuzk_lv_number",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "house_number"]


class FlatSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_property-api:flat-detail"
    )
    building = BuildingSerializer(nested=True)

    class Meta:
        model = Flat
        fields = [
            "id", "url", "display", "building", "flat_number", "floor",
            "area_m2", "disposition", "number_of_rooms",
            "water_outlets", "waste_outlets",
            "radiator_count", "radiator_power_kw",
            "gas_installed", "has_balcony", "cellar_unit",
            "ownership_cert_number", "note",
            "cuzk_unit_id", "cuzk_share_numerator", "cuzk_share_denominator",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "flat_number"]


class PersonSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_property-api:person-detail"
    )

    class Meta:
        model = Person
        fields = [
            "id", "url", "display",
            "title_before", "first_name", "last_name", "title_after",
            "emails", "phones", "date_of_birth",
            "permanent_address", "contact_address", "note",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "first_name", "last_name"]


class PropertyOwnerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_property-api:propertyowner-detail"
    )
    persons = PersonSerializer(nested=True, many=True, read_only=True)

    class Meta:
        model = PropertyOwner
        fields = [
            "id", "url", "display", "display_name", "person_type",
            "persons", "email", "phone",
            "permanent_address", "contact_address",
            "deputy_name", "deputy_contact", "note",
            "cuzk_owner_id",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display", "display_name", "person_type"]


class FlatOwnerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_property-api:flatowner-detail"
    )
    flat = FlatSerializer(nested=True)
    owner = PropertyOwnerSerializer(nested=True)

    class Meta:
        model = FlatOwner
        fields = [
            "id", "url", "display", "flat", "owner",
            "share_numerator", "share_denominator",
            "effective_from", "effective_to",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display"]


class PropertyTenantSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:solomon_property-api:propertytenant-detail"
    )
    flat = FlatSerializer(nested=True)
    person = PersonSerializer(nested=True)

    class Meta:
        model = PropertyTenant
        fields = [
            "id", "url", "display", "flat", "person",
            "effective_from", "effective_to", "note",
            "tags", "custom_fields", "created", "last_updated",
        ]
        brief_fields = ["id", "url", "display"]
