"""Typed forward and rollback migration plan models."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .enums import OperationCategory, RiskAnalysisScope
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
    dependencies: list[MigrationNodeKeyJSON]
    operation_count: int
    is_merge: bool
    has_irreversible_operation: bool
    reverse_operations: list[RollbackOperationDescriptorJSON]


class RollbackOperationDescriptorJSON(TypedDict):
    """Stable JSON shape for reverse operation descriptors."""

    index: int
    path: str
    context: str
    name: str
    source_name: str
    import_path: str
    category: str
    description: str
    source_description: str
    is_reversible: bool
    is_elidable: bool
    nested_operations: list[RollbackOperationDescriptorJSON]


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

        return sum(operation.operation_count for operation in self.operations)

    def iter_operations(self) -> Iterator[OperationDescriptor]:
        """Yield all operations in execution order, including nested operations."""

        for operation in self.operations:
            yield from operation.iter_self_and_nested()

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
    scope: RiskAnalysisScope
    target_leaf_nodes: tuple[MigrationNodeKey, ...]
    steps: tuple[PlannedMigrationStep, ...]


@dataclass(frozen=True, slots=True)
class RollbackMigrationStep:
    """A migration step in the reverse execution plan."""

    key: MigrationNodeKey
    module: str
    file_path: Path | None
    dependencies: tuple[MigrationNodeKey, ...]
    is_merge: bool
    reverse_operations: tuple[RollbackOperationDescriptor, ...]

    @property
    def operation_count(self) -> int:
        """Return the number of reverse operations in the step."""

        return sum(operation.operation_count for operation in self.reverse_operations)

    @property
    def has_irreversible_operation(self) -> bool:
        """Return whether the reverse step contains an irreversible operation."""

        return any(not operation.is_reversible for operation in self.iter_reverse_operations())

    def iter_reverse_operations(self) -> Iterator[RollbackOperationDescriptor]:
        """Yield all reverse operations, including nested operations."""

        for operation in self.reverse_operations:
            yield from operation.iter_self_and_nested()

    def to_json_dict(self) -> RollbackMigrationStepJSON:
        """Serialize the rollback step into the stable JSON contract."""

        return {
            "key": self.key.to_json_dict(),
            "module": self.module,
            "file_path": None if self.file_path is None else str(self.file_path),
            "dependencies": [dependency.to_json_dict() for dependency in self.dependencies],
            "operation_count": self.operation_count,
            "is_merge": self.is_merge,
            "has_irreversible_operation": self.has_irreversible_operation,
            "reverse_operations": [
                operation.to_json_dict() for operation in self.reverse_operations
            ],
        }


@dataclass(frozen=True, slots=True)
class RollbackOperationDescriptor:
    """Normalized description of one reverse migration operation."""

    index: int
    path: str
    context: str
    name: str
    source_name: str
    import_path: str
    category: OperationCategory
    description: str
    source_description: str
    is_reversible: bool
    is_elidable: bool
    nested_operations: tuple[RollbackOperationDescriptor, ...] = ()

    @property
    def operation_count(self) -> int:
        """Return this reverse operation plus any nested reverse operations."""

        return 1 + sum(operation.operation_count for operation in self.nested_operations)

    def iter_self_and_nested(self) -> Iterator[RollbackOperationDescriptor]:
        """Yield this reverse operation and recursively yield nested operations."""

        yield self
        for operation in self.nested_operations:
            yield from operation.iter_self_and_nested()

    def to_json_dict(self) -> RollbackOperationDescriptorJSON:
        """Serialize the reverse operation into the rollback JSON contract."""

        return {
            "index": self.index,
            "path": self.path,
            "context": self.context,
            "name": self.name,
            "source_name": self.source_name,
            "import_path": self.import_path,
            "category": self.category.value,
            "description": self.description,
            "source_description": self.source_description,
            "is_reversible": self.is_reversible,
            "is_elidable": self.is_elidable,
            "nested_operations": [operation.to_json_dict() for operation in self.nested_operations],
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
