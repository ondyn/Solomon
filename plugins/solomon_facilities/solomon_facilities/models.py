"""Spatial, access-control, and technical facility models for Solomon."""

import math

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel


LEVEL_UNIT_CHOICES = (("m", _("Meters")), ("cm", _("Centimeters")))
REVISION_STATUS_CHOICES = (
    ("draft", _("Draft")),
    ("published", _("Published")),
    ("archived", _("Archived")),
)
SPACE_KIND_CHOICES = (
    ("flat", _("Flat")),
    ("room", _("Room")),
    ("common_room", _("Common room")),
    ("cellar", _("Cellar cubicle")),
    ("corridor", _("Corridor")),
    ("stair", _("Staircase")),
    ("elevator", _("Elevator")),
    ("shaft", _("Service shaft")),
    ("technical_room", _("Technical room")),
    ("balcony", _("Balcony or loggia")),
    ("exterior", _("Exterior")),
    ("other", _("Other")),
)
SPACE_STATUS_CHOICES = (
    ("active", _("Active")),
    ("inactive", _("Inactive")),
    ("planned", _("Planned")),
)
SPACE_ASSIGNMENT_ROLE_CHOICES = (
    ("primary", _("Primary flat area")),
    ("room", _("Room in flat")),
    ("cellar", _("Cellar assigned to flat")),
    ("balcony", _("Balcony or loggia assigned to flat")),
    ("exclusive_use", _("Common area under exclusive use")),
)
SPACE_USAGE_TYPE_CHOICES = (
    ("rental", _("Rental")),
    ("occupancy", _("Occupancy")),
    ("loan", _("Loan")),
    ("license", _("License")),
)
ELEMENT_TYPE_CHOICES = (
    ("wall", _("Wall")),
    ("door", _("Door")),
    ("window", _("Window")),
    ("space", _("Space")),
    ("technical", _("Technical item")),
    ("line", _("Line")),
    ("text", _("Text")),
    ("dimension", _("Dimension")),
)
DOOR_TYPE_CHOICES = (
    ("interior", _("Interior")),
    ("entrance", _("Entrance")),
    ("fire", _("Fire door")),
    ("service", _("Service door")),
    ("gate", _("Gate")),
)
KEY_COPY_STATUS_CHOICES = (
    ("available", _("Available")),
    ("issued", _("Issued")),
    ("lost", _("Lost")),
    ("damaged", _("Damaged")),
    ("retired", _("Retired")),
)
SYSTEM_KIND_CHOICES = (
    ("gas", _("Gas")),
    ("cold_water", _("Cold water")),
    ("hot_water", _("Hot water")),
    ("wastewater", _("Wastewater")),
    ("electrical", _("Electrical")),
    ("low_current", _("Low-current and data")),
    ("heating", _("Heating")),
    ("ventilation", _("Ventilation")),
    ("fire_safety", _("Fire safety")),
    ("other", _("Other")),
)
ASSET_STATUS_CHOICES = (
    ("active", _("Active")),
    ("out_of_service", _("Out of service")),
    ("planned", _("Planned")),
    ("removed", _("Removed")),
)
CONNECTION_KIND_CHOICES = (
    ("feeds", _("Feeds")),
    ("controls", _("Controls")),
    ("isolates", _("Isolates")),
    ("monitors", _("Monitors")),
)


def plan_upload_path(instance, filename):
    building_object_id = instance.plan.level.building_object_id
    return f"solomon-facilities/{building_object_id}/{instance.plan_id}/{filename}"


