"""Django app configuration for the reusable package."""

from django.apps import AppConfig


class DjangoMigrationInspectorConfig(AppConfig):
    """Register the reusable Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_migration_inspector"
    verbose_name = "Django Migration Inspector"
