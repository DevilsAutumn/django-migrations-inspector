"""App configuration for the catalog fixture app."""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Register the catalog fixture app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.fixtures.test_project.test_apps.catalog"
    label = "catalog"

