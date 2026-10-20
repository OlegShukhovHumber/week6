import pytest
import requests

from cadrates import RateSource, SourceError

URL = "https://example.invalid/rates"


def make_source():
    return RateSource(url=URL, timeout=1)


def test_a_failed_download_raises_a_source_error(fake_api):
    fake_api(error=requests.ConnectionError("no network"))
    with pytest.raises(SourceError, match="no network"):
        make_source().fetch_raw()


def test_an_http_error_status_raises_a_source_error(fake_api):
    fake_api(status_error=requests.HTTPError("500 Server Error"))
    with pytest.raises(SourceError, match="500"):
        make_source().fetch_raw()


def test_fetch_raw_returns_the_parsed_json(fake_api, api_payload):
    fake_api(api_payload)
    assert make_source().fetch_raw() == api_payload


@pytest.mark.parametrize("raw", [{}, [], None, "text"])
def test_a_response_without_rates_raises_a_source_error(raw):
    with pytest.raises(SourceError, match="unexpected response format"):
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
    source = make_source()
    bad = source.build_records({"rates": {"oops": {"USD": 1}}})
    assert source.filter_records(bad) == []


def test_fetch_downloads_builds_and_filters(fake_api, api_payload):
    fake_api(api_payload)
    records = make_source().fetch()
    assert len(records) == 3
