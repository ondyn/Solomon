"""
Solomon — Owner URL configuration.
"""

from django.urls import path

from . import views

app_name = "owners"

urlpatterns = [
    # Owner CRUD
    path("", views.OwnerListView.as_view(), name="owner-list"),
    path("new/", views.OwnerCreateView.as_view(), name="owner-create"),
    path("<uuid:pk>/", views.OwnerDetailView.as_view(), name="owner-detail"),
    path("<uuid:pk>/edit/", views.OwnerUpdateView.as_view(), name="owner-update"),
    path("<uuid:pk>/delete/", views.OwnerDeleteView.as_view(), name="owner-delete"),
    # FlatOwner CRUD (ownership assignments)
    path("ownership/new/", views.FlatOwnerCreateView.as_view(), name="flatowner-create"),
    path("ownership/<uuid:pk>/edit/", views.FlatOwnerUpdateView.as_view(), name="flatowner-update"),
    path("ownership/<uuid:pk>/delete/", views.FlatOwnerDeleteView.as_view(), name="flatowner-delete"),
]
