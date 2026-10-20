import json

import pytest

from cadrates import (
    MonthlyAverage,
    OutputError,
    build_summary,
    pick_featured_days,
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


def test_build_summary_adds_featured_days_after_the_lab_03_keys(sample_records):
    summary = build_summary(
        "https://example.invalid",
        sample_records,
        [MonthlyAverage()],
        featured_days=["2024-01-02"],
    )
    assert list(summary) == [
        "source_url",
        "records_processed",
        "monthly_average",
        "featured_days",
    ]
    assert summary["featured_days"] == ["2024-01-02"]


def test_the_same_seed_gives_the_same_featured_days(sample_records):
    first = pick_featured_days(sample_records, seed=123, sample_size=2)
    second = pick_featured_days(sample_records, seed=123, sample_size=2)
    assert first == second
    assert len(first) == 2


def test_a_different_seed_can_give_different_featured_days(many_records):
    results = {tuple(pick_featured_days(many_records, s, 5)) for s in range(10)}
    assert len(results) > 1


def test_featured_days_do_not_depend_on_input_order(many_records):
    forward = pick_featured_days(many_records, seed=5, sample_size=5)
    backward = pick_featured_days(list(reversed(many_records)), seed=5, sample_size=5)
    assert forward == backward


def test_featured_days_are_real_dates_from_the_records(many_records):
    available = {f"2024-01-{day:02d}" for day in range(1, 21)}
    assert set(pick_featured_days(many_records, seed=1, sample_size=5)) <= available


@pytest.mark.parametrize(("sample_size", "expected_length"), [(0, 0), (4, 4), (50, 4)])
def test_the_sample_size_is_capped_by_the_number_of_days(
    sample_records, sample_size, expected_length
):
    assert len(pick_featured_days(sample_records, 1, sample_size)) == expected_length


def test_no_records_give_no_featured_days():
    assert pick_featured_days([], seed=1, sample_size=5) == []
