"""Risk-rule protocol definitions."""

from __future__ import annotations

from typing import Protocol

from django_migration_inspector.domain.plans import PlannedMigrationStep
from django_migration_inspector.domain.reports import RiskFinding


class RiskRule(Protocol):
    """Protocol for one risk rule."""

    rule_id: str

    def evaluate(self, step: PlannedMigrationStep) -> tuple[RiskFinding, ...]:
        """Evaluate the step and return any matching risk findings."""
