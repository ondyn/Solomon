from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.SolomonTestView.as_view(), name="solomon_test_status"),
]
