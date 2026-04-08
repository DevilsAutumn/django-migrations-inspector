"""Helpers for ignoring non-project Django apps."""

from __future__ import annotations

from pathlib import Path

from django.apps import AppConfig, apps
from django.conf import settings


def _normalize_path(raw_path: Path | str | None) -> Path | None:
    if raw_path is None or raw_path == "":
        return None
    if isinstance(raw_path, Path):
        return raw_path.resolve()
    return Path(raw_path).resolve()


def _project_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    base_dir = _normalize_path(getattr(settings, "BASE_DIR", None))
    if base_dir is not None:
        roots.append(base_dir)

    current_working_directory = Path.cwd().resolve()
    if current_working_directory not in roots:
        roots.append(current_working_directory)

    return tuple(roots)


def _is_site_packages_path(app_path: Path) -> bool:
    return any(path_part in {"site-packages", "dist-packages"} for path_part in app_path.parts)


def _is_under_project_root(app_path: Path, *, project_roots: tuple[Path, ...]) -> bool:
    return any(app_path.is_relative_to(project_root) for project_root in project_roots)


def should_ignore_app(app_config: AppConfig) -> bool:
    """Return whether the app should be ignored as non-project code."""

    module_name = app_config.name
    app_path = Path(app_config.path).resolve()

    if module_name.startswith(("django.", "django.contrib.")):
        return True
    if module_name == "django_migration_inspector" or module_name.startswith(
        "django_migration_inspector."
    ):
        return True
    if _is_site_packages_path(app_path):
        return True
    return not _is_under_project_root(app_path, project_roots=_project_roots())


def build_ignored_app_labels() -> frozenset[str]:
    """Return installed app labels that should be ignored by default."""

    return frozenset(
        app_config.label for app_config in apps.get_app_configs() if should_ignore_app(app_config)
    )
