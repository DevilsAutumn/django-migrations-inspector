"""Typed configuration objects for inspection commands."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import DEFAULT_DATABASE_ALIAS
from .domain.enums import OutputFormat, RiskAnalysisScope


@dataclass(frozen=True, slots=True)
class InspectConfig:
    """Configuration for graph inspection requests."""

    output_format: OutputFormat = OutputFormat.TEXT
    database_alias: str = DEFAULT_DATABASE_ALIAS
    app_label: str | None = None


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Configuration for risk inspection requests."""

    output_format: OutputFormat = OutputFormat.TEXT
    database_alias: str = DEFAULT_DATABASE_ALIAS
    app_label: str | None = None
    scope: RiskAnalysisScope = RiskAnalysisScope.PENDING


@dataclass(frozen=True, slots=True)
class RollbackConfig:
    """Configuration for rollback simulation requests."""

    output_format: OutputFormat = OutputFormat.TEXT
    database_alias: str = DEFAULT_DATABASE_ALIAS
    target_app_label: str = ""
    target_migration_name: str = ""
