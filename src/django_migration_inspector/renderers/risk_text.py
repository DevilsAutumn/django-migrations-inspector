"""Plain-text renderer for risk assessment reports."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.enums import (
    RiskAnalysisScope,
    RiskDecision,
    RiskFindingKind,
    RiskSeverity,
)
from django_migration_inspector.domain.keys import MigrationNodeKey
from django_migration_inspector.domain.reports import RiskAssessmentReport


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    resolved_plural = plural or f"{singular}s"
    noun = singular if count == 1 else resolved_plural
    return f"{count} {noun}"


@dataclass(frozen=True, slots=True)
class RiskTextRenderOptions:
    """Configuration for risk text rendering."""

    details: bool = False
    max_summary_apps: int = 6
    max_summary_migrations: int = 6


@dataclass(frozen=True, slots=True)
class _RiskAppSummary:
    app_label: str
    risky_migration_count: int
    blocked_migration_count: int
    destructive_migration_count: int
    review_migration_count: int


@dataclass(frozen=True, slots=True)
class _RiskMigrationSummary:
    migration: MigrationNodeKey
    highest_severity: RiskSeverity
    blocked_count: int
    destructive_count: int
    review_count: int


@dataclass(slots=True)
class TextRiskReportRenderer:
    """Render risk reports for local CLI usage."""

    options: RiskTextRenderOptions = RiskTextRenderOptions()

    def render(self, report: RiskAssessmentReport) -> str:
        """Render the risk report into plain text."""

        is_pending_scope = report.analysis_scope is RiskAnalysisScope.PENDING
        title = (
            "Django Migration Inspector Pending Risk"
            if is_pending_scope
            else "Django Migration Inspector Audit"
        )
        lines = [
            title,
            "=" * len(title),
            f"Decision: {self._format_decision(report.decision)}",
            (
                f"Pending migrations: {report.pending_migration_count}"
                if is_pending_scope
                else (
                    "Risky migrations: "
                    f"{report.risky_migration_count} in {_pluralize(report.risky_app_count, 'app')}"
                )
            ),
        ]

        if report.selected_app_label is not None:
            lines.append(f"Scope: {report.selected_app_label}")
        if report.database_alias != "default":
            lines.append(f"Database alias: {report.database_alias}")

        lines.extend(self._render_summary(report))
        lines.extend(self._render_app_summary(report))
        lines.extend(self._render_migration_summary(report))

        if self.options.details:
            lines.extend(self._render_detailed_findings(report))
        else:
            lines.extend(self._render_next_step(report))

        return "\n".join(lines) + "\n"

    def _format_decision(self, decision: RiskDecision) -> str:
        if decision is RiskDecision.ROLLBACK_BLOCKED:
            return "ROLLBACK BLOCKED"
        if decision is RiskDecision.REVIEW_REQUIRED:
            return "REVIEW REQUIRED"
        return "CLEAR"

    def _render_summary(self, report: RiskAssessmentReport) -> list[str]:
        lines = ["", "Summary:"]
        if not report.findings:
            if report.analysis_scope is RiskAnalysisScope.PENDING:
                lines.append("  - No pending migrations need review in the selected scope.")
                lines.append(
                    "  - Use `python manage.py migration_inspect audit` to inspect migration "
                    "files already on disk."
                )
            else:
                lines.append("  - No risky migrations found in the selected scope.")
            return lines

        if report.blocked_migration_count:
            lines.append(
                "  - "
                f"{_pluralize(report.blocked_migration_count, 'migration')} "
                f"{'blocks' if report.blocked_migration_count == 1 else 'block'} a clean "
                "rollback path."
            )
        if report.destructive_migration_count:
            lines.append(
                "  - "
                f"{_pluralize(report.destructive_migration_count, 'migration')} "
                f"{'contains' if report.destructive_migration_count == 1 else 'contain'} "
                "destructive schema changes."
            )
        if report.review_migration_count:
            lines.append(
                "  - "
                f"{_pluralize(report.review_migration_count, 'migration')} "
                f"{'needs' if report.review_migration_count == 1 else 'need'} manual review."
            )
        return lines

    def _render_app_summary(self, report: RiskAssessmentReport) -> list[str]:
        lines = ["", "Apps needing attention:"]
        summaries = self._build_app_summaries(report)
        if not summaries:
            lines.append("  - none")
            return lines

        displayed = summaries[: self.options.max_summary_apps]
        for summary in displayed:
            detail_parts: list[str] = [_pluralize(summary.risky_migration_count, "migration")]
            if summary.blocked_migration_count:
                detail_parts.append(_pluralize(summary.blocked_migration_count, "blocker"))
            if summary.destructive_migration_count:
                detail_parts.append(
                    _pluralize(summary.destructive_migration_count, "destructive change")
                )
            elif summary.review_migration_count:
                detail_parts.append(_pluralize(summary.review_migration_count, "review item"))
            lines.append(f"  - {summary.app_label}: {', '.join(detail_parts)}")

        hidden = len(summaries) - len(displayed)
        if hidden > 0:
            lines.append(f"  - {_pluralize(hidden, 'additional app')} hidden.")
        return lines

    def _build_app_summaries(self, report: RiskAssessmentReport) -> tuple[_RiskAppSummary, ...]:
        risky_migrations: dict[str, set[MigrationNodeKey]] = {}
        blocked_migrations: dict[str, set[MigrationNodeKey]] = {}
        destructive_migrations: dict[str, set[MigrationNodeKey]] = {}
        review_migrations: dict[str, set[MigrationNodeKey]] = {}

        for finding in report.findings:
            app_label = finding.migration.app_label
            risky_migrations.setdefault(app_label, set()).add(finding.migration)
            if finding.kind is RiskFindingKind.BLOCKED:
                blocked_migrations.setdefault(app_label, set()).add(finding.migration)
            elif finding.kind is RiskFindingKind.DESTRUCTIVE:
                destructive_migrations.setdefault(app_label, set()).add(finding.migration)
            else:
                review_migrations.setdefault(app_label, set()).add(finding.migration)

        summaries = tuple(
            _RiskAppSummary(
                app_label=app_label,
                risky_migration_count=len(risky_migrations.get(app_label, set())),
                blocked_migration_count=len(blocked_migrations.get(app_label, set())),
                destructive_migration_count=len(destructive_migrations.get(app_label, set())),
                review_migration_count=len(review_migrations.get(app_label, set())),
            )
            for app_label in risky_migrations
        )
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (
                    -summary.blocked_migration_count,
                    -summary.destructive_migration_count,
                    -summary.risky_migration_count,
                    summary.app_label,
                ),
            )
        )

    def _render_migration_summary(self, report: RiskAssessmentReport) -> list[str]:
        lines = ["", "Top migrations:"]
        summaries = self._build_migration_summaries(report)
        if not summaries:
            lines.append("  - none")
            return lines

        displayed = summaries[: self.options.max_summary_migrations]
        for summary in displayed:
            labels: list[str] = []
            if summary.blocked_count:
                labels.append(_pluralize(summary.blocked_count, "rollback blocker"))
            if summary.destructive_count:
                labels.append(_pluralize(summary.destructive_count, "destructive change"))
            if summary.review_count:
                labels.append(_pluralize(summary.review_count, "review item"))
            lines.append(f"  - {summary.migration.identifier}: {', '.join(labels)}")

        hidden = len(summaries) - len(displayed)
        if hidden > 0:
            lines.append(f"  - {_pluralize(hidden, 'additional migration')} hidden.")
        return lines

    def _build_migration_summaries(
        self,
        report: RiskAssessmentReport,
    ) -> tuple[_RiskMigrationSummary, ...]:
        blocked_counts: dict[MigrationNodeKey, int] = {}
        destructive_counts: dict[MigrationNodeKey, int] = {}
        review_counts: dict[MigrationNodeKey, int] = {}
        highest_severity: dict[MigrationNodeKey, RiskSeverity] = {}

        for finding in report.findings:
            migration = finding.migration
            if finding.kind is RiskFindingKind.BLOCKED:
                blocked_counts[migration] = blocked_counts.get(migration, 0) + 1
            elif finding.kind is RiskFindingKind.DESTRUCTIVE:
                destructive_counts[migration] = destructive_counts.get(migration, 0) + 1
            else:
                review_counts[migration] = review_counts.get(migration, 0) + 1

            current = highest_severity.get(migration, RiskSeverity.NONE)
            if self._severity_rank(finding.severity) > self._severity_rank(current):
                highest_severity[migration] = finding.severity

        migrations = tuple(set(blocked_counts) | set(destructive_counts) | set(review_counts))
        summaries = tuple(
            _RiskMigrationSummary(
                migration=migration,
                highest_severity=highest_severity.get(migration, RiskSeverity.NONE),
                blocked_count=blocked_counts.get(migration, 0),
                destructive_count=destructive_counts.get(migration, 0),
                review_count=review_counts.get(migration, 0),
            )
            for migration in migrations
        )
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (
                    -summary.blocked_count,
                    -summary.destructive_count,
                    -summary.review_count,
                    -self._severity_rank(summary.highest_severity),
                    summary.migration.identifier,
                ),
            )
        )

    def _severity_rank(self, severity: RiskSeverity) -> int:
        return {
            RiskSeverity.NONE: 0,
            RiskSeverity.LOW: 1,
            RiskSeverity.MEDIUM: 2,
            RiskSeverity.HIGH: 3,
            RiskSeverity.CRITICAL: 4,
        }[severity]

    def _render_detailed_findings(self, report: RiskAssessmentReport) -> list[str]:
        lines = ["", "Detailed findings:"]
        if not report.findings:
            lines.append("  - none")
            return lines

        for finding in report.findings:
            lines.extend(
                [
                    (
                        "  - "
                        f"[{finding.kind.value.upper()}] {finding.migration.identifier} "
                        f"(op #{finding.operation_index}: {finding.operation_name})"
                    ),
                    f"    {finding.message}",
                    f"    Recommendation: {finding.recommendation}",
                ]
            )
        return lines

    def _render_next_step(self, report: RiskAssessmentReport) -> list[str]:
        command = (
            "python manage.py migration_inspect risk --details"
            if report.analysis_scope is RiskAnalysisScope.PENDING
            else "python manage.py migration_inspect audit --details"
        )
        if not report.findings:
            return []
        return ["", "Next step:", f"  - Run `{command}` for the full per-operation review."]
