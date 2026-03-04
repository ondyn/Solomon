"""
Solomon — User management URLs.
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.UserListView.as_view(), name="user-list"),
    path("new/", views.UserCreateView.as_view(), name="user-create"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("<int:pk>/edit/", views.UserUpdateView.as_view(), name="user-update"),
]
