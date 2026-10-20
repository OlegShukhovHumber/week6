import logging
from collections.abc import Mapping
from typing import Any

from .config import CURRENCIES, DateTuple

logger = logging.getLogger(__name__)


class DailyRate:
    """Exchange rates for the base currency on a single day."""

    def __init__(self, day: str, rates: Mapping[str, Any]) -> None:
        self.date: DateTuple | None = self._parse_date(day)
        self.month: int | None = self.date[1] if self.date else None
        self.rates: dict[str, float | None] = {
            c: self._to_float(rates.get(c)) for c in CURRENCIES
        }

    def _parse_date(self, day: str) -> DateTuple | None:
        try:
            year, month, d = map(int, day.split("-"))
            return (year, month, d)
        except (ValueError, AttributeError):
            return None

    def _to_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.debug("Could not read a rate from %r", value)
            return None

    def __str__(self) -> str:
        return f"{self.date}: " + ", ".join(f"{c}={v}" for c, v in self.rates.items())
