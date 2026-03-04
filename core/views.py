"""
Solomon — Audit trail browsing views.

Provides views to browse the django-auditlog entries:
  - Global log (all changes)
  - Per-entity log (filtered by content type + object ID)
"""

from auditlog.models import LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView


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
