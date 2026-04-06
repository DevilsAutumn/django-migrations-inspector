"""Helpers for safely loading Django migration graphs."""

from __future__ import annotations

from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.migrations.loader import MigrationLoader

from django_migration_inspector.exceptions import MigrationInspectionError


def get_database_connection(database_alias: str) -> BaseDatabaseWrapper:
    """Return the configured Django database connection for the alias."""

    try:
        return connections[database_alias]
    except KeyError as error:
        raise MigrationInspectionError(
            f"Unknown database alias {database_alias!r}. Check your Django DATABASES setting."
        ) from error


def load_migration_loader(database_alias: str) -> MigrationLoader:
    """Load Django's migration graph and applied migration state."""

    connection = get_database_connection(database_alias)
    return MigrationLoader(connection=connection, ignore_no_migrations=True)
