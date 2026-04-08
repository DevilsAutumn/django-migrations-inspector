"""Unit tests for database-loader helpers."""

from __future__ import annotations

from django_migration_inspector.django_adapter.loader import (
    _build_dotenv_database_overrides,
    _database_url_overrides,
    _legacy_env_overrides,
)


def test_database_url_overrides_parse_postgres_url() -> None:
    overrides = _database_url_overrides(
        {"DATABASE_URL": "postgresql://trevo:password@localhost:5432/trevo"}
    )

    assert overrides == {
        "NAME": "trevo",
        "USER": "trevo",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    }


def test_legacy_env_overrides_read_postgres_vars() -> None:
    overrides = _legacy_env_overrides(
        {
            "POSTGRES_DB": "trevo",
            "POSTGRES_USER": "trevo",
            "POSTGRES_PASSWORD": "password",
            "DB_HOST": "localhost",
        }
    )

    assert overrides == {
        "NAME": "trevo",
        "USER": "trevo",
        "PASSWORD": "password",
        "HOST": "localhost",
    }


def test_build_dotenv_database_overrides_only_fills_missing_values() -> None:
    overrides = _build_dotenv_database_overrides(
        {
            "NAME": "trevo",
            "USER": "trevo",
            "PASSWORD": "",
            "HOST": "localhost",
            "PORT": "5432",
        },
        {
            "POSTGRES_DB": "ignored-db",
            "POSTGRES_USER": "ignored-user",
            "POSTGRES_PASSWORD": "password",
            "DB_HOST": "ignored-host",
        },
    )

    assert overrides == {
        "PASSWORD": "password",
    }
