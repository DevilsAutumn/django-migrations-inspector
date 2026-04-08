"""Renderer protocols for stable report output."""

from __future__ import annotations

from typing import Protocol

from django_migration_inspector.domain.reports import (
    GraphInspectionReport,
    RiskAssessmentReport,
    RollbackSimulationReport,
)


class GraphReportRenderer(Protocol):
    """Protocol for graph report renderers."""

    def render(self, report: GraphInspectionReport) -> str:
        """Render the provided report into a stable string representation."""


class RiskReportRenderer(Protocol):
    """Protocol for risk report renderers."""

    def render(self, report: RiskAssessmentReport) -> str:
        """Render the provided risk report into a stable string representation."""


class RollbackReportRenderer(Protocol):
    """Protocol for rollback report renderers."""

    def render(self, report: RollbackSimulationReport) -> str:
        """Render the provided rollback report into a stable string representation."""
