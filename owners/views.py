"""
Solomon — Owner views (Owner + FlatOwner CRUD).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import RoleFilteredQuerysetMixin

from .forms import FlatOwnerForm, OwnerForm
from .models import FlatOwner, Owner


# =============================================================================
# Owner views
# =============================================================================


class OwnerListView(RoleFilteredQuerysetMixin, LoginRequiredMixin, ListView):
    model = Owner
    template_name = "owners/owner_list.html"
    context_object_name = "owners"
    paginate_by = 25

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(pk=owner.pk)


class OwnerDetailView(RoleFilteredQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Owner
    template_name = "owners/owner_detail.html"
    context_object_name = "owner"

    def owner_queryset_filter(self, qs, owner):
        return qs.filter(pk=owner.pk)


class OwnerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Owner
    form_class = OwnerForm
    template_name = "owners/owner_form.html"
    permission_required = "owners.add_owner"
    success_url = reverse_lazy("owners:owner-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Owner created successfully."))
        return response


class OwnerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Owner
    form_class = OwnerForm
    template_name = "owners/owner_form.html"
    permission_required = "owners.change_owner"

    def get_success_url(self):
        return reverse_lazy("owners:owner-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Owner updated successfully."))
        return response


class OwnerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Owner
    template_name = "owners/owner_confirm_delete.html"
    context_object_name = "owner"
    permission_required = "owners.delete_owner"
    success_url = reverse_lazy("owners:owner-list")

    def form_valid(self, form):
        messages.success(self.request, _("Owner deleted successfully."))
        return super().form_valid(form)


# =============================================================================
# FlatOwner views (ownership assignments)
# =============================================================================


class FlatOwnerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FlatOwner
    form_class = FlatOwnerForm
    template_name = "owners/flatowner_form.html"
    permission_required = "owners.add_flatowner"

    def get_initial(self):
        initial = super().get_initial()
        flat_pk = self.request.GET.get("flat")
        owner_pk = self.request.GET.get("owner")
        if flat_pk:
            initial["flat"] = flat_pk
        if owner_pk:
            initial["owner"] = owner_pk
        return initial

    def get_success_url(self):
        """Redirect back to the flat or owner detail based on context."""
        if self.object.flat_id:
            return reverse_lazy("flats:flat-detail", kwargs={"pk": self.object.flat_id})
        return reverse_lazy("owners:owner-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Ownership assigned successfully."))
        if hasattr(form, "_share_warning") and form._share_warning:
            messages.warning(self.request, form._share_warning)
        return response


class FlatOwnerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FlatOwner
    form_class = FlatOwnerForm
    template_name = "owners/flatowner_form.html"
    permission_required = "owners.change_flatowner"

    def get_success_url(self):
        return reverse_lazy("flats:flat-detail", kwargs={"pk": self.object.flat_id})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Ownership updated successfully."))
        if hasattr(form, "_share_warning") and form._share_warning:
            messages.warning(self.request, form._share_warning)
        return response


class FlatOwnerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = FlatOwner
    template_name = "owners/flatowner_confirm_delete.html"
    context_object_name = "flatowner"
    permission_required = "owners.delete_flatowner"

    def get_success_url(self):
        return reverse_lazy("flats:flat-detail", kwargs={"pk": self.object.flat_id})

    def form_valid(self, form):
        messages.success(self.request, _("Ownership removed successfully."))
        return super().form_valid(form)
