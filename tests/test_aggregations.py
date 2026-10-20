import pytest

from cadrates import Aggregation, DailyRate, LargestDailyChange, MonthlyAverage


def test_monthly_average_uses_every_available_value(sample_records):
    result = MonthlyAverage().compute(sample_records)
    assert result[1]["USD"] == pytest.approx(0.75)
    assert result[2]["USD"] == pytest.approx(0.80)


def test_monthly_average_ignores_missing_values(sample_records):
    # January GBP: the third record has no GBP, so only two values are averaged.
    result = MonthlyAverage().compute(sample_records)
    assert result[1]["GBP"] == pytest.approx((0.59 + 0.58) / 2)


def test_monthly_average_is_none_when_a_currency_is_never_present():
    records = [DailyRate("2024-03-01", {"USD": 0.7, "EUR": 0.6})]
    assert MonthlyAverage().compute(records)[3]["GBP"] is None


def test_largest_daily_change_picks_the_biggest_jump(sample_records):
    result = LargestDailyChange().compute(sample_records)
    assert result[1]["USD"] == pytest.approx(0.02)
    assert result[1]["EUR"] == pytest.approx(0.01)


def test_largest_daily_change_skips_pairs_with_a_missing_value(sample_records):
    # GBP is missing on 2024-01-04, so only the 02 -> 03 pair counts.
    result = LargestDailyChange().compute(sample_records)
    assert result[1]["GBP"] == pytest.approx(0.01)


def test_largest_daily_change_is_zero_for_a_single_day(sample_records):
    assert LargestDailyChange().compute(sample_records)[2]["USD"] == 0


def test_largest_daily_change_does_not_depend_on_input_order(sample_records):
    forward = LargestDailyChange().compute(sample_records)
    backward = LargestDailyChange().compute(list(reversed(sample_records)))
    assert forward == backward


def test_records_without_a_date_are_left_out():
    records = [DailyRate("bad", {"USD": 0.7, "EUR": 0.6, "GBP": 0.5})]
    assert MonthlyAverage().compute(records) == {}


def test_empty_input_gives_empty_result():
    assert MonthlyAverage().compute([]) == {}
    assert LargestDailyChange().compute([]) == {}


def test_base_class_must_be_overridden():
    with pytest.raises(NotImplementedError):
        Aggregation().compute([])


def test_each_subclass_has_its_own_summary_key():
    assert MonthlyAverage.key == "monthly_average"
    assert LargestDailyChange.key == "largest_daily_change"
