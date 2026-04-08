"""Enum types for the package domain model."""

from __future__ import annotations

from enum import Enum


class OutputFormat(str, Enum):
    """Supported render output formats."""

    TEXT = "text"
    JSON = "json"
    MERMAID = "mermaid"
    DOT = "dot"


class RiskSeverity(str, Enum):
    """Supported migration risk severities."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFindingKind(str, Enum):
    """User-facing classes of migration findings."""

    BLOCKED = "blocked"
    DESTRUCTIVE = "destructive"
    REVIEW = "review"


class RiskDecision(str, Enum):
    """High-level decision states for forward migration review."""

    CLEAR = "clear"
    REVIEW_REQUIRED = "review_required"
    ROLLBACK_BLOCKED = "rollback_blocked"


class RiskAnalysisScope(str, Enum):
    """Supported scopes for risk analysis."""

    PENDING = "pending"
    HISTORY = "history"


class OperationCategory(str, Enum):
    """Normalized migration operation categories."""

    SCHEMA = "schema"
    DATA = "data"
    RAW_SQL = "raw_sql"
    STATE = "state"
    UNKNOWN = "unknown"
