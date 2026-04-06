"""Typed configuration objects for inspection commands."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import DEFAULT_DATABASE_ALIAS
from .domain.enums import OutputFormat


@dataclass(frozen=True, slots=True)
class InspectConfig:
    """Configuration for graph inspection requests."""

    output_format: OutputFormat = OutputFormat.TEXT
    database_alias: str = DEFAULT_DATABASE_ALIAS
    app_label: str | None = None

