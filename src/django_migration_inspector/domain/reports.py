"""Report objects emitted by analyzers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from django_migration_inspector.constants import REPORT_SCHEMA_VERSION

from .enums import RiskSeverity
from .keys import MigrationNodeKey, MigrationNodeKeyJSON
from .models import MigrationNode, MigrationNodeJSON
from .plans import ForwardMigrationPlan, PlannedMigrationStepJSON


class AppHeadGroupJSON(TypedDict):
    """Stable JSON shape for multiple-head app groups."""

    app_label: str
    heads: list[MigrationNodeKeyJSON]


class DependencyHotspotJSON(TypedDict):
    """Stable JSON shape for dependency hotspots."""

    node: MigrationNodeKeyJSON
    dependency_count: int
    dependent_count: int


class GraphInspectionReportJSON(TypedDict):
    """Stable JSON shape for graph inspection reports."""

    schema_version: str
    report_type: str
    database_alias: str
    selected_app_label: str | None
    total_apps: int
    total_migrations: int
    root_nodes: list[MigrationNodeKeyJSON]
    leaf_nodes: list[MigrationNodeKeyJSON]
    merge_nodes: list[MigrationNodeKeyJSON]
    multiple_head_apps: list[AppHeadGroupJSON]
    dependency_hotspots: list[DependencyHotspotJSON]
    nodes: list[MigrationNodeJSON]


class RiskFindingJSON(TypedDict):
    """Stable JSON shape for risk findings."""

    rule_id: str
    severity: str
    migration: MigrationNodeKeyJSON
    operation_index: int
    operation_name: str
    message: str
    recommendation: str


class RiskAssessmentReportJSON(TypedDict):
    """Stable JSON shape for risk assessment reports."""

    schema_version: str
    report_type: str
    database_alias: str
    selected_app_label: str | None
    pending_migration_count: int
    pending_operation_count: int
    target_leaf_nodes: list[MigrationNodeKeyJSON]
    overall_severity: str
    rollback_safe: bool
    findings: list[RiskFindingJSON]
    planned_steps: list[PlannedMigrationStepJSON]


@dataclass(frozen=True, slots=True)
class AppHeadGroup:
    """A group of leaf migrations for one app with multiple heads."""

    app_label: str
    heads: tuple[MigrationNodeKey, ...]

    def to_json_dict(self) -> AppHeadGroupJSON:
        """Serialize the group into the report JSON contract."""

        return {
            "app_label": self.app_label,
            "heads": [head.to_json_dict() for head in self.heads],
        }


@dataclass(frozen=True, slots=True)
class DependencyHotspot:
    """A node with many dependents in the visible graph."""

    node: MigrationNodeKey
    dependency_count: int
    dependent_count: int

    def to_json_dict(self) -> DependencyHotspotJSON:
        """Serialize the hotspot into the report JSON contract."""

        return {
            "node": self.node.to_json_dict(),
            "dependency_count": self.dependency_count,
            "dependent_count": self.dependent_count,
        }


@dataclass(frozen=True, slots=True)
class GraphInspectionReport:
    """Output of the graph intelligence analyzer."""

    database_alias: str
    selected_app_label: str | None
    total_apps: int
    total_migrations: int
    root_nodes: tuple[MigrationNodeKey, ...]
    leaf_nodes: tuple[MigrationNodeKey, ...]
    merge_nodes: tuple[MigrationNodeKey, ...]
    multiple_head_apps: tuple[AppHeadGroup, ...]
    dependency_hotspots: tuple[DependencyHotspot, ...]
    nodes: tuple[MigrationNode, ...]

    def to_json_dict(self) -> GraphInspectionReportJSON:
        """Serialize the report into the stable JSON contract."""

        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "report_type": "graph_inspection",
            "database_alias": self.database_alias,
            "selected_app_label": self.selected_app_label,
            "total_apps": self.total_apps,
            "total_migrations": self.total_migrations,
            "root_nodes": [root_node.to_json_dict() for root_node in self.root_nodes],
            "leaf_nodes": [leaf_node.to_json_dict() for leaf_node in self.leaf_nodes],
            "merge_nodes": [merge_node.to_json_dict() for merge_node in self.merge_nodes],
            "multiple_head_apps": [
                app_head_group.to_json_dict() for app_head_group in self.multiple_head_apps
            ],
            "dependency_hotspots": [
                dependency_hotspot.to_json_dict()
                for dependency_hotspot in self.dependency_hotspots
            ],
            "nodes": [node.to_json_dict() for node in self.nodes],
        }


@dataclass(frozen=True, slots=True)
class RiskFinding:
    """One rule-triggered risk finding."""

    rule_id: str
    severity: RiskSeverity
    migration: MigrationNodeKey
    operation_index: int
    operation_name: str
    message: str
    recommendation: str

    def to_json_dict(self) -> RiskFindingJSON:
        """Serialize the finding into the stable JSON contract."""

        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "migration": self.migration.to_json_dict(),
            "operation_index": self.operation_index,
            "operation_name": self.operation_name,
            "message": self.message,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True, slots=True)
class RiskAssessmentReport:
    """Output of the initial risk analysis engine."""

    database_alias: str
    selected_app_label: str | None
    overall_severity: RiskSeverity
    rollback_safe: bool
    findings: tuple[RiskFinding, ...]
    plan: ForwardMigrationPlan

    @property
    def pending_migration_count(self) -> int:
        """Return the number of pending migration steps."""

        return len(self.plan.steps)

    @property
    def pending_operation_count(self) -> int:
        """Return the number of pending operations across the forward plan."""

        return sum(step.operation_count for step in self.plan.steps)

    def to_json_dict(self) -> RiskAssessmentReportJSON:
        """Serialize the report into the stable JSON contract."""

        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "report_type": "risk_assessment",
            "database_alias": self.database_alias,
            "selected_app_label": self.selected_app_label,
            "pending_migration_count": self.pending_migration_count,
            "pending_operation_count": self.pending_operation_count,
            "target_leaf_nodes": [
                target_leaf_node.to_json_dict() for target_leaf_node in self.plan.target_leaf_nodes
            ],
            "overall_severity": self.overall_severity.value,
            "rollback_safe": self.rollback_safe,
            "findings": [finding.to_json_dict() for finding in self.findings],
            "planned_steps": [step.to_json_dict() for step in self.plan.steps],
        }
