"""Plain-text renderer for rollback simulation reports."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import pairwise

from django_migration_inspector.domain.enums import RiskSeverity
from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.reports import (
    RollbackBlocker,
    RollbackSimulationReport,
)


def _severity_rank(severity: RiskSeverity) -> int:
    return {
        RiskSeverity.NONE: 0,
        RiskSeverity.LOW: 1,
        RiskSeverity.MEDIUM: 2,
        RiskSeverity.HIGH: 3,
        RiskSeverity.CRITICAL: 4,
    }[severity]


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    resolved_plural = plural or f"{singular}s"
    noun = singular if count == 1 else resolved_plural
    return f"{count} {noun}"


def _format_operation_reference(
    *,
    operation_index: int | None,
    operation_path: str | None,
) -> str | None:
    if operation_index is None or operation_path is None:
        return None
    if operation_path == str(operation_index):
        return f"op #{operation_index}"
    return f"op {operation_path}"


@dataclass(frozen=True, slots=True)
class RollbackTextRenderOptions:
    """Configuration for rollback text rendering."""

    details: bool = False
    show_operations: bool = False
    why_app: str | None = None
    max_summary_blockers: int = 5
    max_summary_risky_migrations: int = 8
    max_summary_app_reasons: int = 12


@dataclass(frozen=True, slots=True)
class _AppImpactSummary:
    app_label: str
    step_count: int
    operation_count: int
    blocker_count: int
    concern_count: int
    high_or_worse_concern_count: int


@dataclass(frozen=True, slots=True)
class _MigrationRiskSummary:
    migration: MigrationNodeKey
    highest_severity: RiskSeverity
    blocker_count: int
    concern_count: int
    high_or_worse_concern_count: int


@dataclass(slots=True)
class TextRollbackReportRenderer:
    """Render rollback simulation reports for local CLI usage."""

    options: RollbackTextRenderOptions = RollbackTextRenderOptions()

    def render(self, report: RollbackSimulationReport) -> str:
        """Render the rollback report into plain text."""

        title = "Django Migration Inspector Rollback Check"
        lines = [
            title,
            "=" * len(title),
            f"Decision: {self._format_decision(report)}",
            f"Target: {report.plan.target_identifier}",
            "Blast radius: "
            f"{_pluralize(report.step_count, 'step')} in "
            f"{_pluralize(len(report.plan.affected_app_labels), 'app')}",
        ]

        if report.database_alias != "default":
            lines.append(f"Database alias: {report.database_alias}")

        lines.extend(self._render_summary(report))
        lines.extend(self._render_blocker_summary(report))
        lines.extend(self._render_inclusion_reasons(report))
        lines.extend(self._render_app_impact_summary(report))
        lines.extend(self._render_risky_migration_summary(report))

        if self.options.details:
            lines.extend(self._render_step_details(report))
            lines.extend(self._render_full_concerns(report))
        else:
            lines.extend(self._render_next_step(report))

        return "\n".join(lines) + "\n"

    def _format_decision(self, report: RollbackSimulationReport) -> str:
        if not report.rollback_possible:
            return "BLOCKED"
        if not report.rollback_safe:
            return "HIGH RISK"
        if report.concerns:
            return "REVIEW REQUIRED"
        return "CLEAR"

    def _render_summary(self, report: RollbackSimulationReport) -> list[str]:
        lines = ["", "Summary:"]
        if report.blockers:
            blocker_migration_count = len({blocker.migration for blocker in report.blockers})
            lines.append(
                "  - "
                f"{_pluralize(blocker_migration_count, 'migration')} "
                f"{'blocks' if blocker_migration_count == 1 else 'block'} a clean rollback path."
            )

        rollback_removal_migrations = {
            concern.migration
            for concern in report.concerns
            if concern.category in {"rollback_drops_table", "rollback_removes_field"}
        }
        if rollback_removal_migrations:
            rollback_removal_count = len(rollback_removal_migrations)
            lines.append(
                "  - "
                f"{_pluralize(rollback_removal_count, 'migration')} "
                f"{'removes' if rollback_removal_count == 1 else 'remove'} tables or columns "
                "introduced after the target migration. This is expected for rollback, but can "
                "delete live data."
            )

        schema_restore_migrations = {
            concern.migration
            for concern in report.concerns
            if concern.category in {"data_loss_reversal", "table_restore"}
        }
        if schema_restore_migrations:
            schema_restore_count = len(schema_restore_migrations)
            lines.append(
                "  - "
                f"{_pluralize(schema_restore_count, 'migration')} "
                f"{'restores' if schema_restore_count == 1 else 'restore'} schema shape without "
                "restoring deleted data."
            )

        external_app_count = len(
            [
                app_label
                for app_label in report.plan.affected_app_labels
                if app_label != report.plan.target_app_label
            ]
        )
        if external_app_count:
            lines.append(
                "  - "
                f"Rollback reaches {_pluralize(external_app_count, 'additional app')} through "
                "dependencies."
            )

        if not report.blockers and not report.concerns:
            lines.append("  - No rollback blockers or major concerns detected in this path.")
        return lines

    def _render_blocker_summary(self, report: RollbackSimulationReport) -> list[str]:
        lines = ["", "Critical blockers:"]
        if not report.blockers:
            lines.append("  - none")
            return lines

        blockers = report.blockers[: self.options.max_summary_blockers]
        for blocker in blockers:
            lines.extend(self._render_blocker_entry(blocker))

        remaining_blockers = len(report.blockers) - len(blockers)
        if remaining_blockers > 0:
            lines.append(
                "  - "
                f"{_pluralize(remaining_blockers, 'additional blocker')} hidden. "
                "Use --details for the full blocker list."
            )
        return lines

    def _render_blocker_entry(self, blocker: RollbackBlocker) -> list[str]:
        operation_reference = _format_operation_reference(
            operation_index=blocker.operation_index,
            operation_path=blocker.operation_path,
        )
        return [
            (
                "  - "
                f"{blocker.migration.identifier} "
                f"({operation_reference}: {blocker.operation_name})"
            ),
            f"    {blocker.message}",
            f"    Recommendation: {blocker.recommendation}",
        ]

    def _render_inclusion_reasons(self, report: RollbackSimulationReport) -> list[str]:
        lines = [""]
        if self.options.why_app is not None:
            lines.append(f"Why {self.options.why_app} is included:")
            lines.extend(self._render_single_app_reason(report, self.options.why_app))
            return lines

        lines.append("Why other apps are included:")
        external_apps = tuple(
            app_label
            for app_label in report.plan.affected_app_labels
            if app_label != report.plan.target_app_label
        )
        if not external_apps:
            lines.append("  - none")
            return lines

        displayed_apps = external_apps[: self.options.max_summary_app_reasons]
        for app_label in displayed_apps:
            lines.append(f"  - {app_label}: {self._render_short_reason(report, app_label)}")

        remaining_apps = len(external_apps) - len(displayed_apps)
        if remaining_apps > 0:
            lines.append(
                "  - "
                f"{_pluralize(remaining_apps, 'additional app')} hidden. "
                "Use --why-app APP_LABEL for a focused explanation."
            )
        return lines

    def _render_single_app_reason(
        self,
        report: RollbackSimulationReport,
        app_label: str,
    ) -> list[str]:
        if app_label == report.plan.target_app_label:
            return [f"  - {app_label} is the requested rollback target."]

        if app_label not in report.plan.affected_app_labels:
            return [f"  - {app_label} is not part of the current rollback plan."]

        dependency_path = self._find_dependency_path(report, app_label)
        if dependency_path is None or len(dependency_path) < 2:
            return [f"  - {self._render_short_reason(report, app_label)}"]

        lines: list[str] = []
        for current, dependency in pairwise(dependency_path):
            lines.append(f"  - {current.identifier} depends on {dependency.identifier}")
        return lines

    def _render_short_reason(self, report: RollbackSimulationReport, app_label: str) -> str:
        dependency_edge = self._find_app_entry_dependency(report, app_label)
        if dependency_edge is None:
            return "included through transitive dependencies in the rollback plan"

        migration_key, dependency_key = dependency_edge
        return f"{migration_key.identifier} depends on {dependency_key.identifier}"

    def _find_app_entry_dependency(
        self,
        report: RollbackSimulationReport,
        app_label: str,
    ) -> tuple[MigrationNodeKey, MigrationNodeKey] | None:
        plan_keys = {step.key for step in report.plan.steps}
        relevant_steps = tuple(
            step for step in reversed(report.plan.steps) if step.key.app_label == app_label
        )
        for step in relevant_steps:
            cross_app_dependencies = tuple(
                sorted(
                    (
                        dependency
                        for dependency in step.dependencies
                        if dependency in plan_keys and dependency.app_label != app_label
                    ),
                    key=lambda dependency: (
                        dependency.app_label != report.plan.target_app_label,
                        dependency.app_label,
                        dependency.migration_name,
                    ),
                )
            )
            if cross_app_dependencies:
                return (step.key, cross_app_dependencies[0])
        return None

    def _find_dependency_path(
        self,
        report: RollbackSimulationReport,
        app_label: str,
    ) -> tuple[MigrationNodeKey, ...] | None:
        dependency_edge = self._find_app_entry_dependency(report, app_label)
        if dependency_edge is None:
            return None

        start_key = dependency_edge[0]
        step_by_key = {step.key: step for step in report.plan.steps}
        target_keys = {
            step.key
            for step in report.plan.steps
            if step.key.app_label == report.plan.target_app_label
        }
        queue: deque[MigrationNodeKey] = deque([start_key])
        previous: dict[MigrationNodeKey, MigrationNodeKey | None] = {start_key: None}

        while queue:
            current_key = queue.popleft()
            if current_key in target_keys:
                return self._reconstruct_path(previous=previous, end_key=current_key)

            current_step = step_by_key[current_key]
            next_dependencies = tuple(
                sorted(
                    (
                        dependency
                        for dependency in current_step.dependencies
                        if dependency in step_by_key
                    ),
                    key=lambda dependency: (
                        dependency.app_label != report.plan.target_app_label,
                        dependency.app_label,
                        dependency.migration_name,
                    ),
                )
            )
            for dependency in next_dependencies:
                if dependency in previous:
                    continue
                previous[dependency] = current_key
                queue.append(dependency)

        direct_dependency = dependency_edge[1]
        return (start_key, direct_dependency)

    def _reconstruct_path(
        self,
        *,
        previous: dict[MigrationNodeKey, MigrationNodeKey | None],
        end_key: MigrationNodeKey,
    ) -> tuple[MigrationNodeKey, ...]:
        path: list[MigrationNodeKey] = [end_key]
        cursor = previous[end_key]
        while cursor is not None:
            path.append(cursor)
            cursor = previous[cursor]
        path.reverse()
        return tuple(path)

    def _render_app_impact_summary(self, report: RollbackSimulationReport) -> list[str]:
        lines = ["", "App impact summary:"]
        summaries = self._build_app_impact_summaries(report)
        if not summaries:
            lines.append("  - none")
            return lines

        for summary in summaries:
            label = summary.app_label
            if label == report.plan.target_app_label:
                label = f"{label} [target]"

            detail_parts = [
                _pluralize(summary.step_count, "step"),
                _pluralize(summary.operation_count, "operation"),
            ]
            if summary.blocker_count:
                detail_parts.append(_pluralize(summary.blocker_count, "blocker"))
            if summary.high_or_worse_concern_count:
                detail_parts.append(_pluralize(summary.high_or_worse_concern_count, "high concern"))
            elif summary.concern_count:
                detail_parts.append(_pluralize(summary.concern_count, "concern"))

            lines.append(f"  - {label}: {', '.join(detail_parts)}")
        return lines

    def _build_app_impact_summaries(
        self,
        report: RollbackSimulationReport,
    ) -> tuple[_AppImpactSummary, ...]:
        step_counts: dict[str, int] = {}
        operation_counts: dict[str, int] = {}
        blocker_counts: dict[str, int] = {}
        concern_counts: dict[str, int] = {}
        high_concern_counts: dict[str, int] = {}

        for step in report.plan.steps:
            step_counts[step.key.app_label] = step_counts.get(step.key.app_label, 0) + 1
            operation_counts[step.key.app_label] = (
                operation_counts.get(step.key.app_label, 0) + step.operation_count
            )

        for blocker in report.blockers:
            blocker_counts[blocker.migration.app_label] = (
                blocker_counts.get(blocker.migration.app_label, 0) + 1
            )

        for concern in report.concerns:
            concern_counts[concern.migration.app_label] = (
                concern_counts.get(concern.migration.app_label, 0) + 1
            )
            if _severity_rank(concern.severity) >= _severity_rank(RiskSeverity.HIGH):
                high_concern_counts[concern.migration.app_label] = (
                    high_concern_counts.get(concern.migration.app_label, 0) + 1
                )

        summaries = tuple(
            _AppImpactSummary(
                app_label=app_label,
                step_count=step_counts.get(app_label, 0),
                operation_count=operation_counts.get(app_label, 0),
                blocker_count=blocker_counts.get(app_label, 0),
                concern_count=concern_counts.get(app_label, 0),
                high_or_worse_concern_count=high_concern_counts.get(app_label, 0),
            )
            for app_label in report.plan.affected_app_labels
        )
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (
                    summary.app_label != report.plan.target_app_label,
                    -summary.blocker_count,
                    -summary.high_or_worse_concern_count,
                    -summary.step_count,
                    summary.app_label,
                ),
            )
        )

    def _render_risky_migration_summary(self, report: RollbackSimulationReport) -> list[str]:
        lines = ["", "Top risky migrations:"]
        summaries = self._build_risky_migration_summaries(report)
        if not summaries:
            lines.append("  - none")
            return lines

        displayed_summaries = summaries[: self.options.max_summary_risky_migrations]
        for summary in displayed_summaries:
            detail_parts: list[str] = []
            if summary.blocker_count:
                detail_parts.append(_pluralize(summary.blocker_count, "blocker"))
            if summary.high_or_worse_concern_count:
                detail_parts.append(_pluralize(summary.high_or_worse_concern_count, "high concern"))
            remaining_concerns = summary.concern_count - summary.high_or_worse_concern_count
            if remaining_concerns:
                detail_parts.append(_pluralize(remaining_concerns, "additional concern"))
            lines.append(
                "  - "
                f"[{summary.highest_severity.value.upper()}] "
                f"{summary.migration.identifier}: {', '.join(detail_parts)}"
            )

        remaining_summaries = len(summaries) - len(displayed_summaries)
        if remaining_summaries > 0:
            lines.append(
                "  - "
                f"{_pluralize(remaining_summaries, 'additional risky migration')} hidden. "
                "Use --details for the full concern list."
            )
        return lines

    def _build_risky_migration_summaries(
        self,
        report: RollbackSimulationReport,
    ) -> tuple[_MigrationRiskSummary, ...]:
        blocker_counts: dict[MigrationNodeKey, int] = {}
        concern_counts: dict[MigrationNodeKey, int] = {}
        high_concern_counts: dict[MigrationNodeKey, int] = {}
        highest_severity: dict[MigrationNodeKey, RiskSeverity] = {}

        for blocker in report.blockers:
            blocker_counts[blocker.migration] = blocker_counts.get(blocker.migration, 0) + 1
            highest_severity[blocker.migration] = RiskSeverity.CRITICAL

        for concern in report.concerns:
            concern_counts[concern.migration] = concern_counts.get(concern.migration, 0) + 1
            if _severity_rank(concern.severity) >= _severity_rank(RiskSeverity.HIGH):
                high_concern_counts[concern.migration] = (
                    high_concern_counts.get(concern.migration, 0) + 1
                )
            current_severity = highest_severity.get(concern.migration, RiskSeverity.NONE)
            if _severity_rank(concern.severity) > _severity_rank(current_severity):
                highest_severity[concern.migration] = concern.severity

        migration_keys = tuple(
            sorted(
                set(blocker_counts) | set(concern_counts),
                key=lambda migration_key: migration_key.identifier,
            )
        )
        summaries = tuple(
            _MigrationRiskSummary(
                migration=migration_key,
                highest_severity=highest_severity.get(migration_key, RiskSeverity.NONE),
                blocker_count=blocker_counts.get(migration_key, 0),
                concern_count=concern_counts.get(migration_key, 0),
                high_or_worse_concern_count=high_concern_counts.get(migration_key, 0),
            )
            for migration_key in migration_keys
        )
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (
                    -_severity_rank(summary.highest_severity),
                    -summary.blocker_count,
                    -summary.high_or_worse_concern_count,
                    -summary.concern_count,
                    summary.migration.identifier,
                ),
            )
        )

    def _render_step_details(self, report: RollbackSimulationReport) -> list[str]:
        lines = ["", "Rollback steps:"]
        if not report.plan.steps:
            lines.append("  - none")
            return lines

        for step in report.plan.steps:
            flags: list[str] = []
            if step.is_merge:
                flags.append("merge")
            if step.has_irreversible_operation:
                flags.append("blocker")
            detail_parts = [_pluralize(step.operation_count, "operation")]
            detail_parts.extend(flags)
            lines.append(f"  - {step.key.identifier} ({', '.join(detail_parts)})")
            if not self.options.show_operations:
                continue
            if not step.reverse_operations:
                lines.append("    - no operations")
                continue
            for operation in step.iter_reverse_operations():
                marker = "BLOCKER" if not operation.is_reversible else "op"
                operation_reference = _format_operation_reference(
                    operation_index=operation.index,
                    operation_path=operation.path,
                )
                lines.append(
                    f"    - [{marker}] {operation_reference} "
                    f"{operation.name}: {operation.description}"
                )
        return lines

    def _render_full_concerns(self, report: RollbackSimulationReport) -> list[str]:
        lines = ["", "All concerns:"]
        if not report.concerns:
            lines.append("  - none")
            return lines

        for concern in report.concerns:
            operation_reference = _format_operation_reference(
                operation_index=concern.operation_index,
                operation_path=concern.operation_path,
            )
            operation_label = (
                f" ({operation_reference}: {concern.operation_name})"
                if operation_reference is not None and concern.operation_name is not None
                else ""
            )
            lines.extend(
                [
                    (
                        "  - "
                        f"[{concern.severity.value.upper()}] "
                        f"{concern.migration.identifier}{operation_label}"
                    ),
                    f"    {concern.message}",
                    f"    Recommendation: {concern.recommendation}",
                ]
            )
        return lines

    def _render_next_step(self, report: RollbackSimulationReport) -> list[str]:
        target_app_label = report.plan.target_app_label
        target_migration_name = report.plan.target_migration_name or "zero"
        lines = ["", "Next step:"]
        lines.append(
            "  - Run "
            f"`python manage.py migration_inspect rollback {target_app_label} "
            f"{target_migration_name} --details` for the full rollback step list."
        )
        lines.append(
            "  - Run "
            f"`python manage.py migration_inspect rollback {target_app_label} "
            f"{target_migration_name} --show-operations` to inspect reverse operations for each "
            "step."
        )
        if any(app != report.plan.target_app_label for app in report.plan.affected_app_labels):
            lines.append(
                "  - Run "
                f"`python manage.py migration_inspect rollback {target_app_label} "
                f"{target_migration_name} --why-app APP_LABEL` to explain one cross-app "
                "dependency chain."
            )
        return lines