class BuildingLevel(NetBoxModel):
    """A physical level shared by all entrances in one building object."""

    building_object = models.ForeignKey(
        "solomon_property.BuildingObject",
        on_delete=models.PROTECT,
        related_name="facility_levels",
        verbose_name=_("Building object"),
    )
    number = models.SmallIntegerField(
        verbose_name=_("Level number"),
        help_text=_("Basements are negative; ground floor is zero."),
    )
    reference = models.CharField(
        max_length=20,
        verbose_name=_("Displayed reference"),
        help_text=_("For example 1PP, 1NP, or 4NP."),
    )
    name = models.CharField(max_length=100, blank=True, verbose_name=_("Name"))
    elevation_m = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_("Elevation (m)"),
    )
    height_m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Floor-to-floor height (m)"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("building_object", "number")
        constraints = (
            models.UniqueConstraint(
                fields=("building_object", "number"),
                name="solomon_facilities_unique_level_number",
            ),
            models.UniqueConstraint(
                fields=("building_object", "reference"),
                name="solomon_facilities_unique_level_reference",
            ),
        )
        verbose_name = _("Building level")
        verbose_name_plural = _("Building levels")

    def __str__(self):
        return f"{self.building_object} - {self.reference}"

    def get_absolute_url(self):
        if hasattr(self, "plan"):
            return self.plan.get_absolute_url()
        return reverse("plugins:solomon_facilities:level_list")


class FloorPlan(NetBoxModel):
    """Plan metadata; drawing content is stored in versioned revisions."""

    level = models.OneToOneField(
        BuildingLevel,
        on_delete=models.PROTECT,
        related_name="plan",
        verbose_name=_("Level"),
    )
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1600,
        validators=[MinValueValidator(1)],
        verbose_name=_("Canvas width"),
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=900,
        validators=[MinValueValidator(1)],
        verbose_name=_("Canvas height"),
    )
    measurement_unit = models.CharField(
        max_length=2,
        choices=LEVEL_UNIT_CHOICES,
        default="cm",
        verbose_name=_("Measurement unit"),
    )
    active_revision = models.ForeignKey(
        "PlanRevision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_for_plans",
        verbose_name=_("Active revision"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("level",)
        verbose_name = _("Floor plan")
        verbose_name_plural = _("Floor plans")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:solomon_facilities:floorplan", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()
        if self.active_revision_id and self.active_revision.plan_id != self.pk:
            raise ValidationError(
                {"active_revision": _("The active revision must belong to this plan.")}
            )


class PlanRevision(NetBoxModel):
    """A version of a plan and its source provenance."""

    plan = models.ForeignKey(
        FloorPlan,
        on_delete=models.CASCADE,
        related_name="revisions",
        verbose_name=_("Plan"),
    )
    revision = models.PositiveIntegerField(default=1, verbose_name=_("Revision"))
    status = models.CharField(
        max_length=20,
        choices=REVISION_STATUS_CHOICES,
        default="draft",
        verbose_name=_("Status"),
    )
    source_file = models.FileField(
        upload_to=plan_upload_path,
        blank=True,
        verbose_name=_("Source document"),
    )
    background_file = models.FileField(
        upload_to=plan_upload_path,
        blank=True,
        verbose_name=_("Background image or SVG"),
    )
    background_rotation = models.SmallIntegerField(
        default=0,
        choices=(
            (-270, "-270°"),
            (-180, "-180°"),
            (-90, "-90°"),
            (0, "0°"),
            (90, "90°"),
            (180, "180°"),
            (270, "270°"),
        ),
        verbose_name=_("Background rotation"),
    )
    source_page = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Source page")
    )
    scale_denominator = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name=_("Scale denominator"),
        help_text=_("For a 1:75 drawing, enter 75."),
    )
    source_note = models.TextField(blank=True, verbose_name=_("Source note"))

    class Meta:
        ordering = ("plan", "-revision")
        constraints = (
            models.UniqueConstraint(
                fields=("plan", "revision"),
                name="solomon_facilities_unique_plan_revision",
            ),
        )
        verbose_name = _("Plan revision")
        verbose_name_plural = _("Plan revisions")

    def __str__(self):
        return f"{self.plan} r{self.revision}"

    def get_absolute_url(self):
        return self.plan.get_absolute_url()

    @property
    def is_editable(self):
        return self.status == "draft"


