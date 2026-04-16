"""Plain-text renderer for graph inspection reports."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.reports import (
    AppHeadGroup,
    DependencyHotspot,
    GraphInspectionReport,
)


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    resolved_plural = plural or f"{singular}s"
    noun = singular if count == 1 else resolved_plural
    return f"{count} {noun}"


def _be_verb(count: int) -> str:
    return "is" if count == 1 else "are"


def _have_verb(count: int) -> str:
    return "has" if count == 1 else "have"


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


@dataclass(frozen=True, slots=True)
class GraphTextRenderOptions:
    """Configuration for graph text rendering."""

    details: bool = False


@dataclass(slots=True)
class TextGraphReportRenderer:
    """Render graph reports for local CLI usage."""

    options: GraphTextRenderOptions = GraphTextRenderOptions()

    def render(self, report: GraphInspectionReport) -> str:
        """Render the graph report into plain text."""

        title = "Django Migration Inspector Graph Check"
        decision = "REVIEW GRAPH" if report.multiple_head_apps or report.merge_nodes else "CLEAR"
        lines = [
            title,
            "=" * len(title),
            f"Decision: {decision}",
            (
                f"Scope: {report.selected_app_label}"
                if report.selected_app_label is not None
                else f"Visible apps: {report.total_apps}"
            ),
            f"Visible migrations: {report.total_migrations}",
        ]
        if report.offline:
            lines.append("Source: migration files only (offline)")

        lines.extend(
            [
                "",
                "Summary:",
            ]
        )
        lines.extend(
            [
                (
                    f"  - {_pluralize(len(report.multiple_head_apps), 'app')} "
                    f"{_have_verb(len(report.multiple_head_apps))} multiple heads."
                ),
                (
                    f"  - {_pluralize(len(report.merge_nodes), 'merge migration')} "
                    f"{_be_verb(len(report.merge_nodes))} present."
                ),
                "  - "
                f"{_pluralize(len(report.dependency_hotspots), 'dependency hotspot')} may affect "
                "planning.",
            ]
        )

        lines.extend(["", "Graph issues:"])
        if not report.multiple_head_apps and not report.merge_nodes:
            lines.append("  - No multiple heads or merge migrations found in the visible scope.")
        else:
            if report.multiple_head_apps:
                for app_head_group in report.multiple_head_apps:
                    head_list = ", ".join(head.identifier for head in app_head_group.heads)
                    lines.append(
                        "  - "
                        f"{app_head_group.app_label} has {len(app_head_group.heads)} heads: "
                        f"{head_list}"
                    )
            if report.merge_nodes:
                lines.extend([f"  - {merge_node.identifier}" for merge_node in report.merge_nodes])

        lines.extend(["", "Hotspots:"])
        lines.extend(_format_hotspots(report.dependency_hotspots))

        if self.options.details:
            lines.extend(
                [
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
                ]
            )
        elif report.root_nodes or report.leaf_nodes:
            command = (
                "python manage.py migration_inspect --offline --details"
                if report.offline
                else "python manage.py migration_inspect --details"
            )
            lines.extend(
                [
                    "",
                    "Next step:",
                    f"  - Run `{command}` for root and leaf migration lists.",
                ]
            )
        return "\n".join(lines) + "\n"
