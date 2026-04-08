"""Shared helpers for graph visualization renderers."""

from __future__ import annotations

import re
from typing import TypeAlias

from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.reports import GraphInspectionReport

GraphEdge: TypeAlias = tuple[MigrationNodeKey, MigrationNodeKey]


def build_visible_edges(report: GraphInspectionReport) -> tuple[GraphEdge, ...]:
    """Build dependency edges limited to nodes visible in the current report."""

    visible_keys = {node.key for node in report.nodes}
    edges = {
        (dependency, node.key)
        for node in report.nodes
        for dependency in node.dependencies
        if dependency in visible_keys
    }
    return tuple(
        sorted(
            edges,
            key=lambda edge: (
                edge[0].app_label,
                edge[0].migration_name,
                edge[1].app_label,
                edge[1].migration_name,
            ),
        )
    )


def build_multiple_head_key_set(report: GraphInspectionReport) -> frozenset[MigrationNodeKey]:
    """Return the set of leaf nodes belonging to apps with multiple heads."""

    return frozenset(
        head for app_head_group in report.multiple_head_apps for head in app_head_group.heads
    )


def build_mermaid_node_id(migration_key: MigrationNodeKey) -> str:
    """Create a Mermaid-safe node identifier."""

    sanitized_identifier = re.sub(r"[^0-9A-Za-z_]", "_", migration_key.identifier)
    return f"node_{sanitized_identifier}"


def escape_mermaid_label(label: str) -> str:
    """Escape a node label for Mermaid output."""

    return label.replace('"', '\\"')


def escape_dot_label(label: str) -> str:
    """Escape a node label for Graphviz DOT output."""

    return label.replace("\\", "\\\\").replace('"', '\\"')
