"""Core immutable graph models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .enums import OperationCategory
from .keys import MigrationNodeKey, MigrationNodeKeyJSON


class OperationDescriptorJSON(TypedDict):
    """Stable JSON shape for operation descriptors."""

    index: int
    name: str
    import_path: str
    category: str
    description: str
    is_reversible: bool
    is_elidable: bool


class MigrationNodeJSON(TypedDict):
    """Stable JSON shape for migration nodes."""

    key: MigrationNodeKeyJSON
    dependencies: list[MigrationNodeKeyJSON]
    dependents: list[MigrationNodeKeyJSON]
    replaces: list[MigrationNodeKeyJSON]
    operations: list[OperationDescriptorJSON]
    is_initial: bool
    is_merge: bool
    module: str
    file_path: str | None
    dependency_count: int
    dependent_count: int


@dataclass(frozen=True, slots=True)
class OperationDescriptor:
    """Normalized description of one migration operation."""

    index: int
    name: str
    import_path: str
    category: OperationCategory
    description: str
    is_reversible: bool
    is_elidable: bool

    def to_json_dict(self) -> OperationDescriptorJSON:
        """Serialize the operation into the report JSON contract."""

        return {
            "index": self.index,
            "name": self.name,
            "import_path": self.import_path,
            "category": self.category.value,
            "description": self.description,
            "is_reversible": self.is_reversible,
            "is_elidable": self.is_elidable,
        }


@dataclass(frozen=True, slots=True)
class MigrationNode:
    """Immutable representation of one migration node in the graph."""

    key: MigrationNodeKey
    dependencies: tuple[MigrationNodeKey, ...]
    dependents: tuple[MigrationNodeKey, ...]
    replaces: tuple[MigrationNodeKey, ...]
    operations: tuple[OperationDescriptor, ...]
    is_initial: bool
    module: str
    file_path: Path | None

    @property
    def is_merge(self) -> bool:
        """Return whether the migration merges multiple parents."""

        return len(self.dependencies) > 1

    @property
    def dependency_count(self) -> int:
        """Return the number of parent dependencies."""

        return len(self.dependencies)

    @property
    def dependent_count(self) -> int:
        """Return the number of child dependents."""

        return len(self.dependents)

    def to_json_dict(self) -> MigrationNodeJSON:
        """Serialize the node into the report JSON contract."""

        return {
            "key": self.key.to_json_dict(),
            "dependencies": [dependency.to_json_dict() for dependency in self.dependencies],
            "dependents": [dependent.to_json_dict() for dependent in self.dependents],
            "replaces": [replacement.to_json_dict() for replacement in self.replaces],
            "operations": [operation.to_json_dict() for operation in self.operations],
            "is_initial": self.is_initial,
            "is_merge": self.is_merge,
            "module": self.module,
            "file_path": None if self.file_path is None else str(self.file_path),
            "dependency_count": self.dependency_count,
            "dependent_count": self.dependent_count,
        }


@dataclass(frozen=True, slots=True)
class MigrationGraphSnapshot:
    """Normalized immutable snapshot of a Django migration graph."""

    nodes: tuple[MigrationNode, ...]
    app_labels: tuple[str, ...]
    root_nodes: tuple[MigrationNodeKey, ...]
    leaf_nodes: tuple[MigrationNodeKey, ...]
