"""
Solomon — Flat URL configuration.
"""

from django.urls import path

from . import views

app_name = "flats"

urlpatterns = [
    path("", views.FlatListView.as_view(), name="flat-list"),
    path("new/", views.FlatCreateView.as_view(), name="flat-create"),
    path("<uuid:pk>/", views.FlatDetailView.as_view(), name="flat-detail"),
    path("<uuid:pk>/edit/", views.FlatUpdateView.as_view(), name="flat-update"),
    path("<uuid:pk>/delete/", views.FlatDeleteView.as_view(), name="flat-delete"),
]
