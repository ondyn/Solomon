"""
Solomon — Authorization constants and permission helpers.
"""

from django.utils.translation import gettext_lazy as _


class Roles:
    """User role constants matching Django groups."""

    ADMIN = "admin"
    CHAIRMAN = "chairman"
    BOARD_MEMBER = "board_member"
    OWNER = "owner"

    CHOICES = [
        (ADMIN, _("Administrator")),
        (CHAIRMAN, _("Chairman")),
        (BOARD_MEMBER, _("Board member")),
        (OWNER, _("Owner")),
    ]

    # Roles with full CRUD access
    MANAGEMENT_ROLES = {ADMIN, CHAIRMAN, BOARD_MEMBER}
