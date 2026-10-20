import logging
from collections.abc import Mapping, Sequence
from typing import ClassVar

from .config import CURRENCIES, DateTuple
from .models import DailyRate

logger = logging.getLogger(__name__)

MonthlyStats = Mapping[int, Mapping[str, float | None]]


class Aggregation:
    """Base class: one named statistic computed over a list of DailyRate."""

    key: ClassVar[str] = ""

    def compute(self, records: Sequence[DailyRate]) -> MonthlyStats:
        """Return the statistic. Every subclass must override this."""
        raise NotImplementedError

    def _group_by_month(
        self, records: Sequence[DailyRate]
    ) -> dict[int, list[DailyRate]]:
        """Return {month: [records of that month]}, skipping records without a date."""
        groups: dict[int, list[DailyRate]] = {}
        for record in records:
            if record.month is None:
                continue
            if record.month not in groups:
                groups[record.month] = []
            groups[record.month].append(record)
        logger.debug("Grouped %d records into %d months", len(records), len(groups))
        return groups


class MonthlyAverage(Aggregation):
    """Average rate of each currency per month."""

    key = "monthly_average"

    def compute(self, records: Sequence[DailyRate]) -> MonthlyStats:
        groups = self._group_by_month(records)
        result: dict[int, dict[str, float | None]] = {}
        for month in sorted(groups):
            result[month] = {}
            for currency in CURRENCIES:
                values: list[float] = []
                for record in groups[month]:
                    rate = record.rates[currency]
                    if rate is not None:
                        values.append(rate)
                result[month][currency] = sum(values) / len(values) if values else None
        return result


class LargestDailyChange(Aggregation):
    """Largest day-to-day change of each currency per month."""

    key = "largest_daily_change"

    def _get_date(self, record: DailyRate) -> DateTuple:
        # Records are grouped by month, so every record here has a date.
        assert record.date is not None
        return record.date

    def compute(self, records: Sequence[DailyRate]) -> MonthlyStats:
        groups = self._group_by_month(records)
        result: dict[int, dict[str, float]] = {}
        for month in sorted(groups):
            days = sorted(groups[month], key=self._get_date)
            max_change: dict[str, float] = {currency: 0 for currency in CURRENCIES}

            for i in range(len(days) - 1):
                today = days[i]
                tomorrow = days[i + 1]
                for currency in CURRENCIES:
                    before = today.rates[currency]
                    after = tomorrow.rates[currency]
                    if before is None or after is None:
                        continue
                    change = abs(after - before)
                    if change > max_change[currency]:
                        max_change[currency] = change

            result[month] = max_change
        return result
