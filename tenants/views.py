"""
Solomon — Tenant views.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import RoleFilteredQuerysetMixin

from .forms import TenantForm
from .models import Tenant


class TenantListView(RoleFilteredQuerysetMixin, LoginRequiredMixin, ListView):
    model = Tenant
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"
    paginate_by = 25

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(flat__flat_owners__owner=owner).distinct()


class TenantDetailView(RoleFilteredQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Tenant
    template_name = "tenants/tenant_detail.html"
    context_object_name = "tenant"

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(flat__flat_owners__owner=owner).distinct()


class TenantCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = "tenants/tenant_form.html"
    permission_required = "tenants.add_tenant"
    success_url = reverse_lazy("tenants:tenant-list")

    def get_initial(self):
        initial = super().get_initial()
        flat_pk = self.request.GET.get("flat")
        if flat_pk:
            initial["flat"] = flat_pk
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Tenant created successfully."))
        return response


class TenantUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = "tenants/tenant_form.html"
    permission_required = "tenants.change_tenant"

    def get_success_url(self):
        return reverse_lazy("tenants:tenant-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Tenant updated successfully."))
        return response


class TenantDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tenant
    template_name = "tenants/tenant_confirm_delete.html"
    context_object_name = "tenant"
    permission_required = "tenants.delete_tenant"
    success_url = reverse_lazy("tenants:tenant-list")

    def form_valid(self, form):
        messages.success(self.request, _("Tenant deleted successfully."))
        return super().form_valid(form)
