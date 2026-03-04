"""
Solomon — User management views.

Only admin and chairman roles can manage users (DESIGN.md section 7.2).
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import UserCreateForm, UserForm

User = get_user_model()


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 25
    permission_required = "auth.view_user"

    def get_queryset(self):
        return User.objects.prefetch_related("groups").order_by("username")


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "user_obj"
    permission_required = "auth.view_user"


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    permission_required = "auth.add_user"
    success_url = reverse_lazy("accounts:user-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("User created successfully."))
        return response


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "accounts/user_form.html"
    context_object_name = "user_obj"
    permission_required = "auth.change_user"

    def get_success_url(self):
        return reverse_lazy("accounts:user-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("User updated successfully."))
        return response
