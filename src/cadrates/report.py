import json
import logging
import random
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .aggregations import Aggregation
from .errors import OutputError
from .models import DailyRate

logger = logging.getLogger(__name__)


def pick_featured_days(
    records: Sequence[DailyRate], seed: int, sample_size: int
) -> list[str]:
    """Choose sample_size days at random; the same seed gives the same days.

    The candidates are sorted first, so the order the API happened to return
    the days in cannot change the result.
    """
    days = sorted(
        f"{r.date[0]:04d}-{r.date[1]:02d}-{r.date[2]:02d}"
        for r in records
        if r.date is not None
    )
    chosen = random.Random(seed).sample(days, k=min(sample_size, len(days)))
    logger.debug("Picked %d featured days with seed %s", len(chosen), seed)
    return sorted(chosen)


def build_summary(
    source_url: str,
    records: Sequence[DailyRate],
    aggregations: Sequence[Aggregation],
    featured_days: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build the summary dict by running every aggregation over the records."""
    summary: dict[str, Any] = {
        "source_url": source_url,
        "records_processed": len(records),
    }
    for aggregation in aggregations:
        logger.debug("Computing %s", aggregation.key)
        summary[aggregation.key] = aggregation.compute(records)
    if featured_days is not None:
        summary["featured_days"] = list(featured_days)
    return summary


def write_summary(summary: Mapping[str, Any], path: Path) -> None:
    """Write the summary to a JSON file, creating the folder if needed."""
    write_json(summary, path)


def write_json(data: Mapping[str, Any], path: Path) -> None:
    """Write a dict as indented JSON, turning file problems into OutputError."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except OSError as error:
        raise OutputError(f"Could not write {path}: {error}") from error
    logger.info("Wrote %s", path)
