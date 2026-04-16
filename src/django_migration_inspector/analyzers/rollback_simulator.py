"""Rollback simulation and blocker detection."""

from __future__ import annotations

from dataclasses import dataclass

from django_migration_inspector.domain.enums import RiskSeverity
from django_migration_inspector.domain.plans import (
    RollbackMigrationPlan,
    RollbackMigrationStep,
    RollbackOperationDescriptor,
)
from django_migration_inspector.domain.reports import (
    RollbackBlocker,
    RollbackConcern,
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


@dataclass(slots=True)
class RollbackSimulator:
    """Analyze rollback steps and summarize blockers and operational concerns."""

    def analyze(self, plan: RollbackMigrationPlan) -> RollbackSimulationReport:
        """Analyze the rollback plan and return a structured simulation report."""

        blockers = self._build_blockers(plan)
        concerns = self._build_concerns(plan)
        rollback_possible = not blockers
        high_or_worse_concern = any(
            _severity_rank(concern.severity) >= _severity_rank(RiskSeverity.HIGH)
            for concern in concerns
        )
        rollback_safe = rollback_possible and not high_or_worse_concern
        overall_severity = self._calculate_overall_severity(blockers=blockers, concerns=concerns)
        return RollbackSimulationReport(
            database_alias=plan.database_alias,
            overall_severity=overall_severity,
            rollback_possible=rollback_possible,
            rollback_safe=rollback_safe,
            blockers=blockers,
            concerns=concerns,
            plan=plan,
        )

    def _build_blockers(self, plan: RollbackMigrationPlan) -> tuple[RollbackBlocker, ...]:
        blockers: list[RollbackBlocker] = []
        for step in plan.steps:
            for operation in step.iter_reverse_operations():
                if operation.is_reversible:
                    continue
                blockers.append(
                    RollbackBlocker(
                        migration=step.key,
                        operation_index=operation.index,
                        operation_path=operation.path,
                        operation_name=operation.source_name,
                        message=(
                            "This reverse step is irreversible, so Django cannot execute a clean "
                            "rollback through this migration."
                        ),
                        recommendation=(
                            "Plan a manual recovery path or add an explicit reverse operation "
                            "before relying on rollback."
                        ),
                    )
                )
        return tuple(blockers)

    def _build_concerns(self, plan: RollbackMigrationPlan) -> tuple[RollbackConcern, ...]:
        concerns: list[RollbackConcern] = []
        seen_cross_apps: set[str] = set()

        for step in plan.steps:
            concerns.extend(self._build_step_concerns(step=step))

            if (
                step.key.app_label != plan.target_app_label
                and step.key.app_label not in seen_cross_apps
            ):
                seen_cross_apps.add(step.key.app_label)
                concerns.append(
                    RollbackConcern(
                        category="cross_app_impact",
                        severity=RiskSeverity.MEDIUM,
                        migration=step.key,
                        operation_index=None,
                        operation_path=None,
                        operation_name=None,
                        message=(
                            "Rolling back this target also affects migrations in another app "
                            "because of dependency relationships."
                        ),
                        recommendation=(
                            "Review deployment coordination and verify dependent app state before "
                            "attempting rollback."
                        ),
                    )
                )

            if step.is_merge:
                concerns.append(
                    RollbackConcern(
                        category="merge_topology",
                        severity=RiskSeverity.MEDIUM,
                        migration=step.key,
                        operation_index=None,
                        operation_path=None,
                        operation_name=None,
                        message=(
                            "This rollback path traverses a merge migration, which can make branch "
                            "history and recovery sequencing harder to reason about."
                        ),
                        recommendation=(
                            "Validate the full branch history and confirm which parent branches "
                            "must remain applied after rollback."
                        ),
                    )
                )

        return tuple(concerns)

    def _build_step_concerns(
        self,
        *,
        step: RollbackMigrationStep,
    ) -> list[RollbackConcern]:
        concerns: list[RollbackConcern] = []
        for operation in step.iter_reverse_operations():
            concern = self._build_operation_concern(step=step, operation=operation)
            if concern is not None:
                concerns.append(concern)
        return concerns

    def _build_operation_concern(
        self,
        *,
        step: RollbackMigrationStep,
        operation: RollbackOperationDescriptor,
    ) -> RollbackConcern | None:
        if operation.name == "RemoveField":
            return RollbackConcern(
                category="rollback_removes_field",
                severity=RiskSeverity.HIGH,
                migration=step.key,
                operation_index=operation.index,
                operation_path=operation.path,
                operation_name=operation.name,
                message=(
                    "Rollback will remove a field added by this migration. That is expected "
                    "during rollback, but it deletes any data stored in that column after the "
                    "migration was applied."
                ),
                recommendation=(
                    "Confirm the column data is disposable or backed up before executing this "
                    "rollback."
                ),
            )

        if operation.name == "DeleteModel":
            return RollbackConcern(
                category="rollback_drops_table",
                severity=RiskSeverity.HIGH,
                migration=step.key,
                operation_index=operation.index,
                operation_path=operation.path,
                operation_name=operation.name,
                message=(
                    "Rollback will drop a table created by this migration. That is expected "
                    "during rollback, but it deletes rows created after the migration was applied."
                ),
                recommendation=(
                    "Confirm the table data is disposable or backed up before executing this "
                    "rollback."
                ),
            )

        if operation.source_name == "RemoveField":
            return RollbackConcern(
                category="data_loss_reversal",
                severity=RiskSeverity.HIGH,
                migration=step.key,
                operation_index=operation.index,
                operation_path=operation.path,
                operation_name=operation.source_name,
                message=(
                    "Reversing a field removal restores schema shape but cannot recover the "
                    "dropped field data automatically."
                ),
                recommendation=(
                    "Confirm whether backups or a data restoration plan exist before using "
                    "rollback as a recovery strategy."
                ),
            )

        if operation.source_name == "DeleteModel":
            return RollbackConcern(
                category="table_restore",
                severity=RiskSeverity.HIGH,
                migration=step.key,
                operation_index=operation.index,
                operation_path=operation.path,
                operation_name=operation.source_name,
                message=(
                    "Reversing a model deletion can recreate the table structure but does not "
                    "restore deleted rows."
                ),
                recommendation=(
                    "Treat this rollback as schema-only unless you also have a data restoration "
                    "plan."
                ),
            )

        if operation.source_name == "RunPython":
            return RollbackConcern(
                category="reverse_data_migration",
                severity=RiskSeverity.MEDIUM,
                migration=step.key,
                operation_index=operation.index,
                operation_path=operation.path,
                operation_name=operation.source_name,
                message=(
                    "Rollback includes custom Python data logic, which may still be slow or "
                    "operationally risky even when technically reversible."
                ),
                recommendation=(
                    "Review data volume, query patterns, and runtime before executing the "
                    "rollback in a production environment."
                ),
            )

        if operation.source_name == "RunSQL":
            return RollbackConcern(
                category="reverse_sql",
                severity=RiskSeverity.HIGH,
                migration=step.key,
                operation_index=operation.index,
                operation_path=operation.path,
                operation_name=operation.source_name,
                message=(
                    "Rollback includes raw SQL, which may have backend-specific lock or "
                    "transaction behavior."
                ),
                recommendation=(
                    "Review the reverse SQL against the target database engine and test it in a "
                    "representative environment first."
                ),
            )

        return None

    def _calculate_overall_severity(
        self,
        *,
        blockers: tuple[RollbackBlocker, ...],
        concerns: tuple[RollbackConcern, ...],
    ) -> RiskSeverity:
        if blockers:
            return RiskSeverity.CRITICAL
        if not concerns:
            return RiskSeverity.NONE
        return max(concerns, key=lambda concern: _severity_rank(concern.severity)).severity
