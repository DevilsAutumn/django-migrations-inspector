"""Enum types for the package domain model."""

from __future__ import annotations

from enum import Enum


class OutputFormat(str, Enum):
    """Supported render output formats."""

    TEXT = "text"
    JSON = "json"
    MERMAID = "mermaid"
    DOT = "dot"


class OperationCategory(str, Enum):
    """Normalized migration operation categories."""

    SCHEMA = "schema"
    DATA = "data"
    RAW_SQL = "raw_sql"
    STATE = "state"
    UNKNOWN = "unknown"
