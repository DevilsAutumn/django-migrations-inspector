"""Helpers for safely loading Django migration graphs."""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from django.conf import settings
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.migrations.loader import MigrationLoader
from django.db.utils import OperationalError

from django_migration_inspector.exceptions import MigrationInspectionError


def _load_dotenv_values(project_root: Path) -> dict[str, str]:
    try:
        dotenv_module = import_module("dotenv")
    except ImportError:
        return {}

    env_path = project_root / ".env"
    if not env_path.is_file():
        return {}

    dotenv_values = getattr(dotenv_module, "dotenv_values", None)
    if not callable(dotenv_values):
        return {}

    return {
        key: value for key, value in dotenv_values(env_path).items() if key and value is not None
    }


def _database_url_overrides(env_values: Mapping[str, str]) -> dict[str, str]:
    database_url = env_values.get("DATABASE_URL", "").strip()
    if not database_url:
        return {}

    parsed = urlparse(database_url)
    if parsed.scheme.lower() not in {"postgres", "postgresql", "pgsql"}:
        return {}

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    host = query.get("host") or parsed.hostname
    port = query.get("port") or (str(parsed.port) if parsed.port is not None else "")

    overrides = {
        "NAME": parsed.path.lstrip("/"),
        "USER": unquote(parsed.username) if parsed.username else "",
        "PASSWORD": unquote(parsed.password) if parsed.password else "",
        "HOST": host or "",
        "PORT": port,
    }
    return {key: value for key, value in overrides.items() if value}


def _legacy_env_overrides(env_values: Mapping[str, str]) -> dict[str, str]:
    def _first_non_empty(*keys: str) -> str:
        for key in keys:
            value = env_values.get(key, "").strip()
            if value:
                return value
        return ""

    overrides = {
        "NAME": _first_non_empty("POSTGRES_DB", "DB_NAME"),
        "USER": _first_non_empty("POSTGRES_USER", "DB_USER"),
        "PASSWORD": _first_non_empty("POSTGRES_PASSWORD", "DB_PASSWORD"),
        "HOST": _first_non_empty("DB_HOST"),
        "PORT": _first_non_empty("DB_PORT"),
    }
    return {key: value for key, value in overrides.items() if value}


def _build_dotenv_database_overrides(
    existing_settings: Mapping[str, object],
    env_values: Mapping[str, str],
) -> dict[str, str]:
    raw_overrides = _database_url_overrides(env_values) or _legacy_env_overrides(env_values)
    overrides: dict[str, str] = {}
    for key, value in raw_overrides.items():
        existing_value = str(existing_settings.get(key, "")).strip()
        if existing_value:
            continue
        overrides[key] = value
    return overrides


def _hydrate_connection_settings_from_dotenv(
    connection: BaseDatabaseWrapper,
    *,
    database_alias: str,
) -> None:
    env_values = _load_dotenv_values(Path.cwd())
    if not env_values:
        return

    overrides = _build_dotenv_database_overrides(connection.settings_dict, env_values)
    if not overrides:
        return

    connection.settings_dict.update(overrides)
    settings.DATABASES[database_alias].update(overrides)


def get_database_connection(database_alias: str) -> BaseDatabaseWrapper:
    """Return the configured Django database connection for the alias."""

    try:
        connection = connections[database_alias]
    except KeyError as error:
        raise MigrationInspectionError(
            f"Unknown database alias {database_alias!r}. Check your Django DATABASES setting."
        ) from error

    _hydrate_connection_settings_from_dotenv(connection, database_alias=database_alias)
    try:
        connection.ensure_connection()
    except OperationalError as error:
        raise MigrationInspectionError(
            "Failed to connect to the configured Django database. "
            "If your project stores DB credentials in a local .env file, ensure "
            "python-dotenv is installed in the active venv and that the file contains "
            "DATABASE_URL or POSTGRES_/DB_ values."
        ) from error
    return connection


def load_migration_loader(database_alias: str) -> MigrationLoader:
    """Load Django's migration graph and applied migration state."""

    connection = get_database_connection(database_alias)
    return MigrationLoader(connection=connection, ignore_no_migrations=True)
