"""App configuration for the inventory fixture app."""

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Register the inventory fixture app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.fixtures.test_project.test_apps.inventory"
    label = "inventory"
