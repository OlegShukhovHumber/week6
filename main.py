import logging
import sys

from cadrates import (
    CadRatesError,
    LargestDailyChange,
    MonthlyAverage,
    RateSource,
)
from cadrates.config import OUTPUT_PATH, SOURCE_URL
from cadrates.logging_setup import configure_logging
from cadrates.report import build_summary, write_summary

logger = logging.getLogger(__name__)


def main():
    configure_logging("INFO")
    logger.info("Starting a run")
    try:
        records = RateSource().fetch()
        logger.debug("%d records arrived", len(records))
        aggregations = [MonthlyAverage(), LargestDailyChange()]
        summary = build_summary(SOURCE_URL, records, aggregations)
        write_summary(summary, OUTPUT_PATH)
    except CadRatesError as error:
        logger.error("The run failed: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Processed {len(records)} records.")
    print(f"Summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
