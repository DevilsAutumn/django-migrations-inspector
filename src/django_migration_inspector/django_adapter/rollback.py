"""Build normalized rollback plans from Django internals."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.migration import Migration

from django_migration_inspector.django_adapter.compat import validate_supported_django_version
from django_migration_inspector.django_adapter.loader import get_database_connection
from django_migration_inspector.django_adapter.operations import build_operation_descriptor
from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.plans import (
    RollbackMigrationPlan,
    RollbackMigrationStep,
)
from django_migration_inspector.exceptions import MigrationInspectionError


def _resolve_module_path(module_name: str) -> Path | None:
    module = sys.modules.get(module_name)
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        return None
    return Path(module_file).resolve()


def _migration_exists(executor: MigrationExecutor, *, app_label: str, migration_name: str) -> bool:
    return (app_label, migration_name) in executor.loader.disk_migrations


@dataclass(slots=True)
class DjangoRollbackPlanProvider:
    """Build a normalized rollback plan using Django's executor."""

    def build_plan(
        self,
        *,
        database_alias: str,
        target_app_label: str,
        target_migration_name: str,
    ) -> RollbackMigrationPlan:
        """Build the rollback plan for the requested target migration."""

        validate_supported_django_version()
        connection = get_database_connection(database_alias)
        executor = MigrationExecutor(connection=connection)

        if target_migration_name.lower() == "zero":
            target_name_or_none: str | None = None
        else:
            target_name_or_none = target_migration_name
            if not _migration_exists(
                executor,
                app_label=target_app_label,
                migration_name=target_name_or_none,
            ):
                raise MigrationInspectionError(
                    f"Migration {target_app_label!r}.{target_migration_name!r} was not found."
                )

        if target_name_or_none is None and not any(
            migration_key[0] == target_app_label
            for migration_key in executor.loader.disk_migrations
        ):
            raise MigrationInspectionError(
                f"App {target_app_label!r} has no migrations in the loaded Django project."
            )

        migration_plan = executor.migration_plan([(target_app_label, target_name_or_none)])
        forward_steps = [migration for migration, backwards in migration_plan if not backwards]
        if forward_steps:
            raise MigrationInspectionError(
                "Requested rollback target is ahead of the current database state or would "
                "require forward migrations. Rollback simulation only supports pure reverse plans."
            )

        steps = tuple(
            self._build_rollback_step(migration=migration)
            for migration, backwards in migration_plan
            if backwards
        )
        return RollbackMigrationPlan(
            database_alias=database_alias,
            target_app_label=target_app_label,
            target_migration_name=target_name_or_none,
            steps=steps,
        )

    def _build_rollback_step(self, *, migration: Migration) -> RollbackMigrationStep:
        reverse_operations = tuple(
            build_operation_descriptor(operation=operation, index=index)
            for index, operation in reversed(tuple(enumerate(migration.operations)))
        )
        module_name = str(migration.__module__)
        return RollbackMigrationStep(
            key=MigrationNodeKey(
                app_label=str(migration.app_label), migration_name=str(migration.name)
            ),
            module=module_name,
            file_path=_resolve_module_path(module_name),
            is_merge=len(migration.dependencies) > 1,
            reverse_operations=reverse_operations,
        )
