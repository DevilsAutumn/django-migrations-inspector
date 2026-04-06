"""Django compatibility guards."""

from __future__ import annotations

from django import VERSION as DJANGO_VERSION
from django import get_version

from django_migration_inspector.constants import (
    MAX_SUPPORTED_DJANGO_VERSION_EXCLUSIVE,
    MIN_SUPPORTED_DJANGO_VERSION,
)
from django_migration_inspector.exceptions import UnsupportedDjangoVersionError


def validate_supported_django_version() -> None:
    """Raise if the active Django version is outside the supported range."""

    version_prefix = DJANGO_VERSION[:2]
    if version_prefix < MIN_SUPPORTED_DJANGO_VERSION:
        raise UnsupportedDjangoVersionError(
            "Django Migration Inspector supports Django "
            f"{MIN_SUPPORTED_DJANGO_VERSION[0]}.{MIN_SUPPORTED_DJANGO_VERSION[1]} "
            f"and newer. Detected Django {get_version()}."
        )

    if version_prefix >= MAX_SUPPORTED_DJANGO_VERSION_EXCLUSIVE:
        raise UnsupportedDjangoVersionError(
            "Django Migration Inspector currently supports Django versions earlier than "
            f"{MAX_SUPPORTED_DJANGO_VERSION_EXCLUSIVE[0]}.0. "
            f"Detected Django {get_version()}."
        )
