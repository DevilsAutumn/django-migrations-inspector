"""Service layer for rollback simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from django_migration_inspector.analyzers import RollbackSimulator
from django_migration_inspector.config import RollbackConfig
from django_migration_inspector.django_adapter.rollback import DjangoRollbackPlanProvider
from django_migration_inspector.domain.plans import RollbackMigrationPlan
from django_migration_inspector.domain.reports import RollbackSimulationReport


class RollbackPlanProvider(Protocol):
    """Protocol for rollback plan providers."""

    def build_plan(
        self,
        *,
        database_alias: str,
        target_app_label: str,
        target_migration_name: str,
    ) -> RollbackMigrationPlan:
        """Build a rollback plan for the requested target."""


@dataclass(slots=True)
class RollbackInspectionService:
    """Coordinate rollback plan loading and simulation."""

    plan_provider: RollbackPlanProvider
    rollback_simulator: RollbackSimulator

    def inspect_rollback(self, config: RollbackConfig) -> RollbackSimulationReport:
        """Simulate rollback for the requested target and return a structured report."""

        plan = self.plan_provider.build_plan(
            database_alias=config.database_alias,
            target_app_label=config.target_app_label,
            target_migration_name=config.target_migration_name,
        )
        return self.rollback_simulator.analyze(plan)


def build_default_rollback_service() -> RollbackInspectionService:
    """Create the default production rollback-inspection wiring."""

    return RollbackInspectionService(
        plan_provider=DjangoRollbackPlanProvider(),
        rollback_simulator=RollbackSimulator(),
    )
