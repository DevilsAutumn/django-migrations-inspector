"""Rules for data migrations and raw SQL operations."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.enums import RiskFindingKind, RiskSeverity
from django_migration_inspector.domain.plans import PlannedMigrationStep
from django_migration_inspector.domain.reports import RiskFinding


@dataclass(frozen=True, slots=True)
class IrreversibleRunPythonRule:
    """Flag data migrations, especially irreversible ones."""

    rule_id: str = "runpython_operation"

    def evaluate(self, step: PlannedMigrationStep) -> tuple[RiskFinding, ...]:
        findings: list[RiskFinding] = []
        for operation in step.iter_operations():
            if operation.name != "RunPython":
                continue

            severity = RiskSeverity.HIGH if not operation.is_reversible else RiskSeverity.MEDIUM
            message = (
                "RunPython introduces custom data transformation logic that should be reviewed "
                "for runtime and rollback impact."
            )
            recommendation = (
                "Review data volume, execution time, and whether the migration should be broken "
                "into smaller deploy-safe steps."
            )
            if not operation.is_reversible:
                message = (
                    "RunPython is irreversible in this migration plan, which blocks a clean "
                    "database rollback."
                )
                recommendation = (
                    "Add a reverse callable or document a manual recovery procedure before using "
                    "this migration in production."
                )

            findings.append(
                RiskFinding(
                    rule_id=self.rule_id,
                    kind=(
                        RiskFindingKind.BLOCKED
                        if not operation.is_reversible
                        else RiskFindingKind.REVIEW
                    ),
                    severity=severity,
                    migration=step.key,
                    operation_index=operation.index,
                    operation_path=operation.path,
                    operation_name=operation.name,
                    message=message,
                    recommendation=recommendation,
                )
            )
        return tuple(findings)


@dataclass(frozen=True, slots=True)
class RunSqlRule:
    """Flag raw SQL operations that may carry backend-specific risk."""

    rule_id: str = "runsql_operation"

    def evaluate(self, step: PlannedMigrationStep) -> tuple[RiskFinding, ...]:
        findings: list[RiskFinding] = []
        for operation in step.iter_operations():
            if operation.name != "RunSQL":
                continue

            severity = RiskSeverity.HIGH if not operation.is_reversible else RiskSeverity.MEDIUM
            findings.append(
                RiskFinding(
                    rule_id=self.rule_id,
                    kind=(
                        RiskFindingKind.BLOCKED
                        if not operation.is_reversible
                        else RiskFindingKind.REVIEW
                    ),
                    severity=severity,
                    migration=step.key,
                    operation_index=operation.index,
                    operation_path=operation.path,
                    operation_name=operation.name,
                    message=(
                        "RunSQL bypasses Django's higher-level migration semantics and may have "
                        "backend-specific lock or rollback behavior."
                    ),
                    recommendation=(
                        "Review the SQL carefully against the target database engine and ensure "
                        "a reverse path or operational fallback is documented."
                    ),
                )
            )
        return tuple(findings)
