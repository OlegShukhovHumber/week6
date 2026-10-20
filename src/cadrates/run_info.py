"""run_info.json: what a classmate needs to repeat a run exactly."""

import importlib.metadata
import logging
import platform
from pathlib import Path
from typing import Any

from .config import Settings
from .report import write_json

logger = logging.getLogger(__name__)

TOOLS = ("pytest", "mypy", "ruff")


def package_version(name: str) -> str:
    """Return the installed version of a package, or say it is not installed."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        logger.warning("%s is not installed, so its version is not recorded", name)
        return "not installed"


def build_run_info(settings: Settings) -> dict[str, Any]:
    """Collect the settings and tool versions used for this run."""
    return {
        "settings": settings.as_dict(),
        "python_version": platform.python_version(),
        "tool_versions": {name: package_version(name) for name in TOOLS},
    }


def write_run_info(info: dict[str, Any], path: Path) -> None:
    """Write run_info.json next to summary.json."""
    write_json(info, path)
