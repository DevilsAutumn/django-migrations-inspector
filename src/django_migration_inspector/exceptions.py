"""Package-specific exception types."""


class DjangoMigrationInspectorError(Exception):
    """Base exception for all package-specific failures."""


class UnsupportedDjangoVersionError(DjangoMigrationInspectorError):
    """Raised when the active Django version is outside the supported range."""


class MigrationInspectionError(DjangoMigrationInspectorError):
    """Raised when migration inspection cannot complete safely."""
