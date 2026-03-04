"""
Solomon — Tenant URL configuration.
"""

from django.urls import path

from . import views

app_name = "tenants"

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant-list"),
    path("new/", views.TenantCreateView.as_view(), name="tenant-create"),
    path("<uuid:pk>/", views.TenantDetailView.as_view(), name="tenant-detail"),
    path("<uuid:pk>/edit/", views.TenantUpdateView.as_view(), name="tenant-update"),
    path("<uuid:pk>/delete/", views.TenantDeleteView.as_view(), name="tenant-delete"),
]
