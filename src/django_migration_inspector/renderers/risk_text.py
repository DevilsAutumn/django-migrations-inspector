"""Plain-text renderer for risk assessment reports."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.enums import RiskAnalysisScope
from django_migration_inspector.domain.reports import RiskAssessmentReport


@dataclass(slots=True)
class TextRiskReportRenderer:
    """Render risk reports for local CLI usage."""

    def render(self, report: RiskAssessmentReport) -> str:
        """Render the risk report into plain text."""

        is_pending_scope = report.analysis_scope is RiskAnalysisScope.PENDING
        lines = [
            "Django Migration Inspector Risk Report",
            "======================================",
            f"Database alias: {report.database_alias}",
            f"Scope: {report.selected_app_label or 'all apps'}",
            f"Analysis scope: {report.analysis_scope.value}",
            f"Affected apps: {', '.join(report.affected_app_labels) or 'none'}",
            (
                f"Pending migrations: {report.pending_migration_count}"
                if is_pending_scope
                else f"Analyzed migrations: {report.analyzed_migration_count}"
            ),
            (
                f"Pending operations: {report.pending_operation_count}"
                if is_pending_scope
                else f"Analyzed operations: {report.analyzed_operation_count}"
            ),
            f"Overall risk: {report.overall_severity.value.upper()}",
            f"Rollback safe: {'YES' if report.rollback_safe else 'NO'}",
            "",
            ("Target leaf migrations:" if is_pending_scope else "Visible leaf migrations:"),
        ]

        if report.plan.target_leaf_nodes:
            lines.extend(f"  - {target.identifier}" for target in report.plan.target_leaf_nodes)
        else:
            lines.append("  - none")

        if is_pending_scope and report.pending_migration_count == 0:
            lines.extend(
                [
                    "",
                    "Note:",
                    "  - No pending migrations found in the selected scope.",
                    "  - Use --risk-history to audit migration files already on disk.",
                ]
            )

        lines.extend(["", "Findings:"])
        if not report.findings:
            lines.append("  - none")
        else:
            for finding in report.findings:
                lines.extend(
                    [
                        (
                            "  - "
                            f"[{finding.severity.value.upper()}] "
                            f"{finding.migration.identifier} "
                            f"(op #{finding.operation_index}: {finding.operation_name})"
                        ),
                        f"    {finding.message}",
                        f"    Recommendation: {finding.recommendation}",
                    ]
                )

        return "\n".join(lines) + "\n"
