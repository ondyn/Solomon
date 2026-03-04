"""
Solomon — Tenant admin configuration.
"""

from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "flat", "effective_from", "effective_to")
    list_filter = ("effective_from",)
    search_fields = ("last_name", "first_name", "flat__flat_number")
    readonly_fields = ("id", "created_at", "updated_at")
