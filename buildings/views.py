"""
Solomon — Building views.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import RoleFilteredQuerysetMixin

from .forms import BuildingForm
from .models import Building


class BuildingListView(RoleFilteredQuerysetMixin, LoginRequiredMixin, ListView):
    model = Building
    template_name = "buildings/building_list.html"
    context_object_name = "buildings"
    paginate_by = 25

    def owner_queryset_filter(self, qs, owner):
        # Owners see only buildings that contain flats they own
        return qs.filter(flats__flat_owners__owner=owner).distinct()


class BuildingDetailView(RoleFilteredQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Building
    template_name = "buildings/building_detail.html"
    context_object_name = "building"

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(flats__flat_owners__owner=owner).distinct()


class BuildingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Building
    form_class = BuildingForm
    template_name = "buildings/building_form.html"
    permission_required = "buildings.add_building"
    success_url = reverse_lazy("buildings:building-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Building created successfully."))
        return response


class BuildingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Building
    form_class = BuildingForm
    template_name = "buildings/building_form.html"
    permission_required = "buildings.change_building"

    def get_success_url(self):
        return reverse_lazy("buildings:building-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Building updated successfully."))
        return response


class BuildingDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Building
    template_name = "buildings/building_confirm_delete.html"
    context_object_name = "building"
    permission_required = "buildings.delete_building"
    success_url = reverse_lazy("buildings:building-list")

    def form_valid(self, form):
        messages.success(self.request, _("Building deleted successfully."))
        return super().form_valid(form)
