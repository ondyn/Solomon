"""
Solomon — Flat admin configuration.
"""

from django.contrib import admin

from .models import Flat


@admin.register(Flat)
class FlatAdmin(admin.ModelAdmin):
    list_display = ("flat_number", "building", "floor", "disposition", "area_m2")
    list_filter = ("building", "floor")
    search_fields = ("flat_number", "building__name")
    readonly_fields = ("id", "created_at", "updated_at")
