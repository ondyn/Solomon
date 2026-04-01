####
## Solomon - Local Settings Override
##
## This file is imported at the END of NetBox's settings.py via:
##   from .local_settings import *
##
## It can set ANY Django setting, unlike the /etc/netbox/config/ files
## which only support NetBox-specific configuration parameters.
##
## WARNING: This is marked as "UNSUPPORTED FUNCTIONALITY" by NetBox.
## Use only for settings that cannot be set through official config.
####

## ─── Disable migrations for unused NetBox modules ─────────────────────────
## These apps remain in INSTALLED_APPS (runtime imports work) but their
## database tables will NOT be created.
##
## Two monkey-patches are needed:
##
## 1. MigrationLoader.check_key — Django raises NodeNotFoundError for
##    specific-version dependency refs like ('dcim', '0002_squashed') on
##    unmigrated apps. We make check_key() return None for those, so the
##    dependency is silently dropped.
##
## 2. AddField / AlterField / RemoveField operations — extras migrations
##    add ManyToManyFields to ConfigContext pointing at disabled-app models
##    (dcim.Site, virtualization.Cluster, tenancy.Tenant, etc.).  These
##    create FK-constrained through-tables that reference non-existent
##    target tables.  We wrap database_forwards/database_backwards to
##    silently skip any operation whose field targets a disabled app.

_DISABLED_MIGRATION_APPS = {
    "dcim",
    "circuits",
    "ipam",
    "wireless",
    "vpn",
    "virtualization",
    "tenancy",
}

MIGRATION_MODULES = {app: None for app in _DISABLED_MIGRATION_APPS}


# ── Patch 1: skip migration-graph dependencies on disabled apps ────────────
#    AND inject ordering fixes for cross-app model moves (SeparateDatabaseAndState)
from django.db.migrations.loader import MigrationLoader as _MigrationLoader

_original_check_key = _MigrationLoader.check_key

def _patched_check_key(self, key, current_app):
    if key[0] in self.unmigrated_apps:
        return None
    return _original_check_key(self, key, current_app)

_MigrationLoader.check_key = _patched_check_key

# Inject extra dependencies to fix ordering broken by removed disabled-app
# graph edges.  When all apps are present, Django infers the correct order
# through transitive dependencies.  Removing dcim/tenancy/etc. collapses
# those paths, so we add the critical edges explicitly.
#
# Format: (migration_that_must_run_AFTER, migration_that_must_run_BEFORE)
_EXTRA_DEPENDENCIES = [
    # extras.0117 renames extras_objectchange → core_objectchange (DB ops).
    # core.0017+ add columns to core_objectchange — must run AFTER rename.
    (('core', '0017_objectchange_message'), ('extras', '0117_move_objectchange')),
    # extras.0102 renames extras_configrevision → core_configrevision (DB ops).
    # Any core migration touching ConfigRevision after 0009 needs this.
]

_original_build_graph = _MigrationLoader.build_graph

def _patched_build_graph(self):
    _original_build_graph(self)
    for child, parent in _EXTRA_DEPENDENCIES:
        if child in self.graph.nodes and parent in self.graph.nodes:
            self.graph.add_dependency(str(child), child, parent, skip_validation=True)

_MigrationLoader.build_graph = _patched_build_graph


# ── Patch 2: skip field operations that target disabled-app models ─────────
from django.db.migrations import operations as _ops

def _field_targets_disabled_app(operation):
    """Return True if this field operation's field points to a disabled app."""
    field = getattr(operation, 'field', None)
    if field is None:
        return False

    # ManyToManyField, ForeignKey, OneToOneField all have remote_field
    remote = getattr(field, 'remote_field', None)
    if remote is None:
        return False

    # remote_field.model is either a class or a lazy string like 'dcim.Site'
    target = remote.model
    if isinstance(target, str):
        app_label = target.split('.')[0]
    elif hasattr(target, '_meta'):
        app_label = target._meta.app_label
    else:
        return False

    return app_label in _DISABLED_MIGRATION_APPS


def _make_noop_if_disabled(original_method):
    """Wrap database_forwards / database_backwards to skip disabled-app refs."""
    def wrapper(self, app_label, schema_editor, from_state, to_state):
        if _field_targets_disabled_app(self):
            return  # silently skip — target table does not exist
        return original_method(self, app_label, schema_editor, from_state, to_state)
    return wrapper


for _op_cls in (_ops.AddField, _ops.AlterField, _ops.RemoveField):
    _op_cls.database_forwards = _make_noop_if_disabled(_op_cls.database_forwards)
    _op_cls.database_backwards = _make_noop_if_disabled(_op_cls.database_backwards)
