from importlib.metadata import metadata

from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginConfig

_meta = metadata("solomon-issues")


class SolomonIssuesConfig(PluginConfig):
    name = "solomon_issues"
    verbose_name = _("Solomon Issues")
    version = _meta["Version"]
    author = _meta["Author"]
    description = _meta["Summary"]
    base_url = "issues"
    min_version = "4.0.0"

    default_settings = {
        # Absolute base URL embedded in QR codes. Leave empty to derive it from
        # the incoming request, which keeps localhost and any deployment working.
        "public_base_url": "",
        # Master switch for anonymous (QR scan) reporting.
        "allow_anonymous_reports": True,
        # What an anonymous visitor may see on a tag page: none, open, or all.
        "public_issue_visibility": "open",
        # Languages offered by the switcher on public pages.
        "public_languages": ["en", "cs"],
        # Caption printed next to the QR code when a tag defines none.
        "default_label_caption": "",
        # Always-notified addresses, on top of category and tag recipients.
        "manager_emails": [],
        "notifications_enabled": True,
        # Hand notification delivery to the RQ worker instead of the web request.
        "async_notifications": True,
        # L, M, Q or H.
        "qr_error_correction": "M",
        # Anonymous reports accepted per client address per hour.
        "rate_limit_reports_per_hour": 10,
        "attachments_enabled": True,
        "max_attachment_size_mb": 10,
        "require_reporter_email": False,
    }

    def ready(self):
        super().ready()
        from . import signals  # noqa: F401


config = SolomonIssuesConfig
