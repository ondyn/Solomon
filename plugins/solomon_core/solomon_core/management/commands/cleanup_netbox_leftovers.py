from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


def _get_model_or_none(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


class Command(BaseCommand):
    help = "Remove stale NetBox content types and related records left behind after upgrades"

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually delete stale records. Without this flag the command runs as dry-run.",
        )

    def _stale_content_types(self):
        installed_app_labels = {config.label for config in apps.get_app_configs()}
        queryset = ContentType.objects.exclude(app_label__in=installed_app_labels)
        # Never touch Solomon app labels by convention.
        queryset = queryset.exclude(app_label__startswith="solomon")
        return queryset

    def _disabled_app_labels(self):
        plugin_cfg = settings.PLUGINS_CONFIG.get("solomon_core", {})

        labels = set()
        direct_map = {
            "enable_wireless": "wireless",
            "enable_ipam": "ipam",
            "enable_vpn": "vpn",
            "enable_virtualization": "virtualization",
            "enable_circuits": "circuits",
        }

        for setting_key, app_label in direct_map.items():
            if not plugin_cfg.get(setting_key, False):
                labels.add(app_label)

        dcim_keys = [
            "enable_organization",
            "enable_racks",
            "enable_devices",
            "enable_connections",
            "enable_power",
            "enable_provisioning",
        ]
        if all(not plugin_cfg.get(key, False) for key in dcim_keys):
            labels.add("dcim")

        return labels

    def handle(self, *args, **options):
        execute = options["execute"]
        stale_cts = self._stale_content_types()
        disabled_app_labels = self._disabled_app_labels()

        permission_qs = Permission.objects.filter(content_type__in=stale_cts)

        log_entry_model = _get_model_or_none("extras", "LogEntry")
        log_entries_qs = (
            log_entry_model.objects.filter(content_type__in=stale_cts)
            if log_entry_model is not None
            else None
        )

        object_change_model = _get_model_or_none("core", "ObjectChange")
        object_changes_qs = (
            object_change_model.objects.filter(changed_object_type__in=stale_cts)
            if object_change_model is not None
            else None
        )

        object_type_model = _get_model_or_none("core", "ObjectType")
        disabled_object_types_qs = (
            object_type_model.objects.filter(app_label__in=disabled_app_labels)
            .exclude(app_label__startswith="solomon")
            if object_type_model is not None
            else None
        )

        self.stdout.write(self.style.WARNING("Dry run") if not execute else self.style.SUCCESS("Execute mode"))
        self.stdout.write(f"Stale content types: {stale_cts.count()}")
        self.stdout.write(f"Stale permissions: {permission_qs.count()}")
        if log_entries_qs is not None:
            self.stdout.write(f"Stale log entries: {log_entries_qs.count()}")
        else:
            self.stdout.write("Stale log entries: model not available")
        if object_changes_qs is not None:
            self.stdout.write(f"Stale object changes: {object_changes_qs.count()}")
        else:
            self.stdout.write("Stale object changes: model not available")
        if disabled_object_types_qs is not None:
            self.stdout.write(f"Disabled module object types: {disabled_object_types_qs.count()}")
            if disabled_app_labels:
                self.stdout.write(
                    f"Disabled module app labels: {', '.join(sorted(disabled_app_labels))}"
                )
        else:
            self.stdout.write("Disabled module object types: model not available")

        if not execute:
            self.stdout.write("No changes applied. Re-run with --execute to delete.")
            return

        deleted_log_entries = 0
        deleted_object_changes = 0
        if log_entries_qs is not None:
            deleted_log_entries = log_entries_qs.delete()[0]
        if object_changes_qs is not None:
            deleted_object_changes = object_changes_qs.delete()[0]

        normalized_object_types = 0
        if disabled_object_types_qs is not None:
            # Keep content types intact, but remove custom field applicability and hide these object types.
            for object_type in disabled_object_types_qs:
                new_features = [feature for feature in object_type.features if feature != "custom_fields"]
                changed = False
                if new_features != object_type.features:
                    object_type.features = new_features
                    changed = True
                if object_type.public:
                    object_type.public = False
                    changed = True
                if changed:
                    object_type.save(update_fields=["features", "public"])
                    normalized_object_types += 1

        deleted_permissions = permission_qs.delete()[0]
        deleted_content_types = stale_cts.delete()[0]

        self.stdout.write(self.style.SUCCESS("Cleanup completed."))
        self.stdout.write(f"Deleted log entries: {deleted_log_entries}")
        self.stdout.write(f"Deleted object changes: {deleted_object_changes}")
        self.stdout.write(f"Normalized disabled object types: {normalized_object_types}")
        self.stdout.write(f"Deleted permissions: {deleted_permissions}")
        self.stdout.write(f"Deleted content types: {deleted_content_types}")
