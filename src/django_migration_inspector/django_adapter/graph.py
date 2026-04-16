"""Build normalized graph snapshots from Django migration internals."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from django.db.migrations.graph import Node
from django.db.migrations.loader import MigrationLoader

from django_migration_inspector.django_adapter.app_ignore import build_ignored_app_labels
from django_migration_inspector.django_adapter.compat import validate_supported_django_version
from django_migration_inspector.django_adapter.loader import load_migration_loader
from django_migration_inspector.django_adapter.operations import build_operation_descriptor
from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.models import MigrationGraphSnapshot, MigrationNode


def _key_sort_key(migration_key: MigrationNodeKey) -> tuple[str, str]:
    return (migration_key.app_label, migration_key.migration_name)


def _resolve_module_path(module_name: str) -> Path | None:
    module = sys.modules.get(module_name)
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        return None
    return Path(module_file).resolve()


def _sorted_node_keys(
    raw_nodes: set[Node],
    *,
    ignored_app_labels: frozenset[str],
) -> tuple[MigrationNodeKey, ...]:
    return tuple(
        sorted(
            (
                MigrationNodeKey.from_tuple(node.key)
                for node in raw_nodes
                if node.key[0] not in ignored_app_labels
            ),
            key=_key_sort_key,
        )
    )


def build_graph_snapshot(
    loader: MigrationLoader,
    *,
    ignored_app_labels: frozenset[str],
) -> MigrationGraphSnapshot:
    """Normalize the loaded Django migration graph into immutable domain objects."""

    migration_nodes: list[MigrationNode] = []
    for raw_key in sorted(loader.graph.nodes, key=lambda item: (item[0], item[1])):
        if raw_key[0] in ignored_app_labels:
            continue
        migration = loader.graph.nodes[raw_key]
        graph_node = loader.graph.node_map[raw_key]
        migration_key = MigrationNodeKey.from_tuple(raw_key)
        operations = tuple(
            build_operation_descriptor(operation=operation, index=index)
            for index, operation in enumerate(migration.operations)
        )
        migration_nodes.append(
            MigrationNode(
                key=migration_key,
                dependencies=_sorted_node_keys(
                    graph_node.parents,
                    ignored_app_labels=ignored_app_labels,
                ),
                dependents=_sorted_node_keys(
                    graph_node.children,
                    ignored_app_labels=ignored_app_labels,
                ),
                replaces=tuple(
                    sorted(
                        (
                            MigrationNodeKey.from_tuple(replacement)
                            for replacement in (migration.replaces or [])
                            if replacement[0] not in ignored_app_labels
                        ),
                        key=_key_sort_key,
                    )
                ),
                operations=operations,
                is_initial=bool(migration.initial),
                module=migration.__module__,
                file_path=_resolve_module_path(migration.__module__),
            )
        )

    nodes = tuple(sorted(migration_nodes, key=lambda node: _key_sort_key(node.key)))
    root_nodes = tuple(
        sorted((node.key for node in nodes if not node.dependencies), key=_key_sort_key)
    )
    leaf_nodes = tuple(
        sorted((node.key for node in nodes if not node.dependents), key=_key_sort_key)
    )
    app_labels = tuple(sorted({node.key.app_label for node in nodes}))
    return MigrationGraphSnapshot(
        nodes=nodes,
        app_labels=app_labels,
        root_nodes=root_nodes,
        leaf_nodes=leaf_nodes,
    )


@dataclass(slots=True)
class DjangoMigrationGraphProvider:
    """Production graph provider backed by Django migration internals."""

    def build_snapshot(
        self, database_alias: str, *, offline: bool = False
    ) -> MigrationGraphSnapshot:
        """Build a normalized snapshot for the requested database alias."""

        validate_supported_django_version()
        loader = load_migration_loader(database_alias=database_alias, offline=offline)
        return build_graph_snapshot(
            loader=loader,
            ignored_app_labels=build_ignored_app_labels(),
        )