class Space(NetBoxModel):
    """A semantic area such as a flat, room, cubicle, corridor, or shaft."""

    level = models.ForeignKey(
        BuildingLevel,
        on_delete=models.PROTECT,
        related_name="spaces",
        verbose_name=_("Level"),
    )
    building = models.ForeignKey(
        "solomon_property.Building",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="facility_spaces",
        verbose_name=_("Entrance or building"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent space"),
    )
    reference = models.CharField(max_length=80, verbose_name=_("Reference"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    kind = models.CharField(
        max_length=30, choices=SPACE_KIND_CHOICES, verbose_name=_("Type")
    )
    status = models.CharField(
        max_length=20,
        choices=SPACE_STATUS_CHOICES,
        default="active",
        verbose_name=_("Status"),
    )
    area_m2 = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Area (m²)"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("level", "building", "reference")
        constraints = (
            models.UniqueConstraint(
                fields=("level", "reference"),
                name="solomon_facilities_unique_space_reference",
            ),
        )
        verbose_name = _("Space")
        verbose_name_plural = _("Spaces")

    def __str__(self):
        return f"{self.reference} - {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_facilities:space", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()
        if (
            self.building_id
            and self.building.building_object_id != self.level.building_object_id
        ):
            raise ValidationError(
                {
                    "building": _(
                        "The building must belong to the level's building object."
                    )
                }
            )
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError({"parent": _("A space cannot contain itself.")})
            if self.parent.level_id != self.level_id:
                raise ValidationError(
                    {"parent": _("Parent space must be on the same level.")}
                )


class SpaceFlatAssignment(NetBoxModel):
    """Dated relation between a physical space and a legal flat."""

    space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        related_name="flat_assignments",
        verbose_name=_("Space"),
    )
    flat = models.ForeignKey(
        "solomon_property.Flat",
        on_delete=models.PROTECT,
        related_name="space_assignments",
        verbose_name=_("Flat"),
    )
    role = models.CharField(
        max_length=30,
        choices=SPACE_ASSIGNMENT_ROLE_CHOICES,
        verbose_name=_("Assignment type"),
    )
    effective_from = models.DateField(null=True, blank=True, verbose_name=_("From"))
    effective_to = models.DateField(null=True, blank=True, verbose_name=_("To"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("space", "flat")
        constraints = (
            models.UniqueConstraint(
                fields=("space", "flat", "role", "effective_from"),
                name="solomon_facilities_unique_space_flat_assignment",
            ),
        )
        verbose_name = _("Space-to-flat assignment")
        verbose_name_plural = _("Space-to-flat assignments")

    def __str__(self):
        return f"{self.space} - {self.flat} ({self.get_role_display()})"

    def get_absolute_url(self):
        return self.space.get_absolute_url()

    def clean(self):
        super().clean()
        if (
            self.effective_to
            and self.effective_from
            and self.effective_to < self.effective_from
        ):
            raise ValidationError(
                {"effective_to": _("End date cannot precede start date.")}
            )
        if self.flat.building.building_object_id != self.space.level.building_object_id:
            raise ValidationError(
                {"flat": _("The flat and space must be in the same building object.")}
            )
        if self.space.building_id and self.flat.building_id != self.space.building_id:
            raise ValidationError(
                {"flat": _("The flat and space must be in the same entrance.")}
            )
        if (
            self.role in {"primary", "room", "balcony"}
            and self.flat.floor != self.space.level.number
        ):
            raise ValidationError(
                {"flat": _("The flat and assigned space must be on the same level.")}
            )

    @property
    def is_current(self):
        return self.effective_to is None or self.effective_to >= timezone.localdate()


class SpaceUsage(NetBoxModel):
    """Rental or occupancy of a common room or other independently used space."""

    space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        related_name="usages",
        verbose_name=_("Space"),
    )
    person = models.ForeignKey(
        "solomon_property.Person",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="space_usages",
        verbose_name=_("Person"),
    )
    owner = models.ForeignKey(
        "solomon_property.PropertyOwner",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="space_usages",
        verbose_name=_("Owner or organization"),
    )
    usage_type = models.CharField(
        max_length=20,
        choices=SPACE_USAGE_TYPE_CHOICES,
        default="rental",
        verbose_name=_("Usage type"),
    )
    effective_from = models.DateField(verbose_name=_("From"))
    effective_to = models.DateField(null=True, blank=True, verbose_name=_("To"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("space", "-effective_from")
        verbose_name = _("Space usage")
        verbose_name_plural = _("Space usages")

    def __str__(self):
        holder = self.person or self.owner
        return f"{holder} @ {self.space}"

    def get_absolute_url(self):
        return self.space.get_absolute_url()

    def clean(self):
        super().clean()
        if bool(self.person_id) == bool(self.owner_id):
            raise ValidationError(_("Select exactly one person or owner/organization."))
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError(
                {"effective_to": _("End date cannot precede start date.")}
            )

    @property
    def is_current(self):
        return self.effective_to is None or self.effective_to >= timezone.localdate()


class Door(NetBoxModel):
    level = models.ForeignKey(
        BuildingLevel,
        on_delete=models.PROTECT,
        related_name="doors",
        verbose_name=_("Level"),
    )
    reference = models.CharField(max_length=80, verbose_name=_("Reference"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    door_type = models.CharField(
        max_length=20,
        choices=DOOR_TYPE_CHOICES,
        default="interior",
        verbose_name=_("Door type"),
    )
    from_space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="doors_from",
        verbose_name=_("Space A"),
    )
    to_space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="doors_to",
        verbose_name=_("Space B"),
        help_text=_("Leave one side empty for an exterior door."),
    )
    fire_rating = models.CharField(
        max_length=50, blank=True, verbose_name=_("Fire rating")
    )
    emergency_exit = models.BooleanField(
        default=False, verbose_name=_("Emergency exit")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("level", "reference")
        constraints = (
            models.UniqueConstraint(
                fields=("level", "reference"),
                name="solomon_facilities_unique_door_reference",
            ),
        )
        verbose_name = _("Door")
        verbose_name_plural = _("Doors")

    def __str__(self):
        return f"{self.reference} - {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_facilities:door", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()
        if not self.from_space_id and not self.to_space_id:
            raise ValidationError(_("At least one connected space is required."))
        for field_name in ("from_space", "to_space"):
            space = getattr(self, field_name)
            if space and space.level_id != self.level_id:
                raise ValidationError(
                    {field_name: _("Connected spaces must be on the door's level.")}
                )
        if self.from_space_id and self.from_space_id == self.to_space_id:
            raise ValidationError(_("A door must connect two different spaces."))


class LockCylinder(NetBoxModel):
    door = models.ForeignKey(
        Door,
        on_delete=models.PROTECT,
        related_name="locks",
        verbose_name=_("Door"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    code = models.CharField(max_length=100, blank=True, verbose_name=_("Cylinder code"))
    active_from = models.DateField(null=True, blank=True, verbose_name=_("Active from"))
    active_to = models.DateField(null=True, blank=True, verbose_name=_("Active to"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("door", "name")
        constraints = (
            models.UniqueConstraint(
                fields=("door", "name"),
                name="solomon_facilities_unique_lock_name",
            ),
        )
        verbose_name = _("Lock cylinder")
        verbose_name_plural = _("Lock cylinders")

    def __str__(self):
        return f"{self.name} ({self.door})"

    def get_absolute_url(self):
        return self.door.get_absolute_url()

    def clean(self):
        super().clean()
        if self.active_to and self.active_from and self.active_to < self.active_from:
            raise ValidationError(
                {"active_to": _("End date cannot precede start date.")}
            )


class KeyProfile(NetBoxModel):
    """A key cut/profile, including master profiles, which opens one or more locks."""

    building_object = models.ForeignKey(
        "solomon_property.BuildingObject",
        on_delete=models.PROTECT,
        related_name="key_profiles",
        verbose_name=_("Building object"),
    )
    code = models.CharField(max_length=100, verbose_name=_("Profile code"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    locks = models.ManyToManyField(
        LockCylinder,
        through="KeyProfileLock",
        related_name="key_profiles",
        verbose_name=_("Locks opened"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("building_object", "code")
        constraints = (
            models.UniqueConstraint(
                fields=("building_object", "code"),
                name="solomon_facilities_unique_key_profile_code",
            ),
        )
        verbose_name = _("Key profile")
        verbose_name_plural = _("Key profiles")

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:solomon_facilities:keyprofile", kwargs={"pk": self.pk})


class KeyProfileLock(NetBoxModel):
    key_profile = models.ForeignKey(KeyProfile, on_delete=models.CASCADE)
    lock = models.ForeignKey(LockCylinder, on_delete=models.PROTECT)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("key_profile", "lock"),
                name="solomon_facilities_unique_key_profile_lock",
            ),
        )
        verbose_name = _("Key profile lock")
        verbose_name_plural = _("Key profile locks")

    def __str__(self):
        return f"{self.key_profile} opens {self.lock}"

    def clean(self):
        super().clean()
        if (
            self.key_profile.building_object_id
            != self.lock.door.level.building_object_id
        ):
            raise ValidationError(
                _("The key profile and lock must belong to the same building object.")
            )


class KeyCopy(NetBoxModel):
    profile = models.ForeignKey(
        KeyProfile,
        on_delete=models.PROTECT,
        related_name="copies",
        verbose_name=_("Key profile"),
    )
    inventory_code = models.CharField(
        max_length=100, unique=True, verbose_name=_("Inventory code")
    )
    serial_number = models.CharField(
        max_length=100, blank=True, verbose_name=_("Serial number")
    )
    status = models.CharField(
        max_length=20,
        choices=KEY_COPY_STATUS_CHOICES,
        default="available",
        verbose_name=_("Status"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("profile", "inventory_code")
        verbose_name = _("Physical key")
        verbose_name_plural = _("Physical keys")

    def __str__(self):
        return f"{self.inventory_code} ({self.profile.code})"

    def get_absolute_url(self):
        return reverse("plugins:solomon_facilities:keycopy", kwargs={"pk": self.pk})


class KeyIssue(NetBoxModel):
    """Append-oriented custody history for a single physical key."""

    key_copy = models.ForeignKey(
        KeyCopy,
        on_delete=models.PROTECT,
        related_name="issues",
        verbose_name=_("Physical key"),
    )
    person = models.ForeignKey(
        "solomon_property.Person",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="key_issues",
        verbose_name=_("Holder"),
    )
    external_holder = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("External holder"),
        help_text=_("For a contractor or organization not stored as a person."),
    )
    issued_at = models.DateTimeField(default=timezone.now, verbose_name=_("Issued at"))
    due_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Due at"))
    returned_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Returned at")
    )
    purpose = models.CharField(max_length=200, blank=True, verbose_name=_("Purpose"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("-issued_at",)
        constraints = (
            models.UniqueConstraint(
                fields=("key_copy",),
                condition=Q(returned_at__isnull=True),
                name="solomon_facilities_one_active_key_issue",
            ),
        )
        verbose_name = _("Key issue")
        verbose_name_plural = _("Key issues")

    def __str__(self):
        holder = self.person or self.external_holder
        return f"{self.key_copy} - {holder}"

    def get_absolute_url(self):
        return self.key_copy.get_absolute_url()

    def clean(self):
        super().clean()
        if not self.person_id and not self.external_holder.strip():
            raise ValidationError(_("Select a person or enter an external holder."))
        unavailable_statuses = {"lost", "damaged", "retired"}
        if self.returned_at is None and self.key_copy.status in unavailable_statuses:
            raise ValidationError(
                {"key_copy": _("A lost, damaged, or retired key cannot be issued.")}
            )
        if self.due_at and self.due_at < self.issued_at:
            raise ValidationError({"due_at": _("Due date cannot precede issue date.")})
        if self.returned_at and self.returned_at < self.issued_at:
            raise ValidationError(
                {"returned_at": _("Return date cannot precede issue date.")}
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._sync_key_copy_status()

    def delete(self, *args, **kwargs):
        key_copy = self.key_copy
        result = super().delete(*args, **kwargs)
        self.key_copy = key_copy
        self._sync_key_copy_status()
        return result

    def _sync_key_copy_status(self):
        key_copy = self.key_copy
        has_active_issue = key_copy.issues.filter(returned_at__isnull=True).exists()
        if has_active_issue and key_copy.status not in {"lost", "damaged", "retired"}:
            status = "issued"
        elif not has_active_issue and key_copy.status == "issued":
            status = "available"
        else:
            return
        key_copy.status = status
        key_copy.save(update_fields=("status",))


class TechnicalSystem(NetBoxModel):
    building_object = models.ForeignKey(
        "solomon_property.BuildingObject",
        on_delete=models.PROTECT,
        related_name="technical_systems",
        verbose_name=_("Building object"),
    )
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    kind = models.CharField(
        max_length=30, choices=SYSTEM_KIND_CHOICES, verbose_name=_("System type")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        ordering = ("building_object", "kind", "name")
        constraints = (
            models.UniqueConstraint(
                fields=("building_object", "name"),
                name="solomon_facilities_unique_system_name",
            ),
        )
        verbose_name = _("Technical system")
        verbose_name_plural = _("Technical systems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "plugins:solomon_facilities:technicalsystem", kwargs={"pk": self.pk}
        )


class TechnicalAsset(NetBoxModel):
    system = models.ForeignKey(
        TechnicalSystem,
        on_delete=models.PROTECT,
        related_name="assets",
        verbose_name=_("System"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent component"),
    )
    level = models.ForeignKey(
        BuildingLevel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="technical_assets",
        verbose_name=_("Level"),
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="technical_assets",
        verbose_name=_("Space"),
    )
    code = models.CharField(max_length=100, verbose_name=_("Asset code"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    asset_type = models.CharField(
        max_length=100,
        verbose_name=_("Component type"),
        help_text=_(
            "For example valve, riser, switchboard, meter, or distribution board."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=ASSET_STATUS_CHOICES,
        default="active",
        verbose_name=_("Status"),
    )
    serves_flats = models.ManyToManyField(
        "solomon_property.Flat",
        blank=True,
        related_name="technical_assets",
        verbose_name=_("Affected flats"),
    )
    serves_spaces = models.ManyToManyField(
        Space,
        blank=True,
        related_name="served_by_assets",
        verbose_name=_("Affected spaces"),
    )
    emergency_instructions = models.TextField(
        blank=True, verbose_name=_("Emergency instructions")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("system", "code")
        constraints = (
            models.UniqueConstraint(
                fields=("system", "code"),
                name="solomon_facilities_unique_asset_code",
            ),
        )
        verbose_name = _("Technical asset")
        verbose_name_plural = _("Technical assets")

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse(
            "plugins:solomon_facilities:technicalasset", kwargs={"pk": self.pk}
        )

    def clean(self):
        super().clean()
        building_object_id = self.system.building_object_id
        if self.level_id and self.level.building_object_id != building_object_id:
            raise ValidationError(
                {
                    "level": _(
                        "The level and system must belong to the same building object."
                    )
                }
            )
        if self.space_id:
            if self.space.level.building_object_id != building_object_id:
                raise ValidationError(
                    {
                        "space": _(
                            "The space and system must belong to the same building object."
                        )
                    }
                )
            if self.level_id and self.space.level_id != self.level_id:
                raise ValidationError(
                    {"space": _("The space must be on the selected level.")}
                )
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError({"parent": _("An asset cannot contain itself.")})
            if self.parent.system_id != self.system_id:
                raise ValidationError(
                    {"parent": _("Parent asset must belong to the same system.")}
                )


class TechnicalConnection(NetBoxModel):
    from_asset = models.ForeignKey(
        TechnicalAsset,
        on_delete=models.CASCADE,
        related_name="outgoing_connections",
        verbose_name=_("From component"),
    )
    to_asset = models.ForeignKey(
        TechnicalAsset,
        on_delete=models.CASCADE,
        related_name="incoming_connections",
        verbose_name=_("To component"),
    )
    kind = models.CharField(
        max_length=20,
        choices=CONNECTION_KIND_CHOICES,
        default="feeds",
        verbose_name=_("Relationship"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ("from_asset", "to_asset")
        constraints = (
            models.UniqueConstraint(
                fields=("from_asset", "to_asset", "kind"),
                name="solomon_facilities_unique_asset_connection",
            ),
        )
        verbose_name = _("Technical connection")
        verbose_name_plural = _("Technical connections")

    def __str__(self):
        return f"{self.from_asset} {self.get_kind_display()} {self.to_asset}"

    def get_absolute_url(self):
        return self.from_asset.get_absolute_url()

    def clean(self):
        super().clean()
        if self.from_asset_id == self.to_asset_id:
            raise ValidationError(_("A component cannot connect to itself."))
        if self.from_asset.system_id != self.to_asset.system_id:
            raise ValidationError(
                _("Connected components must belong to the same system.")
            )


class PlanElement(NetBoxModel):
    """Canonical geometry for one plan revision, independent of the editor library."""

    revision = models.ForeignKey(
        PlanRevision,
        on_delete=models.CASCADE,
        related_name="elements",
        verbose_name=_("Plan revision"),
    )
    element_type = models.CharField(
        max_length=20, choices=ELEMENT_TYPE_CHOICES, verbose_name=_("Element type")
    )
    label = models.CharField(max_length=200, blank=True, verbose_name=_("Label"))
    geometry = models.JSONField(default=dict, verbose_name=_("Geometry"))
    style = models.JSONField(default=dict, blank=True, verbose_name=_("Style"))
    z_index = models.IntegerField(default=0, verbose_name=_("Layer order"))
    locked = models.BooleanField(default=False, verbose_name=_("Locked"))
    space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="plan_elements",
        verbose_name=_("Space"),
    )
    door = models.ForeignKey(
        Door,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="plan_elements",
        verbose_name=_("Door"),
    )
    technical_asset = models.ForeignKey(
        TechnicalAsset,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="plan_elements",
        verbose_name=_("Technical asset"),
    )

    class Meta:
        ordering = ("revision", "z_index", "pk")
        verbose_name = _("Plan element")
        verbose_name_plural = _("Plan elements")

    def __str__(self):
        return self.label or f"{self.get_element_type_display()} #{self.pk}"

    def get_absolute_url(self):
        return self.revision.plan.get_absolute_url()

    def clean(self):
        super().clean()
        targets = (self.space_id, self.door_id, self.technical_asset_id)
        if sum(bool(target) for target in targets) > 1:
            raise ValidationError(
                _("A plan element can link to only one facility object.")
            )
        self._validate_geometry()

        plan_level_id = self.revision.plan.level_id
        if self.space_id and self.space.level_id != plan_level_id:
            raise ValidationError(
                {"space": _("The linked space must be on this plan's level.")}
            )
        if self.door_id and self.door.level_id != plan_level_id:
            raise ValidationError(
                {"door": _("The linked door must be on this plan's level.")}
            )
        if self.technical_asset_id and self.technical_asset.level_id != plan_level_id:
            raise ValidationError(
                {"technical_asset": _("The linked asset must be on this plan's level.")}
            )

    def _validate_geometry(self):
        if not isinstance(self.geometry, dict):
            raise ValidationError({"geometry": _("Geometry must be a JSON object.")})
        geometry_type = self.geometry.get("type")
        if geometry_type not in {
            "rect",
            "line",
            "polyline",
            "polygon",
            "point",
            "text",
        }:
            raise ValidationError({"geometry": _("Unsupported geometry type.")})

        numbers = []
        for key in ("x", "y", "width", "height", "x1", "y1", "x2", "y2"):
            value = self.geometry.get(key)
            if value is not None:
                numbers.append(value)
        for point in self.geometry.get("points", []):
            if not isinstance(point, dict):
                raise ValidationError(
                    {"geometry": _("Every point must be a JSON object.")}
                )
            numbers.extend((point.get("x"), point.get("y")))
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in numbers
        ):
            raise ValidationError(
                {"geometry": _("Geometry coordinates must be finite numbers.")}
            )
