"""Normalization helpers for Django migration operations."""

from __future__ import annotations

from django.db.migrations.operations.base import Operation

from django_migration_inspector.domain.enums import OperationCategory
from django_migration_inspector.domain.models import OperationDescriptor
from django_migration_inspector.domain.plans import RollbackOperationDescriptor

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


def build_rollback_operation_descriptor(
    operation: Operation,
    index: int,
) -> RollbackOperationDescriptor:
    """Convert a Django operation into a reverse-step descriptor."""

    operation_type = type(operation)
    import_path = f"{operation_type.__module__}.{operation_type.__qualname__}"
    reverse_name, reverse_description = describe_reverse_operation(operation)
    return RollbackOperationDescriptor(
        index=index,
        name=reverse_name,
        source_name=operation_type.__name__,
        import_path=import_path,
        category=classify_operation(operation),
        description=reverse_description,
        source_description=operation.describe(),
        is_reversible=bool(operation.reversible),
        is_elidable=bool(operation.elidable),
    )


def describe_reverse_operation(operation: Operation) -> tuple[str, str]:
    """Return a human-readable reverse action for the provided operation."""

    operation_name = type(operation).__name__
    model_name = _string_attr(operation, "model_name")
    field_name = _string_attr(operation, "name")

    if operation_name == "AddField":
        return "RemoveField", f"Remove field {field_name} from {model_name}"
    if operation_name == "RemoveField":
        return "AddField", f"Add field {field_name} to {model_name}"
    if operation_name == "CreateModel":
        return "DeleteModel", f"Delete model {_string_attr(operation, 'name')}"
    if operation_name == "DeleteModel":
        return "CreateModel", f"Create model {_string_attr(operation, 'name')}"
    if operation_name == "AddIndex":
        return "RemoveIndex", _build_remove_index_description(operation)
    if operation_name == "RemoveIndex":
        return "AddIndex", _build_add_index_description(operation)
    if operation_name == "AddConstraint":
        return "RemoveConstraint", _build_remove_constraint_description(operation)
    if operation_name == "RemoveConstraint":
        return "AddConstraint", _build_add_constraint_description(operation)
    if operation_name == "AlterField":
        return "AlterField", f"Revert field {field_name} on {model_name} to its previous definition"
    if operation_name == "RenameField":
        old_name = _string_attr(operation, "old_name")
        new_name = _string_attr(operation, "new_name")
        return "RenameField", f"Rename field {new_name} on {model_name} back to {old_name}"
    if operation_name == "RenameModel":
        old_name = _string_attr(operation, "old_name")
        new_name = _string_attr(operation, "new_name")
        return "RenameModel", f"Rename model {new_name} back to {old_name}"
    if operation_name == "RenameIndex":
        old_name = _string_attr(operation, "old_name")
        new_name = _string_attr(operation, "new_name")
        return "RenameIndex", f"Rename index {new_name} on {model_name} back to {old_name}"
    if operation_name == "RunPython":
        return "RunPython", "Run reverse Python data migration logic"
    if operation_name == "RunSQL":
        return "RunSQL", "Run reverse SQL statements"
    if operation_name == "SeparateDatabaseAndState":
        return "SeparateDatabaseAndState", "Reverse separate database and state changes"
    return operation_name, f"Reverse operation: {operation.describe()}"


def _string_attr(operation: Operation, attribute_name: str) -> str:
    value = getattr(operation, attribute_name, attribute_name)
    return str(value)


def _build_remove_index_description(operation: Operation) -> str:
    index_name = getattr(getattr(operation, "index", None), "name", None)
    if index_name is None:
        index_name = getattr(operation, "name", None)
    if index_name is None:
        index_name = "index"
    return f"Remove index {index_name} from {_string_attr(operation, 'model_name')}"


def _build_add_index_description(operation: Operation) -> str:
    index_name = getattr(operation, "name", None)
    if index_name is None:
        index_name = getattr(getattr(operation, "index", None), "name", None)
    if index_name is None:
        index_name = "index"
    return f"Create index {index_name} on {_string_attr(operation, 'model_name')}"


def _build_remove_constraint_description(operation: Operation) -> str:
    constraint_name = getattr(getattr(operation, "constraint", None), "name", None)
    if constraint_name is None:
        constraint_name = getattr(operation, "name", None)
    if constraint_name is None:
        constraint_name = "constraint"
    return f"Remove constraint {constraint_name} from {_string_attr(operation, 'model_name')}"


def _build_add_constraint_description(operation: Operation) -> str:
    constraint_name = getattr(operation, "name", None)
    if constraint_name is None:
        constraint_name = getattr(getattr(operation, "constraint", None), "name", None)
    if constraint_name is None:
        constraint_name = "constraint"
    return f"Create constraint {constraint_name} on {_string_attr(operation, 'model_name')}"
