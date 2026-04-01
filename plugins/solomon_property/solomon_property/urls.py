"""Solomon Property - URL patterns."""

from django.urls import path

from netbox.views.generic import ObjectChangeLogView

from . import models, views
from .contacts_views import ContactsExportView, ContactsImportView
from .cuzk_views import (
    CUZKAddressSearchView,
    CUZKCityPartAutocompleteView,
    CUZKImportPreviewView,
    CUZKImportSearchView,
    FlatAreaCalculationView,
    OwnersImportView,
)

urlpatterns = [
    # ── Buildings ──────────────────────────────────────────────────────────
    path("buildings/", views.BuildingListView.as_view(), name="building_list"),
    path("buildings/add/", views.BuildingEditView.as_view(), name="building_add"),
    path("buildings/delete/", views.BuildingBulkDeleteView.as_view(), name="building_bulk_delete"),
    path("buildings/<int:pk>/", views.BuildingView.as_view(), name="building"),
    path("buildings/<int:pk>/edit/", views.BuildingEditView.as_view(), name="building_edit"),
    path("buildings/<int:pk>/delete/", views.BuildingDeleteView.as_view(), name="building_delete"),
    path(
        "buildings/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="building_changelog",
        kwargs={"model": models.Building},
    ),

    # ── Flats ─────────────────────────────────────────────────────────────
    path("flats/", views.FlatListView.as_view(), name="flat_list"),
    path("flats/add/", views.FlatEditView.as_view(), name="flat_add"),
    path("flats/delete/", views.FlatBulkDeleteView.as_view(), name="flat_bulk_delete"),
    path("flats/<int:pk>/", views.FlatView.as_view(), name="flat"),
    path("flats/<int:pk>/edit/", views.FlatEditView.as_view(), name="flat_edit"),
    path("flats/<int:pk>/delete/", views.FlatDeleteView.as_view(), name="flat_delete"),
    path(
        "flats/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="flat_changelog",
        kwargs={"model": models.Flat},
    ),

    # ── Persons ───────────────────────────────────────────────────────────
    path("persons/", views.PersonListView.as_view(), name="person_list"),
    path("persons/add/", views.PersonEditView.as_view(), name="person_add"),
    path("persons/delete/", views.PersonBulkDeleteView.as_view(), name="person_bulk_delete"),
    path("persons/<int:pk>/", views.PersonView.as_view(), name="person"),
    path("persons/<int:pk>/edit/", views.PersonEditView.as_view(), name="person_edit"),
    path("persons/<int:pk>/delete/", views.PersonDeleteView.as_view(), name="person_delete"),
    path(
        "persons/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="person_changelog",
        kwargs={"model": models.Person},
    ),

    # ── PropertyOwners ────────────────────────────────────────────────────────
    path("owners/", views.PropertyOwnerListView.as_view(), name="propertyowner_list"),
    path("owners/add/", views.PropertyOwnerEditView.as_view(), name="propertyowner_add"),
    path("owners/delete/", views.PropertyOwnerBulkDeleteView.as_view(), name="propertyowner_bulk_delete"),
    path("owners/<int:pk>/", views.PropertyOwnerView.as_view(), name="propertyowner"),
    path("owners/<int:pk>/edit/", views.PropertyOwnerEditView.as_view(), name="propertyowner_edit"),
    path("owners/<int:pk>/delete/", views.PropertyOwnerDeleteView.as_view(), name="propertyowner_delete"),
    path(
        "owners/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="propertyowner_changelog",
        kwargs={"model": models.PropertyOwner},
    ),

    # ── FlatOwners ────────────────────────────────────────────────────────
    path("flat-owners/", views.FlatOwnerListView.as_view(), name="flatowner_list"),
    path("flat-owners/add/", views.FlatOwnerEditView.as_view(), name="flatowner_add"),
    path("flat-owners/delete/", views.FlatOwnerBulkDeleteView.as_view(), name="flatowner_bulk_delete"),
    path("flat-owners/<int:pk>/", views.FlatOwnerView.as_view(), name="flatowner"),
    path("flat-owners/<int:pk>/edit/", views.FlatOwnerEditView.as_view(), name="flatowner_edit"),
    path("flat-owners/<int:pk>/delete/", views.FlatOwnerDeleteView.as_view(), name="flatowner_delete"),
    path(
        "flat-owners/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="flatowner_changelog",
        kwargs={"model": models.FlatOwner},
    ),

    # ── PropertyTenants ───────────────────────────────────────────────────────
    path("tenants/", views.PropertyTenantListView.as_view(), name="propertytenant_list"),
    path("tenants/add/", views.PropertyTenantEditView.as_view(), name="propertytenant_add"),
    path("tenants/delete/", views.PropertyTenantBulkDeleteView.as_view(), name="propertytenant_bulk_delete"),
    path("tenants/<int:pk>/", views.PropertyTenantView.as_view(), name="propertytenant"),
    path("tenants/<int:pk>/edit/", views.PropertyTenantEditView.as_view(), name="propertytenant_edit"),
    path("tenants/<int:pk>/delete/", views.PropertyTenantDeleteView.as_view(), name="propertytenant_delete"),
    path(
        "tenants/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="propertytenant_changelog",
        kwargs={"model": models.PropertyTenant},
    ),

    # ── CUZK Import ───────────────────────────────────────────────────────
    path("cuzk/import/", CUZKImportSearchView.as_view(), name="cuzk-import-search"),
    path("cuzk/import/preview/", CUZKImportPreviewView.as_view(), name="cuzk-import-preview"),
    path("cuzk/import/address-search/", CUZKAddressSearchView.as_view(), name="cuzk-address-search"),
    path("cuzk/autocomplete/city-parts/", CUZKCityPartAutocompleteView.as_view(), name="cuzk-citypart-autocomplete"),

    # ── Owners.txt Import ─────────────────────────────────────────────────
    path("owners/import/", OwnersImportView.as_view(), name="owners-import"),

    # ── Contacts Import/Export ────────────────────────────────────────
    path("contacts/import/", ContactsImportView.as_view(), name="contacts-import"),
    path("contacts/export/", ContactsExportView.as_view(), name="contacts-export"),

    # ── Flat Area Calculation ─────────────────────────────────────────
    path("flats/calculate-area/", FlatAreaCalculationView.as_view(), name="flat-area-calculation"),
]
