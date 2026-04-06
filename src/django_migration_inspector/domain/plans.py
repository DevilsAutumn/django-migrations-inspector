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
