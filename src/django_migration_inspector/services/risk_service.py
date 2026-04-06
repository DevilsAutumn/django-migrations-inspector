"""Service layer for forward-plan risk inspection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from django_migration_inspector.analyzers import RiskEngine
from django_migration_inspector.config import InspectConfig
from django_migration_inspector.django_adapter.planner import DjangoForwardPlanProvider
from django_migration_inspector.domain.plans import ForwardMigrationPlan
from django_migration_inspector.domain.reports import RiskAssessmentReport


class ForwardPlanProvider(Protocol):
    """Protocol for forward migration plan providers."""

    def build_plan(
        self,
        *,
        database_alias: str,
        app_label: str | None = None,
    ) -> ForwardMigrationPlan:
        """Build a forward plan for the requested scope."""


@dataclass(slots=True)
class RiskInspectionService:
    """Coordinate forward plan loading and risk analysis."""

    plan_provider: ForwardPlanProvider
    risk_engine: RiskEngine

    def inspect_risk(self, config: InspectConfig) -> RiskAssessmentReport:
        """Analyze the current forward plan and return a risk report."""

        plan = self.plan_provider.build_plan(
            database_alias=config.database_alias,
            app_label=config.app_label,
        )
        return self.risk_engine.analyze(plan)


def build_default_risk_service() -> RiskInspectionService:
    """Create the default production risk-inspection wiring."""

    return RiskInspectionService(
        plan_provider=DjangoForwardPlanProvider(),
        risk_engine=RiskEngine(),
    )
