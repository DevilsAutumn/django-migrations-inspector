"""Typed forward migration plan models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .keys import MigrationNodeKey, MigrationNodeKeyJSON
from .models import OperationDescriptor, OperationDescriptorJSON


class PlannedMigrationStepJSON(TypedDict):
    """Stable JSON shape for forward plan steps."""

    key: MigrationNodeKeyJSON
    module: str
    file_path: str | None
    operation_count: int
    operations: list[OperationDescriptorJSON]


class RollbackMigrationStepJSON(TypedDict):
    """Stable JSON shape for rollback plan steps."""

    key: MigrationNodeKeyJSON
    module: str
    file_path: str | None
    operation_count: int
    is_merge: bool
    has_irreversible_operation: bool
    reverse_operations: list[OperationDescriptorJSON]


@dataclass(frozen=True, slots=True)
class PlannedMigrationStep:
    """A migration step in the forward execution plan."""

    key: MigrationNodeKey
    module: str
    file_path: Path | None
    operations: tuple[OperationDescriptor, ...]

    @property
    def operation_count(self) -> int:
        """Return the number of operations in the step."""

        return len(self.operations)

    def to_json_dict(self) -> PlannedMigrationStepJSON:
        """Serialize the step into the stable JSON contract."""

        return {
            "key": self.key.to_json_dict(),
            "module": self.module,
            "file_path": None if self.file_path is None else str(self.file_path),
            "operation_count": self.operation_count,
            "operations": [operation.to_json_dict() for operation in self.operations],
        }


@dataclass(frozen=True, slots=True)
class ForwardMigrationPlan:
    """The normalized forward migration plan for the current database state."""

    database_alias: str
    selected_app_label: str | None
    target_leaf_nodes: tuple[MigrationNodeKey, ...]
    steps: tuple[PlannedMigrationStep, ...]


@dataclass(frozen=True, slots=True)
class RollbackMigrationStep:
    """A migration step in the reverse execution plan."""

    key: MigrationNodeKey
    module: str
    file_path: Path | None
    is_merge: bool
    reverse_operations: tuple[OperationDescriptor, ...]

    @property
    def operation_count(self) -> int:
        """Return the number of reverse operations in the step."""

        return len(self.reverse_operations)

    @property
    def has_irreversible_operation(self) -> bool:
        """Return whether the reverse step contains an irreversible operation."""

        return any(not operation.is_reversible for operation in self.reverse_operations)

    def to_json_dict(self) -> RollbackMigrationStepJSON:
        """Serialize the rollback step into the stable JSON contract."""

        return {
            "key": self.key.to_json_dict(),
            "module": self.module,
            "file_path": None if self.file_path is None else str(self.file_path),
            "operation_count": self.operation_count,
            "is_merge": self.is_merge,
            "has_irreversible_operation": self.has_irreversible_operation,
            "reverse_operations": [
                operation.to_json_dict() for operation in self.reverse_operations
            ],
        }


@dataclass(frozen=True, slots=True)
class RollbackMigrationPlan:
    """The normalized rollback plan for a requested target migration."""

    database_alias: str
    target_app_label: str
    target_migration_name: str | None
    steps: tuple[RollbackMigrationStep, ...]

    @property
    def target_identifier(self) -> str:
        """Return a human-readable rollback target identifier."""

        target_migration_name = self.target_migration_name or "zero"
        return f"{self.target_app_label}.{target_migration_name}"

    @property
    def affected_app_labels(self) -> tuple[str, ...]:
        """Return the app labels touched by the rollback plan."""

        return tuple(sorted({step.key.app_label for step in self.steps}))
