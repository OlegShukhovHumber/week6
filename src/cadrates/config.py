"""Settings: a TOML file read into one frozen object."""

import logging
import tomllib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .errors import SettingsError

logger = logging.getLogger(__name__)

DateTuple = tuple[int, int, int]

# The three currencies a DailyRate holds. This is the shape of a record, not a
# setting: the aggregations and the summary rely on it.
CURRENCIES = ["USD", "EUR", "GBP"]

DEFAULT_CONFIG_PATH = Path("config/cadrates.toml")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
REQUIRED_SETTINGS = (
    "source_url",
    "start_date",
    "end_date",
    "timeout",
    "output_dir",
    "seed",
    "sample_size",
    "log_level",
)


@dataclass(frozen=True)
class Settings:
    """Everything a run needs, read once and never changed."""

    source_url: str
    start_date: str
    end_date: str
    timeout: float
    output_dir: Path
    seed: int
    sample_size: int
    log_level: str

    @property
    def start_date_t(self) -> DateTuple:
        return _to_tuple(self.start_date)

    @property
    def end_date_t(self) -> DateTuple:
        return _to_tuple(self.end_date)

    @property
    def summary_path(self) -> Path:
        return self.output_dir / "summary.json"

    @property
    def run_info_path(self) -> Path:
        return self.output_dir / "run_info.json"

    def as_dict(self) -> dict[str, Any]:
        """Return the settings in a form json.dump accepts."""
        data = asdict(self)
        data["output_dir"] = self.output_dir.as_posix()
        return data


def _to_tuple(text: str) -> DateTuple:
    parsed = date.fromisoformat(text)
    return (parsed.year, parsed.month, parsed.day)


def _get_str(data: Mapping[str, Any], name: str) -> str:
    value = data[name]
    if not isinstance(value, str) or not value.strip():
        raise SettingsError(f"Setting '{name}' must be a non-empty string")
    return value


def _get_int(data: Mapping[str, Any], name: str, minimum: int) -> int:
    value = data[name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise SettingsError(f"Setting '{name}' must be a whole number")
    if value < minimum:
        raise SettingsError(f"Setting '{name}' must be at least {minimum}")
    return value


def _get_timeout(data: Mapping[str, Any]) -> float:
    value = data["timeout"]
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise SettingsError("Setting 'timeout' must be a number above 0")
    return float(value)


def _get_date(data: Mapping[str, Any], name: str) -> str:
    text = _get_str(data, name)
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as error:
        raise SettingsError(
            f"Setting '{name}' must be a date like 2024-01-31, got {text!r}"
        ) from error


def _get_log_level(data: Mapping[str, Any]) -> str:
    level = _get_str(data, "log_level").upper()
    if level not in LOG_LEVELS:
        raise SettingsError(
            f"Setting 'log_level' must be one of {', '.join(LOG_LEVELS)}, "
            f"got {data['log_level']!r}"
        )
    return level


def load_settings(path: Path | str = DEFAULT_CONFIG_PATH) -> Settings:
    """Read and check the TOML file. Raise SettingsError if it is unusable."""
    try:
        with open(path, "rb") as file:
            data = tomllib.load(file)
    except FileNotFoundError as error:
        raise SettingsError(f"Settings file not found: {path}") from error
    except OSError as error:
        raise SettingsError(
            f"Could not read the settings file {path}: {error}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(
            f"Settings file {path} is not valid TOML: {error}"
        ) from error

    missing = [name for name in REQUIRED_SETTINGS if name not in data]
    if missing:
        raise SettingsError(f"Settings file {path} is missing: {', '.join(missing)}")

    settings = Settings(
        source_url=_get_str(data, "source_url"),
        start_date=_get_date(data, "start_date"),
        end_date=_get_date(data, "end_date"),
        timeout=_get_timeout(data),
        output_dir=Path(_get_str(data, "output_dir")),
        seed=_get_int(data, "seed", minimum=-(2**63)),
        sample_size=_get_int(data, "sample_size", minimum=0),
        log_level=_get_log_level(data),
    )
    if settings.end_date_t < settings.start_date_t:
        raise SettingsError("Setting 'end_date' must not be before 'start_date'")
    logger.debug("Loaded settings from %s", path)
    return settings
