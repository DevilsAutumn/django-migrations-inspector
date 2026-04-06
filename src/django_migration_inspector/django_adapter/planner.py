"""Build normalized forward migration plans from Django internals."""

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
    ForwardMigrationPlan,
    PlannedMigrationStep,
)
from django_migration_inspector.exceptions import MigrationInspectionError


def _resolve_module_path(module_name: str) -> Path | None:
    module = sys.modules.get(module_name)
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        return None
    return Path(module_file).resolve()


def _key_sort_key(migration_key: MigrationNodeKey) -> tuple[str, str]:
    return (migration_key.app_label, migration_key.migration_name)


@dataclass(slots=True)
class DjangoForwardPlanProvider:
    """Build a normalized forward migration plan using Django's executor."""

    def build_plan(
        self,
        *,
        database_alias: str,
        app_label: str | None = None,
    ) -> ForwardMigrationPlan:
        """Build the current forward migration plan for the requested scope."""

        validate_supported_django_version()
        connection = get_database_connection(database_alias)
        executor = MigrationExecutor(connection=connection)

        raw_targets = tuple(sorted(executor.loader.graph.leaf_nodes()))
        if app_label is None:
            selected_targets = raw_targets
        else:
            selected_targets = tuple(target for target in raw_targets if target[0] == app_label)

        if app_label is not None and not selected_targets:
            raise MigrationInspectionError(
                f"App {app_label!r} has no migrations in the loaded Django project."
            )

        migration_plan = executor.migration_plan(selected_targets)
        planned_steps = tuple(
            self._build_planned_step(migration=migration)
            for migration, backwards in migration_plan
            if not backwards
        )
        target_leaf_nodes = tuple(
            sorted(
                (MigrationNodeKey.from_tuple(target) for target in selected_targets),
                key=_key_sort_key,
            )
        )
        return ForwardMigrationPlan(
            database_alias=database_alias,
            selected_app_label=app_label,
            target_leaf_nodes=target_leaf_nodes,
            steps=planned_steps,
        )

    def _build_planned_step(self, *, migration: Migration) -> PlannedMigrationStep:
        migration_key = MigrationNodeKey(
            app_label=str(migration.app_label),
            migration_name=str(migration.name),
        )
        operations = tuple(
            build_operation_descriptor(operation=operation, index=index)
            for index, operation in enumerate(migration.operations)
        )
        module_name = str(migration.__module__)
        return PlannedMigrationStep(
            key=migration_key,
            module=module_name,
            file_path=_resolve_module_path(module_name),
            operations=operations,
        )
