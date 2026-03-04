"""
Solomon — Owner admin configuration.
"""

from django.contrib import admin

from .models import FlatOwner, Owner


class FlatOwnerInline(admin.TabularInline):
    model = FlatOwner
    extra = 0
    readonly_fields = ("id", "created_at")


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "email", "phone", "user")
    search_fields = ("last_name", "first_name", "email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [FlatOwnerInline]


@admin.register(FlatOwner)
class FlatOwnerAdmin(admin.ModelAdmin):
    list_display = ("flat", "owner", "share_numerator", "share_denominator", "effective_from", "effective_to")
    list_filter = ("effective_from",)
    search_fields = ("flat__flat_number", "owner__last_name")
    readonly_fields = ("id", "created_at", "updated_at")
