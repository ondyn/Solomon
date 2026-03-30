"""
Solomon — Core app URLs (audit trail, CUZK import).
"""

from django.urls import path

from . import views
from .cuzk_import import (
    CUZKBuildingSearchView,
    CUZKCityPartSearchView,
    CUZKImportPreviewView,
    CUZKImportSearchView,
)

app_name = "core"

urlpatterns = [
    path("auditlog/", views.AuditLogListView.as_view(), name="auditlog-list"),
    path("auditlog/<int:pk>/", views.AuditLogDetailView.as_view(), name="auditlog-detail"),
    path("cuzk-import/", CUZKImportSearchView.as_view(), name="cuzk-import-search"),
    path("cuzk-import/preview/", CUZKImportPreviewView.as_view(), name="cuzk-import-preview"),
    path("cuzk-import/search-building/", CUZKBuildingSearchView.as_view(), name="cuzk-building-search"),
    path("cuzk-import/search-city-parts/", CUZKCityPartSearchView.as_view(), name="cuzk-city-part-search"),
]
