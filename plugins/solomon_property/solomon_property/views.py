"""Solomon Property - Views (CRUD) for all property models."""

from django.utils.translation import gettext_lazy as _

from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import layout
from netbox.ui.panels import ContextTablePanel
from netbox.views import generic

from . import filtersets, filterforms, forms, models, tables
from .ui.panels import (
    BuildingObjectNotesPanel,
    BuildingObjectPanel,
    BuildingObjectTechnicalPanel,
    BuildingCuzkPanel,
    BuildingNotesPanel,
    BuildingPanel,
    FlatCuzkPanel,
    FlatInstallationsPanel,
    FlatNotesPanel,
    FlatOwnerPanel,
    FlatPanel,
    PersonAddressPanel,
    PersonNotesPanel,
    PersonPanel,
    PropertyOwnerAddressPanel,
    PropertyOwnerCuzkPanel,
    PropertyOwnerDeputyPanel,
    PropertyOwnerNotesPanel,
    PropertyOwnerPanel,
    PropertyTenantNotesPanel,
    PropertyTenantPanel,
)


# ---------------------------------------------------------------------------
#  BuildingObject views
# ---------------------------------------------------------------------------


class BuildingObjectListView(generic.ObjectListView):
    queryset = models.BuildingObject.objects.all()
    table = tables.BuildingObjectTable
    filterset = filtersets.BuildingObjectFilterSet
    filterset_form = filterforms.BuildingObjectFilterForm


