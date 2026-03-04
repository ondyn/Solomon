"""
Solomon — View mixins for role-based data filtering.
"""

from django.contrib.auth.models import Group

from core.permissions import Roles


class RoleFilteredQuerysetMixin:
    """
    Mixin that filters queryset based on the user's role.

    For users in the 'owner' group, restricts data to only their own
    related records. Management roles see everything.

    Subclasses must define:
      - ``owner_queryset_filter(qs, owner)`` — returns filtered queryset
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Superusers and management roles see everything
        if user.is_superuser:
            return qs

        user_groups = set(user.groups.values_list("name", flat=True))
        if user_groups & Roles.MANAGEMENT_ROLES:
            return qs

        # Owner role: filter to own data
        if Roles.OWNER in user_groups:
            owner = getattr(user, "owner_profile", None)
            if owner and hasattr(self, "owner_queryset_filter"):
                return self.owner_queryset_filter(qs, owner)
            # No linked owner profile — show nothing
            return qs.none()

        # No recognized role — show nothing
        return qs.none()
