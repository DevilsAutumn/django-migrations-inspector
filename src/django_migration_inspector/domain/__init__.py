"""Typed domain objects used by the toolkit."""

from .enums import OperationCategory, OutputFormat, RiskSeverity
from .keys import MigrationNodeKey
from .models import MigrationGraphSnapshot, MigrationNode, OperationDescriptor
from .plans import (
    ForwardMigrationPlan,
    PlannedMigrationStep,
    RollbackMigrationPlan,
    RollbackMigrationStep,
)
from .reports import (
    AppHeadGroup,
    DependencyHotspot,
    GraphInspectionReport,
    RiskAssessmentReport,
    RiskFinding,
    RollbackBlocker,
    RollbackConcern,
    RollbackSimulationReport,
)

__all__ = [
    "AppHeadGroup",
    "DependencyHotspot",
    "ForwardMigrationPlan",
    "GraphInspectionReport",
    "MigrationGraphSnapshot",
    "MigrationNode",
    "MigrationNodeKey",
    "OperationCategory",
    "OperationDescriptor",
    "OutputFormat",
    "PlannedMigrationStep",
    "RiskAssessmentReport",
    "RiskFinding",
    "RiskSeverity",
    "RollbackBlocker",
    "RollbackConcern",
    "RollbackMigrationPlan",
    "RollbackMigrationStep",
    "RollbackSimulationReport",
]
