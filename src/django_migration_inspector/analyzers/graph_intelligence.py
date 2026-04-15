"""Migration graph analysis for CLI and CI reporting."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from django_migration_inspector.constants import DEFAULT_DEPENDENCY_HOTSPOT_LIMIT
from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.models import MigrationGraphSnapshot, MigrationNode
from django_migration_inspector.domain.reports import (
    AppHeadGroup,
    DependencyHotspot,
    GraphInspectionReport,
)
from django_migration_inspector.exceptions import MigrationInspectionError


def _key_sort_key(migration_key: MigrationNodeKey) -> tuple[str, str]:
    return (migration_key.app_label, migration_key.migration_name)


@dataclass(slots=True)
class GraphIntelligenceAnalyzer:
    """Analyze normalized migration graphs into stable reports."""

    max_hotspots: int = DEFAULT_DEPENDENCY_HOTSPOT_LIMIT

    def analyze(
        self,
        snapshot: MigrationGraphSnapshot,
        *,
        database_alias: str,
        app_label: str | None = None,
    ) -> GraphInspectionReport:
        """Analyze the migration graph and return a stable inspection report."""

        visible_nodes = self._select_nodes(snapshot=snapshot, app_label=app_label)
        visible_keys = {node.key for node in visible_nodes}
        root_nodes = tuple(
            sorted(
                (
                    node.key
                    for node in visible_nodes
                    if not any(dependency in visible_keys for dependency in node.dependencies)
                ),
                key=_key_sort_key,
            )
        )
        leaf_nodes = tuple(
            sorted(
                (
                    node.key
                    for node in visible_nodes
                    if not any(dependent in visible_keys for dependent in node.dependents)
                ),
                key=_key_sort_key,
            )
        )
        merge_nodes = tuple(
            sorted((node.key for node in visible_nodes if node.is_merge), key=_key_sort_key)
        )
        app_heads = self._build_app_heads(visible_nodes=visible_nodes, visible_keys=visible_keys)
        dependency_hotspots = self._build_dependency_hotspots(
            visible_nodes=visible_nodes,
            visible_keys=visible_keys,
        )
        return GraphInspectionReport(
            database_alias=database_alias,
            selected_app_label=app_label,
            total_apps=len({node.key.app_label for node in visible_nodes}),
            total_migrations=len(visible_nodes),
            root_nodes=root_nodes,
            leaf_nodes=leaf_nodes,
            merge_nodes=merge_nodes,
            multiple_head_apps=app_heads,
            dependency_hotspots=dependency_hotspots,
            nodes=visible_nodes,
        )

    def _select_nodes(
        self,
        *,
        snapshot: MigrationGraphSnapshot,
        app_label: str | None,
    ) -> tuple[MigrationNode, ...]:
        if app_label is None:
            return snapshot.nodes

        filtered_nodes = tuple(node for node in snapshot.nodes if node.key.app_label == app_label)
        if not filtered_nodes:
            raise MigrationInspectionError(
                f"App {app_label!r} has no migrations in the loaded Django project."
            )
        return filtered_nodes

    def _build_app_heads(
        self,
        *,
        visible_nodes: tuple[MigrationNode, ...],
        visible_keys: set[MigrationNodeKey],
    ) -> tuple[AppHeadGroup, ...]:
        heads_by_app: dict[str, list[MigrationNodeKey]] = defaultdict(list)
        for node in visible_nodes:
            visible_dependents = [
                dependent for dependent in node.dependents if dependent in visible_keys
            ]
            if not visible_dependents:
                heads_by_app[node.key.app_label].append(node.key)

        groups = [
            AppHeadGroup(
                app_label=app_name,
                heads=tuple(sorted(app_heads, key=_key_sort_key)),
            )
            for app_name, app_heads in sorted(heads_by_app.items())
            if len(app_heads) > 1
        ]
        return tuple(groups)

    def _build_dependency_hotspots(
        self,
        *,
        visible_nodes: tuple[MigrationNode, ...],
        visible_keys: set[MigrationNodeKey],
    ) -> tuple[DependencyHotspot, ...]:
        scored_nodes: list[DependencyHotspot] = []
        for node in visible_nodes:
            dependency_count = sum(
                1 for dependency in node.dependencies if dependency in visible_keys
            )
            dependent_count = sum(1 for dependent in node.dependents if dependent in visible_keys)
            if dependent_count == 0:
                continue
            scored_nodes.append(
                DependencyHotspot(
                    node=node.key,
                    dependency_count=dependency_count,
                    dependent_count=dependent_count,
                )
            )

        sorted_nodes = sorted(
            scored_nodes,
            key=lambda hotspot: (
                -hotspot.dependent_count,
                -hotspot.dependency_count,
                hotspot.node.app_label,
                hotspot.node.migration_name,
            ),
        )
        return tuple(sorted_nodes[: self.max_hotspots])
