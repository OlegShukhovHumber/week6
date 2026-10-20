import logging

import pytest
import requests

from cadrates import (
    CadRatesError,
    DailyRate,
    RateSource,
    ResponseFormatError,
    SourceError,
)

URL = "https://example.invalid/rates"


def make_source():
    return RateSource(
        url=URL, timeout=1, start_date_t=(2024, 1, 1), end_date_t=(2024, 6, 30)
    )


def test_a_failed_download_raises_a_source_error(fake_api):
    fake_api(error=requests.ConnectionError("no network"))
    with pytest.raises(SourceError, match="Could not reach"):
        make_source().fetch_raw()


def test_an_http_error_status_raises_a_source_error(fake_api):
    fake_api(status_error=requests.HTTPError("500 Server Error"))
    with pytest.raises(SourceError, match="500"):
        make_source().fetch_raw()


def test_fetch_raw_returns_the_parsed_json(fake_api, api_payload):
    fake_api(api_payload)
    assert make_source().fetch_raw() == api_payload


@pytest.mark.parametrize("raw", [{}, {"rates": None}, {"rates": []}, [], None, "text"])
def test_a_response_without_rates_raises_a_format_error(raw):
    with pytest.raises(ResponseFormatError, match="Unexpected response format"):
        make_source().build_records(raw)


def test_build_records_makes_one_record_per_day(api_payload):
    records = make_source().build_records(api_payload)
    assert len(records) == 4
    assert records[1].date == (2024, 1, 2)


def test_filter_records_keeps_only_the_period(api_payload):
    source = make_source()
    kept = source.filter_records(source.build_records(api_payload))
    assert [r.date for r in kept] == [(2024, 1, 2), (2024, 1, 3), (2024, 2, 1)]


def test_filter_records_drops_records_with_a_bad_date():
    assert make_source().filter_records([DailyRate("oops", {"USD": 1})]) == []


def test_build_records_skips_a_bad_date_and_logs_a_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="cadrates"):
        records = make_source().build_records({"rates": {"oops": {"USD": 1}}})
    assert records == []
    assert "Skipping record with an unreadable date: 'oops'" in caplog.text


def test_fetch_logs_a_milestone_at_info_level(fake_api, api_payload, caplog):
    fake_api(api_payload)
    with caplog.at_level(logging.INFO, logger="cadrates"):
        make_source().fetch()
    assert "Fetched 3 records for the period" in caplog.text


def test_fetch_downloads_builds_and_filters(fake_api, api_payload):
    fake_api(api_payload)
    records = make_source().fetch()
    assert len(records) == 3


def test_rates_for_a_day_must_be_an_object():
    with pytest.raises(ResponseFormatError, match="2024-01-02"):
        make_source().build_records({"rates": {"2024-01-02": [0.7]}})


def test_a_response_that_is_not_json_raises_a_format_error(fake_api):
    fake_api(json_error=ValueError("Expecting value"))
    with pytest.raises(ResponseFormatError, match="not valid JSON"):
        make_source().fetch_raw()


def test_the_original_error_is_kept_as_the_cause(fake_api):
    original = requests.Timeout("too slow")
    fake_api(error=original)
    with pytest.raises(SourceError) as caught:
        make_source().fetch_raw()
    assert caught.value.__cause__ is original


@pytest.mark.parametrize("error_class", [SourceError, ResponseFormatError])
def test_every_package_error_shares_one_base_class(error_class):
    assert issubclass(error_class, CadRatesError)
