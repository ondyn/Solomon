"""
Solomon — Audit trail browsing views.

Provides views to browse the django-auditlog entries:
  - Global log (all changes)
  - Per-entity log (filtered by content type + object ID)
"""

from auditlog.models import LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, TemplateView

from buildings.models import Building
from core.permissions import Roles
from flats.models import Flat
from owners.models import Owner
from tenants.models import Tenant


class HomeView(TemplateView):
    """Main dashboard page."""

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            # Provide filtered counts depending on the user role
            buildings_qs = Building.objects.all()
            flats_qs = Flat.objects.all()
            owners_qs = Owner.objects.all()
            tenants_qs = Tenant.objects.all()

            if not user.is_superuser:
                user_groups = set(user.groups.values_list("name", flat=True))
                # If they don't have management roles, restrict to their own data
                if not (user_groups & Roles.MANAGEMENT_ROLES) and Roles.OWNER in user_groups:
                    owner = getattr(user, "owner_profile", None)
                    if owner:
                        flats_qs = flats_qs.filter(flat_owners__owner=owner).distinct()
                        buildings_qs = buildings_qs.filter(flats__in=flats_qs).distinct()
                        owners_qs = Owner.objects.filter(pk=owner.pk)
                        tenants_qs = tenants_qs.filter(flat__in=flats_qs).distinct()
                    else:
                        flats_qs = flats_qs.none()
                        buildings_qs = buildings_qs.none()
                        owners_qs = owners_qs.none()
                        tenants_qs = tenants_qs.none()
                elif not (user_groups & Roles.MANAGEMENT_ROLES):
                    # No recognizable role, show zero
                    flats_qs = flats_qs.none()
                    buildings_qs = buildings_qs.none()
                    owners_qs = owners_qs.none()
                    tenants_qs = tenants_qs.none()

            ctx["buildings_count"] = buildings_qs.count()
            ctx["flats_count"] = flats_qs.count()
            ctx["owners_count"] = owners_qs.count()
            ctx["tenants_count"] = tenants_qs.count()
        return ctx


class AuditLogListView(LoginRequiredMixin, ListView):
    """Global audit log — chronological list of all changes."""

    model = LogEntry
    template_name = "core/auditlog_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        qs = LogEntry.objects.select_related("content_type", "actor").order_by("-timestamp")
        # Filtering
        actor = self.request.GET.get("actor")
        action = self.request.GET.get("action")
        content_type = self.request.GET.get("content_type")
        object_id = self.request.GET.get("object_id")
        if actor:
            qs = qs.filter(actor__username__icontains=actor)
        if action:
            qs = qs.filter(action=action)
        if content_type:
            qs = qs.filter(content_type_id=content_type)
        if object_id:
            qs = qs.filter(object_id=object_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action_choices"] = LogEntry.Action.choices
        return ctx


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """Detail of a single audit log entry showing full field-level diff."""

    model = LogEntry
    template_name = "core/auditlog_detail.html"
    context_object_name = "entry"
