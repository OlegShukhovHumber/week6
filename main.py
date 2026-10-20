import sys

from cadrates import (
    CadRatesError,
    LargestDailyChange,
    MonthlyAverage,
    RateSource,
)
from cadrates.config import OUTPUT_PATH, SOURCE_URL
from cadrates.report import build_summary, write_summary


def main():
    try:
        records = RateSource().fetch()
        aggregations = [MonthlyAverage(), LargestDailyChange()]
        summary = build_summary(SOURCE_URL, records, aggregations)
        write_summary(summary, OUTPUT_PATH)
    except CadRatesError as error:
        print(f"Error: {error}")
        sys.exit(1)

    print(f"Processed {len(records)} records.")
    print(f"Summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
