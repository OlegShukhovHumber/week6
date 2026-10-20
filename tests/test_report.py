import json

import pytest

from cadrates import (
    MonthlyAverage,
    OutputError,
    build_summary,
    write_summary,
)


def test_build_summary_has_the_lab_03_keys(sample_records):
    summary = build_summary(
        "https://example.invalid", sample_records, [MonthlyAverage()]
    )
    assert list(summary) == ["source_url", "records_processed", "monthly_average"]
    assert summary["records_processed"] == 4


def test_write_summary_creates_the_folder_and_the_file(tmp_path):
    target = tmp_path / "nested" / "summary.json"
    write_summary({"records_processed": 3}, target)
    assert json.loads(target.read_text(encoding="utf-8")) == {"records_processed": 3}


def test_write_summary_reports_an_unwritable_path(tmp_path):
    blocker = tmp_path / "file.txt"
    blocker.write_text("in the way")
    with pytest.raises(OutputError, match="Could not write"):
        write_summary({}, blocker / "summary.json")
