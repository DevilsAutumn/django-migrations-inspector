"""Report objects emitted by analyzers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from django_migration_inspector.constants import REPORT_SCHEMA_VERSION

from .keys import MigrationNodeKey, MigrationNodeKeyJSON
from .models import MigrationNode, MigrationNodeJSON


class AppHeadGroupJSON(TypedDict):
    """Stable JSON shape for multiple-head app groups."""

    app_label: str
    heads: list[MigrationNodeKeyJSON]


class DependencyHotspotJSON(TypedDict):
    """Stable JSON shape for dependency hotspots."""

    node: MigrationNodeKeyJSON
    dependency_count: int
    dependent_count: int


class GraphInspectionReportJSON(TypedDict):
    """Stable JSON shape for graph inspection reports."""

    schema_version: str
    report_type: str
    database_alias: str
    selected_app_label: str | None
    total_apps: int
    total_migrations: int
    root_nodes: list[MigrationNodeKeyJSON]
    leaf_nodes: list[MigrationNodeKeyJSON]
    merge_nodes: list[MigrationNodeKeyJSON]
    multiple_head_apps: list[AppHeadGroupJSON]
    dependency_hotspots: list[DependencyHotspotJSON]
    nodes: list[MigrationNodeJSON]


@dataclass(frozen=True, slots=True)
class AppHeadGroup:
    """A group of leaf migrations for one app with multiple heads."""

    app_label: str
    heads: tuple[MigrationNodeKey, ...]

    def to_json_dict(self) -> AppHeadGroupJSON:
        """Serialize the group into the report JSON contract."""

        return {
            "app_label": self.app_label,
            "heads": [head.to_json_dict() for head in self.heads],
        }


@dataclass(frozen=True, slots=True)
class DependencyHotspot:
    """A node with many dependents in the visible graph."""

    node: MigrationNodeKey
    dependency_count: int
    dependent_count: int

    def to_json_dict(self) -> DependencyHotspotJSON:
        """Serialize the hotspot into the report JSON contract."""

        return {
            "node": self.node.to_json_dict(),
            "dependency_count": self.dependency_count,
            "dependent_count": self.dependent_count,
        }


@dataclass(frozen=True, slots=True)
class GraphInspectionReport:
    """Output of the graph intelligence analyzer."""

    database_alias: str
    selected_app_label: str | None
    total_apps: int
    total_migrations: int
    root_nodes: tuple[MigrationNodeKey, ...]
    leaf_nodes: tuple[MigrationNodeKey, ...]
    merge_nodes: tuple[MigrationNodeKey, ...]
    multiple_head_apps: tuple[AppHeadGroup, ...]
    dependency_hotspots: tuple[DependencyHotspot, ...]
    nodes: tuple[MigrationNode, ...]

    def to_json_dict(self) -> GraphInspectionReportJSON:
        """Serialize the report into the stable JSON contract."""

        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "report_type": "graph_inspection",
            "database_alias": self.database_alias,
            "selected_app_label": self.selected_app_label,
            "total_apps": self.total_apps,
            "total_migrations": self.total_migrations,
            "root_nodes": [root_node.to_json_dict() for root_node in self.root_nodes],
            "leaf_nodes": [leaf_node.to_json_dict() for leaf_node in self.leaf_nodes],
            "merge_nodes": [merge_node.to_json_dict() for merge_node in self.merge_nodes],
            "multiple_head_apps": [
                app_head_group.to_json_dict() for app_head_group in self.multiple_head_apps
            ],
            "dependency_hotspots": [
                dependency_hotspot.to_json_dict()
                for dependency_hotspot in self.dependency_hotspots
            ],
            "nodes": [node.to_json_dict() for node in self.nodes],
        }

