"""Service layer for risk inspection."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from django_migration_inspector.analyzers import RiskEngine
from django_migration_inspector.config import RiskConfig
from django_migration_inspector.django_adapter.planner import (
    DjangoForwardPlanProvider,
    DjangoHistoricalPlanProvider,
)
from django_migration_inspector.domain.enums import RiskAnalysisScope
from django_migration_inspector.domain.plans import ForwardMigrationPlan
from django_migration_inspector.domain.reports import RiskAssessmentReport


class ForwardPlanProvider(Protocol):
    """Protocol for forward migration plan providers."""

    def build_plan(
        self,
        *,
        database_alias: str,
        app_label: str | None = None,
        offline: bool = False,
    ) -> ForwardMigrationPlan:
        """Build a forward plan for the requested scope."""


@dataclass(slots=True)
class RiskInspectionService:
    """Coordinate risk-plan loading and analysis."""

    pending_plan_provider: ForwardPlanProvider
    historical_plan_provider: ForwardPlanProvider
    risk_engine: RiskEngine

    def inspect_risk(self, config: RiskConfig) -> RiskAssessmentReport:
        """Analyze the requested migration slice and return a risk report."""

        plan_provider = (
            self.pending_plan_provider
            if config.scope is RiskAnalysisScope.PENDING
            else self.historical_plan_provider
        )
        plan = plan_provider.build_plan(
            database_alias=config.database_alias,
            app_label=config.app_label,
            offline=config.offline,
        )
        report = self.risk_engine.analyze(plan)
        return replace(report, offline=config.offline)


def build_default_risk_service() -> RiskInspectionService:
    """Create the default production risk-inspection wiring."""

    return RiskInspectionService(
        pending_plan_provider=DjangoForwardPlanProvider(),
        historical_plan_provider=DjangoHistoricalPlanProvider(),
        risk_engine=RiskEngine(),
    )
