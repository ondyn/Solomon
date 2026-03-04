"""
Management command to set up default role-based groups and permissions.

Creates four groups matching the Role-Permission Matrix from DESIGN.md:
  - admin: full CRUD on all models, manage users
  - chairman: full CRUD + contract approval
  - board_member: full CRUD + approve expenses/repairs
  - owner: read-only on own data (view permissions only)

Usage::

    python manage.py setup_groups
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from core.permissions import Roles


class Command(BaseCommand):
    help = "Create default role-based groups with proper permissions."

    # Apps whose model permissions we distribute to groups
    MANAGED_APPS = ["buildings", "flats", "owners", "tenants"]

    def handle(self, *args, **options):
        self._create_groups()
        self.stdout.write(self.style.SUCCESS("Groups and permissions set up successfully."))

    def _get_app_permissions(self, codename_prefixes: list[str]) -> list[Permission]:
        """Return Permission objects for managed apps filtered by codename prefix."""
        cts = ContentType.objects.filter(app_label__in=self.MANAGED_APPS)
        perms = Permission.objects.filter(content_type__in=cts)
        if codename_prefixes:
            from django.db.models import Q

            q = Q()
            for prefix in codename_prefixes:
                q |= Q(codename__startswith=prefix)
            perms = perms.filter(q)
        return list(perms)

    def _create_groups(self):
        # All CRUD permissions for managed apps
        all_perms = self._get_app_permissions([])
        view_perms = self._get_app_permissions(["view_"])

        # Also include auth-related permissions for user management
        auth_ct = ContentType.objects.get(app_label="auth", model="user")
        user_perms = list(Permission.objects.filter(content_type=auth_ct))

        # Admin: everything including user management
        admin_group, _ = Group.objects.get_or_create(name=Roles.ADMIN)
        admin_group.permissions.set(all_perms + user_perms)
        self.stdout.write(f"  ✓ {Roles.ADMIN}: {admin_group.permissions.count()} permissions")

        # Chairman: full CRUD on all models + user management
        chairman_group, _ = Group.objects.get_or_create(name=Roles.CHAIRMAN)
        chairman_group.permissions.set(all_perms + user_perms)
        self.stdout.write(f"  ✓ {Roles.CHAIRMAN}: {chairman_group.permissions.count()} permissions")

        # Board member: full CRUD on all models (no user management)
        board_group, _ = Group.objects.get_or_create(name=Roles.BOARD_MEMBER)
        board_group.permissions.set(all_perms)
        self.stdout.write(f"  ✓ {Roles.BOARD_MEMBER}: {board_group.permissions.count()} permissions")

        # Owner: view-only permissions
        owner_group, _ = Group.objects.get_or_create(name=Roles.OWNER)
        owner_group.permissions.set(view_perms)
        self.stdout.write(f"  ✓ {Roles.OWNER}: {owner_group.permissions.count()} permissions")
