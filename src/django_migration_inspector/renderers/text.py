"""Plain-text renderer for graph inspection reports."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.reports import (
    AppHeadGroup,
    DependencyHotspot,
    GraphInspectionReport,
)


def _format_node_keys(node_keys: tuple[MigrationNodeKey, ...]) -> list[str]:
    if not node_keys:
        return ["  - none"]
    return [f"  - {node_key.identifier}" for node_key in node_keys]


def _format_app_heads(app_head_groups: tuple[AppHeadGroup, ...]) -> list[str]:
    if not app_head_groups:
        return ["  - none"]

    lines: list[str] = []
    for app_head_group in app_head_groups:
        head_list = ", ".join(head.identifier for head in app_head_group.heads)
        lines.append(f"  - {app_head_group.app_label}: {head_list}")
    return lines


def _format_hotspots(dependency_hotspots: tuple[DependencyHotspot, ...]) -> list[str]:
    if not dependency_hotspots:
        return ["  - none"]

    return [
        (
            "  - "
            f"{hotspot.node.identifier} "
            f"(dependents={hotspot.dependent_count}, dependencies={hotspot.dependency_count})"
        )
        for hotspot in dependency_hotspots
    ]


@dataclass(slots=True)
class TextGraphReportRenderer:
    """Render graph reports for local CLI usage."""

    def render(self, report: GraphInspectionReport) -> str:
        """Render the graph report into plain text."""

        scope = report.selected_app_label or "all apps"
        lines = [
            "Django Migration Inspector",
            "==========================",
            f"Database alias: {report.database_alias}",
            f"Scope: {scope}",
            f"Total apps: {report.total_apps}",
            f"Total migrations: {report.total_migrations}",
            "",
            "Root migrations:",
            *_format_node_keys(report.root_nodes),
            "",
            "Leaf migrations:",
            *_format_node_keys(report.leaf_nodes),
            "",
            "Merge migrations:",
            *_format_node_keys(report.merge_nodes),
            "",
            "Apps with multiple heads:",
            *_format_app_heads(report.multiple_head_apps),
            "",
            "Dependency hotspots:",
            *_format_hotspots(report.dependency_hotspots),
        ]
        return "\n".join(lines) + "\n"
