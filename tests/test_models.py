import pytest

from cadrates import DailyRate


def test_normal_record():
    record = DailyRate("2024-01-02", {"USD": 0.75, "EUR": 0.69, "GBP": 0.59})
    assert record.date == (2024, 1, 2)
    assert record.month == 1
    assert record.rates == {"USD": 0.75, "EUR": 0.69, "GBP": 0.59}


def test_missing_currency_becomes_none():
    record = DailyRate("2024-01-02", {"USD": 0.75, "EUR": 0.69})
    assert record.rates["GBP"] is None


def test_missing_rate_value_becomes_none():
    record = DailyRate("2024-01-02", {"USD": 0.75, "EUR": 0.69, "GBP": None})
    assert record.rates["GBP"] is None
    assert record.rates["USD"] == 0.75


@pytest.mark.parametrize("bad_date", ["not-a-date", "2024-01", "", "2024/01/02", None])
def test_bad_date_gives_no_date_and_no_month(bad_date):
    record = DailyRate(bad_date, {"USD": 0.75, "EUR": 0.69, "GBP": 0.59})
    assert record.date is None
    assert record.month is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("0.75", 0.75), (1, 1.0), ("abc", None), (None, None), ([], None)],
)
def test_rates_are_converted_to_float_or_none(raw, expected):
    record = DailyRate("2024-01-02", {"USD": raw})
    assert record.rates["USD"] == expected


def test_str_shows_date_and_rates():
    record = DailyRate("2024-01-02", {"USD": 0.75, "EUR": 0.69, "GBP": 0.59})
    assert str(record) == "(2024, 1, 2): USD=0.75, EUR=0.69, GBP=0.59"
