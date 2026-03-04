"""
Solomon — Building admin configuration.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Building


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "street", "house_number", "city", "postal_code", "created_at")
    list_filter = ("city",)
    search_fields = ("name", "street", "house_number")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "street", "house_number", "city", "postal_code")}),
        (_("Notes"), {"fields": ("note",), "classes": ("collapse",)}),
        (_("Metadata"), {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
