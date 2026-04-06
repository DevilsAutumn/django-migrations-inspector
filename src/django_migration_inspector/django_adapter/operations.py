"""Normalization helpers for Django migration operations."""

from __future__ import annotations

from django.db.migrations.operations.base import Operation

from django_migration_inspector.domain.enums import OperationCategory
from django_migration_inspector.domain.models import OperationDescriptor

_SCHEMA_OPERATION_NAMES = frozenset(
    {
        "AddConstraint",
        "AddField",
        "AddIndex",
        "AlterField",
        "AlterIndexTogether",
        "AlterModelManagers",
        "AlterModelOptions",
        "AlterModelTable",
        "AlterModelTableComment",
        "AlterOrderWithRespectTo",
        "AlterUniqueTogether",
        "CreateModel",
        "DeleteModel",
        "RemoveConstraint",
        "RemoveField",
        "RemoveIndex",
        "RenameField",
        "RenameIndex",
        "RenameModel",
    }
)
_DATA_OPERATION_NAMES = frozenset({"RunPython"})
_RAW_SQL_OPERATION_NAMES = frozenset({"RunSQL"})
_STATE_OPERATION_NAMES = frozenset({"SeparateDatabaseAndState"})


def classify_operation(operation: Operation) -> OperationCategory:
    """Map a Django operation to a normalized category."""

    operation_name = type(operation).__name__
    if operation_name in _SCHEMA_OPERATION_NAMES:
        return OperationCategory.SCHEMA
    if operation_name in _DATA_OPERATION_NAMES:
        return OperationCategory.DATA
    if operation_name in _RAW_SQL_OPERATION_NAMES:
        return OperationCategory.RAW_SQL
    if operation_name in _STATE_OPERATION_NAMES:
        return OperationCategory.STATE
    return OperationCategory.UNKNOWN


def build_operation_descriptor(operation: Operation, index: int) -> OperationDescriptor:
    """Convert a Django operation object into a typed domain descriptor."""

    operation_type = type(operation)
    import_path = f"{operation_type.__module__}.{operation_type.__qualname__}"
    return OperationDescriptor(
        index=index,
        name=operation_type.__name__,
        import_path=import_path,
        category=classify_operation(operation),
        description=operation.describe(),
        is_reversible=bool(operation.reversible),
        is_elidable=bool(operation.elidable),
    )
