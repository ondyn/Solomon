"""
Solomon — Core app URLs (audit trail).
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("auditlog/", views.AuditLogListView.as_view(), name="auditlog-list"),
    path("auditlog/<int:pk>/", views.AuditLogDetailView.as_view(), name="auditlog-detail"),
]