class BuildingObjectView(generic.ObjectView):
    queryset = models.BuildingObject.objects.prefetch_related("buildings")
    layout = layout.SimpleLayout(
        left_panels=[
            BuildingObjectPanel(),
            BuildingObjectNotesPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[
            BuildingObjectTechnicalPanel(),
        ],
        bottom_panels=[
            ContextTablePanel(table="building_table", title=_("Buildings")),
        ],
    )

    def get_extra_context(self, request, instance):
        building_table = tables.BuildingTable(instance.buildings.all())
        building_table.configure(request)
        return {
            "building_table": building_table,
            "building_count": instance.buildings.count(),
        }


class BuildingObjectEditView(generic.ObjectEditView):
    queryset = models.BuildingObject.objects.all()
    form = forms.BuildingObjectForm


class BuildingObjectDeleteView(generic.ObjectDeleteView):
    queryset = models.BuildingObject.objects.all()


class BuildingObjectBulkDeleteView(generic.BulkDeleteView):
    queryset = models.BuildingObject.objects.all()
    table = tables.BuildingObjectTable


# ---------------------------------------------------------------------------
#  Building views
# ---------------------------------------------------------------------------


class BuildingListView(generic.ObjectListView):
    queryset = models.Building.objects.select_related("building_object")
    table = tables.BuildingTable
    filterset = filtersets.BuildingFilterSet
    filterset_form = filterforms.BuildingFilterForm


class BuildingView(generic.ObjectView):
    queryset = models.Building.objects.select_related(
        "building_object"
    ).prefetch_related("flats")
    layout = layout.SimpleLayout(
        left_panels=[
            BuildingPanel(),
            BuildingNotesPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[
            BuildingCuzkPanel(),
        ],
        bottom_panels=[
            ContextTablePanel(table="flat_table", title=_("Flats")),
        ],
    )

    def get_extra_context(self, request, instance):
        flats = instance.flats.all()
        flat_table = tables.FlatTable(flats)
        flat_table.configure(request)
        return {"flat_table": flat_table, "flat_count": flats.count()}


class BuildingEditView(generic.ObjectEditView):
    queryset = models.Building.objects.all()
    form = forms.BuildingForm


class BuildingDeleteView(generic.ObjectDeleteView):
    queryset = models.Building.objects.all()


class BuildingBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Building.objects.all()
    table = tables.BuildingTable


# ---------------------------------------------------------------------------
#  Flat views
# ---------------------------------------------------------------------------


class FlatListView(generic.ObjectListView):
    queryset = models.Flat.objects.select_related("building")
    table = tables.FlatTable
    filterset = filtersets.FlatFilterSet
    filterset_form = filterforms.FlatFilterForm


class FlatView(generic.ObjectView):
    queryset = models.Flat.objects.select_related("building").prefetch_related(
        "flat_owners__owner__persons",
        "tenants__person",
    )
    layout = layout.SimpleLayout(
        left_panels=[
            FlatPanel(),
            FlatInstallationsPanel(),
            FlatNotesPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[
            FlatCuzkPanel(),
        ],
        bottom_panels=[
            ContextTablePanel(table="current_owner_table", title=_("Current Owners")),
            ContextTablePanel(table="owner_table", title=_("Ownership History")),
            ContextTablePanel(table="propertytenant_table", title=_("Tenants")),
        ],
    )

    def get_extra_context(self, request, instance):
        current_owners_qs = instance.flat_owners.filter(
            effective_to__isnull=True
        ).select_related("owner")
        current_owner_table = tables.CurrentOwnerTable(
            current_owners_qs, orderable=False
        )
        current_owner_table.configure(request)

        owner_table = tables.FlatOwnerTable(
            instance.flat_owners.select_related("owner").order_by(
                "-effective_from", "-pk"
            ),
            orderable=False,
        )
        owner_table.configure(request)
        tenant_table = tables.PropertyTenantTable(
            instance.tenants.select_related("person"), orderable=False
        )
        tenant_table.configure(request)
        return {
            "current_owner_table": current_owner_table,
            "owner_table": owner_table,
            "propertytenant_table": tenant_table,
        }


class FlatEditView(generic.ObjectEditView):
    queryset = models.Flat.objects.all()
    form = forms.FlatForm


class FlatDeleteView(generic.ObjectDeleteView):
    queryset = models.Flat.objects.all()


class FlatBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Flat.objects.all()
    table = tables.FlatTable


# ---------------------------------------------------------------------------
#  Person views
# ---------------------------------------------------------------------------


class PersonListView(generic.ObjectListView):
    queryset = models.Person.objects.all()
    table = tables.PersonTable
    filterset = filtersets.PersonFilterSet
    filterset_form = filterforms.PersonFilterForm


class PersonView(generic.ObjectView):
    queryset = models.Person.objects.prefetch_related(
        "ownerships__flat_owners__flat__building",
        "tenancies__flat__building",
    )
    layout = layout.SimpleLayout(
        left_panels=[
            PersonPanel(),
            PersonAddressPanel(),
            PersonNotesPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[],
        bottom_panels=[
            ContextTablePanel(table="ownership_table", title=_("Flat Ownerships")),
            ContextTablePanel(table="tenancy_table", title=_("Tenancies")),
        ],
    )

    def get_extra_context(self, request, instance):
        # Collect all FlatOwner rows across all PropertyOwner records this person is linked to
        flat_owner_ids = list(
            models.FlatOwner.objects.filter(owner__persons=instance)
            .select_related("owner", "flat__building")
            .values_list("pk", flat=True)
        )
        flat_owners_qs = (
            models.FlatOwner.objects.filter(pk__in=flat_owner_ids)
            .select_related("owner", "flat__building")
            .order_by("-effective_from", "-pk")
        )
        ownership_table = tables.PersonOwnershipTable(flat_owners_qs, orderable=False)
        ownership_table.configure(request)

        tenancies = instance.tenancies.select_related("flat__building")
        tenancy_table = tables.PropertyTenantTable(tenancies, orderable=False)
        tenancy_table.configure(request)
        return {
            "ownership_table": ownership_table,
            "tenancy_table": tenancy_table,
        }


class PersonEditView(generic.ObjectEditView):
    queryset = models.Person.objects.all()
    form = forms.PersonForm


class PersonDeleteView(generic.ObjectDeleteView):
    queryset = models.Person.objects.all()


class PersonBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Person.objects.all()
    table = tables.PersonTable


# ---------------------------------------------------------------------------
#  PropertyOwner views
# ---------------------------------------------------------------------------


class PropertyOwnerListView(generic.ObjectListView):
    queryset = models.PropertyOwner.objects.prefetch_related("persons")
    table = tables.PropertyOwnerTable
    filterset = filtersets.PropertyOwnerFilterSet
    filterset_form = filterforms.PropertyOwnerFilterForm


class PropertyOwnerView(generic.ObjectView):
    queryset = models.PropertyOwner.objects.prefetch_related(
        "persons", "flat_owners__flat__building"
    )
    layout = layout.SimpleLayout(
        left_panels=[
            PropertyOwnerPanel(),
            PropertyOwnerAddressPanel(),
            PropertyOwnerDeputyPanel(),
            PropertyOwnerNotesPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[
            PropertyOwnerCuzkPanel(),
        ],
        bottom_panels=[
            ContextTablePanel(table="person_table", title=_("Persons")),
            ContextTablePanel(table="flat_owner_table", title=_("Flat Ownerships")),
        ],
    )

    def get_extra_context(self, request, instance):
        flat_owners = instance.flat_owners.select_related("flat__building")
        fo_table = tables.FlatOwnerTable(flat_owners, orderable=False)
        fo_table.configure(request)
        person_table = tables.PersonCompactTable(
            instance.persons.all(), orderable=False
        )
        person_table.configure(request)
        return {
            "flat_owner_table": fo_table,
            "person_table": person_table,
        }


class PropertyOwnerEditView(generic.ObjectEditView):
    queryset = models.PropertyOwner.objects.all()
    form = forms.PropertyOwnerForm


class PropertyOwnerDeleteView(generic.ObjectDeleteView):
    queryset = models.PropertyOwner.objects.all()


class PropertyOwnerBulkDeleteView(generic.BulkDeleteView):
    queryset = models.PropertyOwner.objects.all()
    table = tables.PropertyOwnerTable


# ---------------------------------------------------------------------------
#  FlatOwner views
# ---------------------------------------------------------------------------


class FlatOwnerListView(generic.ObjectListView):
    queryset = models.FlatOwner.objects.select_related("flat__building", "owner")
    table = tables.FlatOwnerTable
    filterset = filtersets.FlatOwnerFilterSet
    filterset_form = filterforms.FlatOwnerFilterForm


class FlatOwnerView(generic.ObjectView):
    queryset = models.FlatOwner.objects.select_related("flat__building", "owner")
    layout = layout.SimpleLayout(
        left_panels=[
            FlatOwnerPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[],
    )


class FlatOwnerEditView(generic.ObjectEditView):
    queryset = models.FlatOwner.objects.all()
    form = forms.FlatOwnerForm


class FlatOwnerDeleteView(generic.ObjectDeleteView):
    queryset = models.FlatOwner.objects.all()


class FlatOwnerBulkDeleteView(generic.BulkDeleteView):
    queryset = models.FlatOwner.objects.all()
    table = tables.FlatOwnerTable


# ---------------------------------------------------------------------------
#  PropertyTenant views
# ---------------------------------------------------------------------------


class PropertyTenantListView(generic.ObjectListView):
    queryset = models.PropertyTenant.objects.select_related("flat__building", "person")
    table = tables.PropertyTenantTable
    filterset = filtersets.PropertyTenantFilterSet
    filterset_form = filterforms.PropertyTenantFilterForm


class PropertyTenantView(generic.ObjectView):
    queryset = models.PropertyTenant.objects.select_related("flat__building", "person")
    layout = layout.SimpleLayout(
        left_panels=[
            PropertyTenantPanel(),
            PropertyTenantNotesPanel(),
            CustomFieldsPanel(),
            TagsPanel(),
        ],
        right_panels=[],
    )


class PropertyTenantEditView(generic.ObjectEditView):
    queryset = models.PropertyTenant.objects.all()
    form = forms.PropertyTenantForm


class PropertyTenantDeleteView(generic.ObjectDeleteView):
    queryset = models.PropertyTenant.objects.all()


class PropertyTenantBulkDeleteView(generic.BulkDeleteView):
    queryset = models.PropertyTenant.objects.all()
    table = tables.PropertyTenantTable
