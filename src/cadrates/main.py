"""Command line entry point: python -m cadrates.main [--config FILE]."""

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from .aggregations import LargestDailyChange, MonthlyAverage
from .config import DEFAULT_CONFIG_PATH, Settings, load_settings
from .errors import CadRatesError
from .logging_setup import configure_logging
from .report import build_summary, pick_featured_days, write_summary
from .run_info import build_run_info, write_run_info
from .sources import RateSource

logger = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m cadrates.main",
        description="Summarize CAD exchange rates from the Frankfurter API.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="settings file (default: %(default)s)",
    )
    return parser.parse_args(argv)


def run(settings: Settings) -> int:
    """Download, summarize and write both result files. Return the record count."""
    records = RateSource.from_settings(settings).fetch()
    logger.debug("%d records arrived", len(records))
    featured = pick_featured_days(records, settings.seed, settings.sample_size)
    summary = build_summary(
        settings.source_url,
        records,
        [MonthlyAverage(), LargestDailyChange()],
        featured_days=featured,
    )
    write_summary(summary, settings.summary_path)
    write_run_info(build_run_info(settings), settings.run_info_path)
    return len(records)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the program. Return 0 on success and 1 on an expected failure."""
    args = parse_args(argv)
    logging_ready = False
    try:
        settings = load_settings(args.config)
        configure_logging(settings.log_level)
        logging_ready = True
        logger.info("Starting a run with settings from %s", args.config)
        count = run(settings)
    except CadRatesError as error:
        if not logging_ready:
            configure_logging("INFO")
        logger.error("The run failed: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Processed {count} records.")
    print(f"Summary written to {settings.summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
