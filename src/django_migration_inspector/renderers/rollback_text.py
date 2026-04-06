"""Plain-text renderer for rollback simulation reports."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.reports import RollbackSimulationReport


@dataclass(slots=True)
class TextRollbackReportRenderer:
    """Render rollback simulation reports for local CLI usage."""

    def render(self, report: RollbackSimulationReport) -> str:
        """Render the rollback report into plain text."""

        lines = [
            "Django Migration Inspector Rollback Simulation",
            "==============================================",
            f"Database alias: {report.database_alias}",
            f"Target: {report.plan.target_identifier}",
            f"Planned rollback steps: {report.step_count}",
            (
                "Affected apps: "
                + (
                    ", ".join(report.plan.affected_app_labels)
                    if report.plan.affected_app_labels
                    else "none"
                )
            ),
            f"Overall severity: {report.overall_severity.value.upper()}",
            f"Rollback possible: {'YES' if report.rollback_possible else 'NO'}",
            f"Rollback safe: {'YES' if report.rollback_safe else 'NO'}",
            "",
            "Rollback steps:",
        ]

        if not report.plan.steps:
            lines.append("  - none")
        else:
            for step in report.plan.steps:
                step_suffix = " [merge]" if step.is_merge else ""
                lines.append(f"  - {step.key.identifier}{step_suffix}")
                if not step.reverse_operations:
                    lines.append("    - no operations")
                else:
                    for operation in step.reverse_operations:
                        marker = "BLOCKER" if not operation.is_reversible else "op"
                        lines.append(
                            "    - "
                            f"[{marker}] #{operation.index} "
                            f"{operation.name}: {operation.description}"
                        )

        lines.extend(["", "Blockers:"])
        if not report.blockers:
            lines.append("  - none")
        else:
            for blocker in report.blockers:
                lines.extend(
                    [
                        (
                            "  - "
                            f"{blocker.migration.identifier} "
                            f"(op #{blocker.operation_index}: {blocker.operation_name})"
                        ),
                        f"    {blocker.message}",
                        f"    Recommendation: {blocker.recommendation}",
                    ]
                )

        lines.extend(["", "Concerns:"])
        if not report.concerns:
            lines.append("  - none")
        else:
            for concern in report.concerns:
                operation_label = (
                    f" (op #{concern.operation_index}: {concern.operation_name})"
                    if concern.operation_index is not None and concern.operation_name is not None
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

        return "\n".join(lines) + "\n"
