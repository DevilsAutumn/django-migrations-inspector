"""Rules for unknown or custom migration operations."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.enums import OperationCategory, RiskSeverity
from django_migration_inspector.domain.plans import PlannedMigrationStep
from django_migration_inspector.domain.reports import RiskFinding


@dataclass(frozen=True, slots=True)
class UnknownOperationRule:
    """Flag custom or unknown operations that need manual review."""

    rule_id: str = "unknown_operation"

    def evaluate(self, step: PlannedMigrationStep) -> tuple[RiskFinding, ...]:
        findings: list[RiskFinding] = []
        for operation in step.operations:
            if operation.category is not OperationCategory.UNKNOWN:
                continue

            findings.append(
                RiskFinding(
                    rule_id=self.rule_id,
                    severity=RiskSeverity.MEDIUM,
                    migration=step.key,
                    operation_index=operation.index,
                    operation_name=operation.name,
                    message=(
                        "This operation is not yet classified by the toolkit and needs manual "
                        "review before relying on the automated risk summary."
                    ),
                    recommendation=(
                        "Inspect the custom operation implementation and add a dedicated rule if "
                        "it is used frequently."
                    ),
                )
            )
        return tuple(findings)
