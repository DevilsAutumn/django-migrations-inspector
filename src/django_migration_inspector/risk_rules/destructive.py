"""Rules for destructive schema operations."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.enums import RiskFindingKind, RiskSeverity
from django_migration_inspector.domain.plans import PlannedMigrationStep
from django_migration_inspector.domain.reports import RiskFinding


@dataclass(frozen=True, slots=True)
class DestructiveSchemaRule:
    """Flag potentially destructive schema operations."""

    rule_id: str = "destructive_schema_operation"

    def evaluate(self, step: PlannedMigrationStep) -> tuple[RiskFinding, ...]:
        findings: list[RiskFinding] = []
        for operation in step.operations:
            if operation.name == "RemoveField":
                findings.append(
                    RiskFinding(
                        rule_id=self.rule_id,
                        kind=RiskFindingKind.DESTRUCTIVE,
                        severity=RiskSeverity.HIGH,
                        migration=step.key,
                        operation_index=operation.index,
                        operation_name=operation.name,
                        message="Removing a field can drop stored data and complicate recovery.",
                        recommendation=(
                            "Review whether the field removal should be split into a safer staged "
                            "migration or guarded by a deprecation window."
                        ),
                    )
                )
            elif operation.name == "DeleteModel":
                findings.append(
                    RiskFinding(
                        rule_id=self.rule_id,
                        kind=RiskFindingKind.DESTRUCTIVE,
                        severity=RiskSeverity.HIGH,
                        migration=step.key,
                        operation_index=operation.index,
                        operation_name=operation.name,
                        message="Deleting a model can remove an entire table and all stored rows.",
                        recommendation=(
                            "Validate data retention, backup strategy, and a phased removal plan "
                            "before deployment."
                        ),
                    )
                )
        return tuple(findings)
