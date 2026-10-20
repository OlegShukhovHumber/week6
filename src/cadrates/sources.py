import logging
from collections.abc import Sequence
from typing import Any

import requests

from .config import DateTuple, Settings
from .errors import ResponseFormatError, SourceError
from .models import DailyRate

logger = logging.getLogger(__name__)


class RateSource:
    """Downloads exchange rates from the API and returns DailyRate objects."""

    def __init__(
        self,
        url: str,
        timeout: float,
        start_date_t: DateTuple,
        end_date_t: DateTuple,
    ) -> None:
        self.url = url
        self.timeout = timeout
        self.start_date_t = start_date_t
        self.end_date_t = end_date_t

    @classmethod
    def from_settings(cls, settings: Settings) -> "RateSource":
        """Build a source from the settings file."""
        return cls(
            url=settings.source_url,
            timeout=settings.timeout,
            start_date_t=settings.start_date_t,
            end_date_t=settings.end_date_t,
        )

    def fetch_raw(self) -> Any:
        """Download the JSON response."""
        logger.info("Downloading rates from %s", self.url)
        try:
            response = requests.get(self.url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as error:
            raise SourceError(f"Could not reach {self.url}: {error}") from error
        try:
            return response.json()
        except ValueError as error:
            raise ResponseFormatError(
                f"The response from {self.url} is not valid JSON"
            ) from error

    def build_records(self, raw: Any) -> list[DailyRate]:
        """Turn the raw JSON into a list of DailyRate objects."""
        if not isinstance(raw, dict) or not isinstance(raw.get("rates"), dict):
            raise ResponseFormatError(
                "Unexpected response format: expected an object with a 'rates' object"
            )
        records: list[DailyRate] = []
        for day, values in raw["rates"].items():
            if not isinstance(values, dict):
                raise ResponseFormatError(
                    f"Unexpected response format: the rates for {day} are not an object"
                )
            record = DailyRate(day, values)
            if record.date is None:
                logger.warning("Skipping record with an unreadable date: %r", day)
                continue
            records.append(record)
        logger.debug("Built %d records from the response", len(records))
        return records

    def filter_records(self, records: Sequence[DailyRate]) -> list[DailyRate]:
        """Keep only records whose date is inside the period."""
        kept = [
            r
            for r in records
            if r.date is not None and self.start_date_t <= r.date <= self.end_date_t
        ]
        logger.debug("Kept %d of %d records inside the period", len(kept), len(records))
        return kept

    def fetch(self) -> list[DailyRate]:
        """Download, build and filter the records."""
        raw = self.fetch_raw()
        records = self.build_records(raw)
        kept = self.filter_records(records)
        logger.info("Fetched %d records for the period", len(kept))
        return kept
