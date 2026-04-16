"""Build normalized migration analysis plans from Django internals."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.migration import Migration

from django_migration_inspector.django_adapter.app_ignore import build_ignored_app_labels
from django_migration_inspector.django_adapter.compat import validate_supported_django_version
from django_migration_inspector.django_adapter.loader import (
    get_database_connection,
    load_migration_loader,
)
from django_migration_inspector.django_adapter.operations import build_operation_descriptor
from django_migration_inspector.domain.enums import RiskAnalysisScope
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


def _raw_key_sort_key(migration_key: tuple[str, str]) -> tuple[str, str]:
    return (migration_key[0], migration_key[1])


def _build_target_leaf_nodes_from_loader(
    *, loader: MigrationLoader, app_label: str | None
) -> tuple[MigrationNodeKey, ...]:
    if app_label is None:
        selected_targets = tuple(sorted(loader.graph.leaf_nodes()))
    else:
        if not any(raw_key[0] == app_label for raw_key in loader.disk_migrations):
            raise MigrationInspectionError(
                f"App {app_label!r} has no migrations in the loaded Django project."
            )
        selected_targets = tuple(sorted(loader.graph.leaf_nodes(app_label)))

    return tuple(
        sorted(
            (MigrationNodeKey.from_tuple(target) for target in selected_targets),
            key=_key_sort_key,
        )
    )


def _generate_historical_plan_keys(
    *, graph: MigrationGraph, targets: tuple[MigrationNodeKey, ...]
) -> tuple[tuple[str, str], ...]:
    ordered_keys: list[tuple[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    visible_targets = tuple(
        sorted((target.to_tuple() for target in targets), key=_raw_key_sort_key)
    )
    for target in visible_targets:
        for migration_key in graph.forwards_plan(target):
            if migration_key in seen_keys:
                continue
            seen_keys.add(migration_key)
            ordered_keys.append(migration_key)
    return tuple(ordered_keys)


def _filter_target_leaf_nodes(
    *,
    target_leaf_nodes: tuple[MigrationNodeKey, ...],
    ignored_app_labels: frozenset[str],
) -> tuple[MigrationNodeKey, ...]:
    return tuple(
        target_leaf_node
        for target_leaf_node in target_leaf_nodes
        if target_leaf_node.app_label not in ignored_app_labels
    )


def _validate_selected_app_label(
    *,
    app_label: str | None,
    ignored_app_labels: frozenset[str],
) -> None:
    if app_label is None or app_label not in ignored_app_labels:
        return
    raise MigrationInspectionError(
        f"App {app_label!r} is ignored because it is not a user project app."
    )


@dataclass(slots=True)
class DjangoForwardPlanProvider:
    """Build a normalized forward migration plan using Django's executor."""

    def build_plan(
        self,
        *,
        database_alias: str,
        app_label: str | None = None,
        offline: bool = False,
    ) -> ForwardMigrationPlan:
        """Build the current forward migration plan for the requested scope."""

        if offline:
            raise MigrationInspectionError(
                "Pending risk analysis needs database state. Use `audit --offline` for a "
                "file-only migration review."
            )

        validate_supported_django_version()
        ignored_app_labels = build_ignored_app_labels()
        _validate_selected_app_label(
            app_label=app_label,
            ignored_app_labels=ignored_app_labels,
        )
        connection = get_database_connection(database_alias)
        executor = MigrationExecutor(connection=connection)
        target_leaf_nodes = _filter_target_leaf_nodes(
            target_leaf_nodes=_build_target_leaf_nodes_from_loader(
                loader=executor.loader,
                app_label=app_label,
            ),
            ignored_app_labels=ignored_app_labels,
        )
        migration_plan = executor.migration_plan(
            tuple(target.to_tuple() for target in target_leaf_nodes)
        )
        planned_steps = tuple(
            self._build_planned_step(migration=migration)
            for migration, backwards in migration_plan
            if not backwards and migration.app_label not in ignored_app_labels
        )
        return ForwardMigrationPlan(
            database_alias=database_alias,
            selected_app_label=app_label,
            scope=RiskAnalysisScope.PENDING,
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


@dataclass(slots=True)
class DjangoHistoricalPlanProvider:
    """Build a normalized migration-history plan using Django's graph."""

    def build_plan(
        self,
        *,
        database_alias: str,
        app_label: str | None = None,
        offline: bool = False,
    ) -> ForwardMigrationPlan:
        """Build the full migration-history plan for the requested scope."""

        validate_supported_django_version()
        ignored_app_labels = build_ignored_app_labels()
        _validate_selected_app_label(
            app_label=app_label,
            ignored_app_labels=ignored_app_labels,
        )
        loader = load_migration_loader(database_alias=database_alias, offline=offline)
        target_leaf_nodes = _filter_target_leaf_nodes(
            target_leaf_nodes=_build_target_leaf_nodes_from_loader(
                loader=loader,
                app_label=app_label,
            ),
            ignored_app_labels=ignored_app_labels,
        )
        planned_steps = tuple(
            DjangoForwardPlanProvider()._build_planned_step(
                migration=loader.graph.nodes[migration_key]
            )
            for migration_key in _generate_historical_plan_keys(
                graph=loader.graph,
                targets=target_leaf_nodes,
            )
            if migration_key[0] not in ignored_app_labels
        )
        return ForwardMigrationPlan(
            database_alias=database_alias,
            selected_app_label=app_label,
            scope=RiskAnalysisScope.HISTORY,
            target_leaf_nodes=target_leaf_nodes,
            steps=planned_steps,
        )
