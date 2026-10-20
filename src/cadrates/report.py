import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .aggregations import Aggregation
from .errors import OutputError
from .models import DailyRate

logger = logging.getLogger(__name__)


def build_summary(
    source_url: str,
    records: Sequence[DailyRate],
    aggregations: Sequence[Aggregation],
) -> dict[str, Any]:
    """Build the summary dict by running every aggregation over the records."""
    summary: dict[str, Any] = {
        "source_url": source_url,
        "records_processed": len(records),
    }
    for aggregation in aggregations:
        logger.debug("Computing %s", aggregation.key)
        summary[aggregation.key] = aggregation.compute(records)
    return summary


def write_summary(summary: Mapping[str, Any], path: Path) -> None:
    """Write the summary to a JSON file, creating the folder if needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(summary, file, indent=2, ensure_ascii=False)
    except OSError as error:
        raise OutputError(f"Could not write {path}: {error}") from error
    logger.info("Wrote %s", path)
