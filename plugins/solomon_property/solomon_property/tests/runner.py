"""
Solomon test runner - works around NetBox v4.3+ test setup issue.

NetBox v4.3 added users.Owner (migration 0015_owner) and FK references to
users_owner in unmigrated apps (circuits, dcim, etc.). Django's test runner
calls `migrate --run-syncdb`, which syncs unmigrated apps BEFORE running
migrations. This causes deferred FK constraints to reference non-existent
tables like `users_owner`.

FIX: Patch the PostgreSQL schema editor's `__exit__` to execute each deferred
SQL statement individually inside its own savepoint. If a deferred FK fails
because the referenced table doesn't exist yet, we roll back just that
savepoint and skip it. The FK will be properly enforced once the full
migration run creates those tables.
"""

from django.test.runner import DiscoverRunner


class SolomonTestRunner(DiscoverRunner):
    """Tolerate deferred FK constraints against not-yet-migrated tables."""

    def setup_databases(self, **kwargs):
        from django.db.backends.base.schema import BaseDatabaseSchemaEditor

        original_exit = BaseDatabaseSchemaEditor.__exit__

        def tolerant_exit(self_editor, exc_type, exc_value, traceback):
            if exc_type is None:
                for sql in self_editor.deferred_sql:
                    sql_str = sql.sql if hasattr(sql, "sql") else str(sql)
                    if "DEFERRABLE INITIALLY DEFERRED" in sql_str:
                        # Execute inside a savepoint so a failure is recoverable
                        try:
                            with self_editor.connection.cursor() as cursor:
                                cursor.execute("SAVEPOINT solomon_fk_sp")
                            self_editor.execute(sql, None)
                            with self_editor.connection.cursor() as cursor:
                                cursor.execute("RELEASE SAVEPOINT solomon_fk_sp")
                        except Exception as exc:
                            msg = str(exc)
                            if "does not exist" in msg or "undefined" in msg.lower():
                                # Referenced table not yet created - skip.
                                # The FK will be re-added when that app migrates.
                                with self_editor.connection.cursor() as cursor:
                                    cursor.execute(
                                        "ROLLBACK TO SAVEPOINT solomon_fk_sp"
                                    )
                            else:
                                raise
                    else:
                        self_editor.execute(sql, None)
            if self_editor.atomic_migration:
                self_editor.atomic.__exit__(exc_type, exc_value, traceback)

        BaseDatabaseSchemaEditor.__exit__ = tolerant_exit
        try:
            result = super().setup_databases(**kwargs)
        finally:
            BaseDatabaseSchemaEditor.__exit__ = original_exit
        return result
