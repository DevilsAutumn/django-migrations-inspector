"""Plain-text renderer for risk assessment reports."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.reports import RiskAssessmentReport


@dataclass(slots=True)
class TextRiskReportRenderer:
    """Render risk reports for local CLI usage."""

    def render(self, report: RiskAssessmentReport) -> str:
        """Render the risk report into plain text."""

        lines = [
            "Django Migration Inspector Risk Report",
            "======================================",
            f"Database alias: {report.database_alias}",
            f"Scope: {report.selected_app_label or 'all apps'}",
            f"Pending migrations: {report.pending_migration_count}",
            f"Pending operations: {report.pending_operation_count}",
            f"Overall risk: {report.overall_severity.value.upper()}",
            f"Rollback safe: {'YES' if report.rollback_safe else 'NO'}",
            "",
            "Target leaf migrations:",
        ]

        if report.plan.target_leaf_nodes:
            lines.extend(f"  - {target.identifier}" for target in report.plan.target_leaf_nodes)
        else:
            lines.append("  - none")

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
