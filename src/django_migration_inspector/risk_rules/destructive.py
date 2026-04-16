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
        for operation in step.iter_operations():
            if operation.name == "RemoveField":
                if operation.context == "state":
                    findings.append(
                        RiskFinding(
                            rule_id=self.rule_id,
                            kind=RiskFindingKind.REVIEW,
                            severity=RiskSeverity.MEDIUM,
                            migration=step.key,
                            operation_index=operation.index,
                            operation_path=operation.path,
                            operation_name=operation.name,
                            message=(
                                "A nested state operation removes a field from Django's migration "
                                "state. This does not drop data by itself, but it often pairs with "
                                "manual database changes that need review."
                            ),
                            recommendation=(
                                "Review the matching database operation and confirm the real "
                                "column change is safe and reversible."
                            ),
                        )
                    )
                    continue
                findings.append(
                    RiskFinding(
                        rule_id=self.rule_id,
                        kind=RiskFindingKind.DESTRUCTIVE,
                        severity=RiskSeverity.HIGH,
                        migration=step.key,
                        operation_index=operation.index,
                        operation_path=operation.path,
                        operation_name=operation.name,
                        message="Removing a field can drop stored data and complicate recovery.",
                        recommendation=(
                            "Review whether the field removal should be split into a safer staged "
                            "migration or guarded by a deprecation window."
                        ),
                    )
                )
            elif operation.name == "DeleteModel":
                if operation.context == "state":
                    findings.append(
                        RiskFinding(
                            rule_id=self.rule_id,
                            kind=RiskFindingKind.REVIEW,
                            severity=RiskSeverity.MEDIUM,
                            migration=step.key,
                            operation_index=operation.index,
                            operation_path=operation.path,
                            operation_name=operation.name,
                            message=(
                                "A nested state operation deletes a model from Django's migration "
                                "state. This does not drop the table by itself, but it often pairs "
                                "with manual database changes that need review."
                            ),
                            recommendation=(
                                "Review the matching database operation and confirm the real table "
                                "change is safe and reversible."
                            ),
                        )
                    )
                    continue
                findings.append(
                    RiskFinding(
                        rule_id=self.rule_id,
                        kind=RiskFindingKind.DESTRUCTIVE,
                        severity=RiskSeverity.HIGH,
                        migration=step.key,
                        operation_index=operation.index,
                        operation_path=operation.path,
                        operation_name=operation.name,
                        message="Deleting a model can remove an entire table and all stored rows.",
                        recommendation=(
                            "Validate data retention, backup strategy, and a phased removal plan "
                            "before deployment."
                        ),
                    )
                )
        return tuple(findings)
