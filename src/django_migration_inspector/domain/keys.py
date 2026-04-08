"""Typed key objects used across reports and graph models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class MigrationNodeKeyJSON(TypedDict):
    """Stable JSON shape for migration keys."""

    app_label: str
    migration_name: str
    identifier: str


@dataclass(frozen=True, order=True, slots=True)
class MigrationNodeKey:
    """Canonical key for one Django migration."""

    app_label: str
    migration_name: str

    @property
    def identifier(self) -> str:
        """Return a stable dotted identifier."""

        return f"{self.app_label}.{self.migration_name}"

    def to_tuple(self) -> tuple[str, str]:
        """Return the key in Django's native tuple shape."""

        return (self.app_label, self.migration_name)

    @classmethod
    def from_tuple(cls, raw_key: tuple[str, str]) -> MigrationNodeKey:
        """Create a domain key from a Django migration tuple."""

        return cls(app_label=raw_key[0], migration_name=raw_key[1])

    def to_json_dict(self) -> MigrationNodeKeyJSON:
        """Serialize the key into the report JSON contract."""

        return {
            "app_label": self.app_label,
            "migration_name": self.migration_name,
            "identifier": self.identifier,
        }
