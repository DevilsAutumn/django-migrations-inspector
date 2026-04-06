"""Initial rule-driven risk analysis engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from django_migration_inspector.domain.enums import RiskSeverity
from django_migration_inspector.domain.plans import ForwardMigrationPlan
from django_migration_inspector.domain.reports import RiskAssessmentReport, RiskFinding
from django_migration_inspector.risk_rules import (
    DestructiveSchemaRule,
    IrreversibleRunPythonRule,
    RiskRule,
    RunSqlRule,
    UnknownOperationRule,
)


def _severity_rank(severity: RiskSeverity) -> int:
    return {
        RiskSeverity.NONE: 0,
        RiskSeverity.LOW: 1,
        RiskSeverity.MEDIUM: 2,
        RiskSeverity.HIGH: 3,
        RiskSeverity.CRITICAL: 4,
    }[severity]


def _default_rules() -> tuple[RiskRule, ...]:
    return (
        cast(RiskRule, DestructiveSchemaRule()),
        cast(RiskRule, IrreversibleRunPythonRule()),
        cast(RiskRule, RunSqlRule()),
        cast(RiskRule, UnknownOperationRule()),
    )


@dataclass(slots=True)
class RiskEngine:
    """Analyze a forward migration plan and summarize deployment risk."""

    rules: tuple[RiskRule, ...] = field(default_factory=_default_rules)

    def analyze(self, plan: ForwardMigrationPlan) -> RiskAssessmentReport:
        """Analyze the plan with all configured risk rules."""

        findings = tuple(
            finding
            for step in plan.steps
            for rule in self.rules
            for finding in rule.evaluate(step)
        )
        overall_severity = self._calculate_overall_severity(findings=findings)
        rollback_safe = all(
            operation.is_reversible
            for step in plan.steps
            for operation in step.operations
        )
        return RiskAssessmentReport(
            database_alias=plan.database_alias,
            selected_app_label=plan.selected_app_label,
            overall_severity=overall_severity,
            rollback_safe=rollback_safe,
            findings=findings,
            plan=plan,
        )

    def _calculate_overall_severity(self, *, findings: tuple[RiskFinding, ...]) -> RiskSeverity:
        if not findings:
            return RiskSeverity.NONE
        return max(findings, key=lambda finding: _severity_rank(finding.severity)).severity
