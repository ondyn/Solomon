from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer

from .. import models


class FacilitiesSerializer(NetBoxModelSerializer):
    serializer_url_name = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.serializer_url_name:
            cls._declared_fields["url"] = serializers.HyperlinkedIdentityField(
                view_name=f"plugins-api:solomon_facilities-api:{cls.serializer_url_name}-detail"
            )


class BuildingLevelSerializer(FacilitiesSerializer):
    serializer_url_name = "buildinglevel"

    class Meta:
        model = models.BuildingLevel
        fields = (
            "id",
            "url",
            "display",
            "building_object",
            "number",
            "reference",
            "name",
            "elevation_m",
            "height_m",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class FloorPlanSerializer(FacilitiesSerializer):
    serializer_url_name = "floorplan"

    class Meta:
        model = models.FloorPlan
        fields = (
            "id",
            "url",
            "display",
            "level",
            "name",
            "width",
            "height",
            "measurement_unit",
            "active_revision",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class PlanRevisionSerializer(FacilitiesSerializer):
    serializer_url_name = "planrevision"

    class Meta:
        model = models.PlanRevision
        fields = (
            "id",
            "url",
            "display",
            "plan",
            "revision",
            "status",
            "source_file",
            "background_file",
            "background_rotation",
            "source_page",
            "scale_denominator",
            "source_note",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class SpaceSerializer(FacilitiesSerializer):
    serializer_url_name = "space"

    class Meta:
        model = models.Space
        fields = (
            "id",
            "url",
            "display",
            "level",
            "building",
            "parent",
            "reference",
            "name",
            "kind",
            "status",
            "area_m2",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class SpaceFlatAssignmentSerializer(FacilitiesSerializer):
    serializer_url_name = "spaceflatassignment"

    class Meta:
        model = models.SpaceFlatAssignment
        fields = (
            "id",
            "url",
            "display",
            "space",
            "flat",
            "role",
            "effective_from",
            "effective_to",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class SpaceUsageSerializer(FacilitiesSerializer):
    serializer_url_name = "spaceusage"

    class Meta:
        model = models.SpaceUsage
        fields = (
            "id",
            "url",
            "display",
            "space",
            "person",
            "owner",
            "usage_type",
            "effective_from",
            "effective_to",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class DoorSerializer(FacilitiesSerializer):
    serializer_url_name = "door"

    class Meta:
        model = models.Door
        fields = (
            "id",
            "url",
            "display",
            "level",
            "reference",
            "name",
            "door_type",
            "from_space",
            "to_space",
            "fire_rating",
            "emergency_exit",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class LockCylinderSerializer(FacilitiesSerializer):
    serializer_url_name = "lockcylinder"

    class Meta:
        model = models.LockCylinder
        fields = (
            "id",
            "url",
            "display",
            "door",
            "name",
            "code",
            "active_from",
            "active_to",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class KeyProfileSerializer(FacilitiesSerializer):
    serializer_url_name = "keyprofile"

    class Meta:
        model = models.KeyProfile
        fields = (
            "id",
            "url",
            "display",
            "building_object",
            "code",
            "name",
            "locks",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class KeyCopySerializer(FacilitiesSerializer):
    serializer_url_name = "keycopy"

    class Meta:
        model = models.KeyCopy
        fields = (
            "id",
            "url",
            "display",
            "profile",
            "inventory_code",
            "serial_number",
            "status",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class KeyIssueSerializer(FacilitiesSerializer):
    serializer_url_name = "keyissue"

    class Meta:
        model = models.KeyIssue
        fields = (
            "id",
            "url",
            "display",
            "key_copy",
            "person",
            "external_holder",
            "issued_at",
            "due_at",
            "returned_at",
            "purpose",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class TechnicalSystemSerializer(FacilitiesSerializer):
    serializer_url_name = "technicalsystem"

    class Meta:
        model = models.TechnicalSystem
        fields = (
            "id",
            "url",
            "display",
            "building_object",
            "name",
            "kind",
            "description",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class TechnicalAssetSerializer(FacilitiesSerializer):
    serializer_url_name = "technicalasset"

    class Meta:
        model = models.TechnicalAsset
        fields = (
            "id",
            "url",
            "display",
            "system",
            "parent",
            "level",
            "space",
            "code",
            "name",
            "asset_type",
            "status",
            "serves_flats",
            "serves_spaces",
            "emergency_instructions",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class TechnicalConnectionSerializer(FacilitiesSerializer):
    serializer_url_name = "technicalconnection"

    class Meta:
        model = models.TechnicalConnection
        fields = (
            "id",
            "url",
            "display",
            "from_asset",
            "to_asset",
            "kind",
            "notes",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )


class PlanElementSerializer(FacilitiesSerializer):
    serializer_url_name = "planelement"

    class Meta:
        model = models.PlanElement
        fields = (
            "id",
            "url",
            "display",
            "revision",
            "element_type",
            "label",
            "geometry",
            "style",
            "z_index",
            "locked",
            "space",
            "door",
            "technical_asset",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        )
