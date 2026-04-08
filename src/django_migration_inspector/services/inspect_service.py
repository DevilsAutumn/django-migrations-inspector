"""Service layer for graph inspection flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from django_migration_inspector.analyzers import GraphIntelligenceAnalyzer
from django_migration_inspector.config import InspectConfig
from django_migration_inspector.django_adapter import DjangoMigrationGraphProvider
from django_migration_inspector.django_adapter.app_ignore import build_ignored_app_labels
from django_migration_inspector.domain.models import MigrationGraphSnapshot
from django_migration_inspector.domain.reports import GraphInspectionReport
from django_migration_inspector.exceptions import MigrationInspectionError


class MigrationGraphProvider(Protocol):
    """Protocol for graph snapshot providers."""

    def build_snapshot(self, database_alias: str) -> MigrationGraphSnapshot:
        """Build a graph snapshot for the requested database alias."""


@dataclass(slots=True)
class InspectService:
    """Coordinate graph providers and analyzers."""

    graph_provider: MigrationGraphProvider
    graph_analyzer: GraphIntelligenceAnalyzer

    def inspect_graph(self, config: InspectConfig) -> GraphInspectionReport:
        """Inspect the Django migration graph for the provided configuration."""

        if config.app_label is not None and config.app_label in build_ignored_app_labels():
            raise MigrationInspectionError(
                f"App {config.app_label!r} is ignored because it is not a user project app."
            )
        snapshot = self.graph_provider.build_snapshot(database_alias=config.database_alias)
        return self.graph_analyzer.analyze(
            snapshot,
            database_alias=config.database_alias,
            app_label=config.app_label,
        )


def build_default_inspect_service() -> InspectService:
    """Create the default service wiring for production usage."""

    return InspectService(
        graph_provider=DjangoMigrationGraphProvider(),
        graph_analyzer=GraphIntelligenceAnalyzer(),
    )
