"""
Solomon — Building URL configuration.
"""

from django.urls import path

from . import views

app_name = "buildings"

urlpatterns = [
    path("", views.BuildingListView.as_view(), name="building-list"),
    path("new/", views.BuildingCreateView.as_view(), name="building-create"),
    path("<uuid:pk>/", views.BuildingDetailView.as_view(), name="building-detail"),
    path("<uuid:pk>/edit/", views.BuildingUpdateView.as_view(), name="building-update"),
    path("<uuid:pk>/delete/", views.BuildingDeleteView.as_view(), name="building-delete"),
]
