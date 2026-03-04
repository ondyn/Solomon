"""
Solomon — Flat views.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import RoleFilteredQuerysetMixin

from .forms import FlatForm
from .models import Flat


class FlatListView(RoleFilteredQuerysetMixin, LoginRequiredMixin, ListView):
    model = Flat
    template_name = "flats/flat_list.html"
    context_object_name = "flats"
    paginate_by = 25

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(flat_owners__owner=owner).distinct()


class FlatDetailView(RoleFilteredQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Flat
    template_name = "flats/flat_detail.html"
    context_object_name = "flat"

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(flat_owners__owner=owner).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        flat_owners = self.object.flat_owners.all()
        total_pct = sum(fo.share_percentage for fo in flat_owners)
        ctx["ownership_total_pct"] = round(total_pct, 2)
        return ctx


class FlatCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Flat
    form_class = FlatForm
    template_name = "flats/flat_form.html"
    permission_required = "flats.add_flat"
    success_url = reverse_lazy("flats:flat-list")

    def get_initial(self):
        initial = super().get_initial()
        building = self.request.GET.get("building")
        if building:
            initial["building"] = building
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Flat created successfully."))
        return response


class FlatUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Flat
    form_class = FlatForm
    template_name = "flats/flat_form.html"
    permission_required = "flats.change_flat"

    def get_success_url(self):
        return reverse_lazy("flats:flat-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Flat updated successfully."))
        return response


class FlatDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Flat
    template_name = "flats/flat_confirm_delete.html"
    context_object_name = "flat"
    permission_required = "flats.delete_flat"
    success_url = reverse_lazy("flats:flat-list")

    def form_valid(self, form):
        messages.success(self.request, _("Flat deleted successfully."))
        return super().form_valid(form)
