import logging
import sys

from cadrates import (
    CadRatesError,
    LargestDailyChange,
    MonthlyAverage,
    RateSource,
    load_settings,
)
from cadrates.config import DEFAULT_CONFIG_PATH
from cadrates.logging_setup import configure_logging
from cadrates.report import build_summary, write_summary

logger = logging.getLogger(__name__)


def main():
    configure_logging("INFO")
    logger.info("Starting a run")
    try:
        settings = load_settings(DEFAULT_CONFIG_PATH)
        configure_logging(settings.log_level)
        records = RateSource.from_settings(settings).fetch()
        logger.debug("%d records arrived", len(records))
        aggregations = [MonthlyAverage(), LargestDailyChange()]
        summary = build_summary(settings.source_url, records, aggregations)
        write_summary(summary, settings.summary_path)
    except CadRatesError as error:
        logger.error("The run failed: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Processed {len(records)} records.")
    print(f"Summary written to {settings.summary_path}")


if __name__ == "__main__":
    main()
