import json
import logging

import pytest

from cadrates import DailyRate, Settings, sources


class FakeResponse:
    """Stands in for requests.Response so no test touches the network."""

    def __init__(self, payload, status_error=None, json_error=None):
        self.payload = payload
        self.status_error = status_error
        self.json_error = json_error

    def raise_for_status(self):
        if self.status_error is not None:
            raise self.status_error

    def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


@pytest.fixture
def sample_records():
    """Four hand-made records: three days in January, one in February."""
    return [
        DailyRate("2024-01-02", {"USD": 0.75, "EUR": 0.69, "GBP": 0.59}),
        DailyRate("2024-01-03", {"USD": 0.76, "EUR": 0.70, "GBP": 0.58}),
        DailyRate("2024-01-04", {"USD": 0.74, "EUR": 0.69}),  # GBP missing
        DailyRate("2024-02-01", {"USD": 0.80, "EUR": 0.70, "GBP": 0.60}),
    ]


@pytest.fixture
def api_payload():
    """A response shaped like the Frankfurter API, with one day outside the period."""
    return {
        "base": "CAD",
        "rates": {
            "2023-12-29": {"USD": 0.75, "EUR": 0.68, "GBP": 0.59},
            "2024-01-02": {"USD": 0.75, "EUR": 0.69, "GBP": 0.59},
            "2024-01-03": {"USD": 0.76, "EUR": 0.70, "GBP": 0.58},
            "2024-02-01": {"USD": 0.80, "EUR": 0.70, "GBP": 0.60},
        },
    }


@pytest.fixture
def fake_api(monkeypatch):
    """Replace requests.get inside the sources module for one test."""

    def install(payload=None, *, error=None, status_error=None, json_error=None):
        def fake_get(*args, **kwargs):
            if error is not None:
                raise error
            return FakeResponse(payload, status_error, json_error)

        monkeypatch.setattr(sources.requests, "get", fake_get)

    return install


@pytest.fixture(autouse=True)
def restore_package_logger():
    """configure_logging changes global state; put it back after every test."""
    root, urllib3 = logging.getLogger(), logging.getLogger("urllib3")
    level, handlers, urllib3_level = root.level, list(root.handlers), urllib3.level
    yield
    root.setLevel(level)
    root.handlers[:] = handlers
    urllib3.setLevel(urllib3_level)


@pytest.fixture
def settings(tmp_path):
    """Settings that write into a temporary folder."""
    return Settings(
        source_url="https://example.invalid/rates",
        start_date="2024-01-01",
        end_date="2024-06-30",
        timeout=1.0,
        output_dir=tmp_path / "out",
        seed=7,
        sample_size=2,
        log_level="INFO",
    )


@pytest.fixture
def write_config(tmp_path):
    """Write a settings file into tmp_path; override or drop settings per test."""

    def write(*, drop=(), **overrides):
        values = {
            "source_url": "https://example.invalid/rates",
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "timeout": 5,
            "output_dir": (tmp_path / "out").as_posix(),
            "seed": 7,
            "sample_size": 2,
            "log_level": "INFO",
        }
        values.update(overrides)
        lines = [f"{k} = {json.dumps(v)}" for k, v in values.items() if k not in drop]
        path = tmp_path / "cadrates.toml"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    return write


@pytest.fixture
def many_records():
    """Twenty hand-made January days, enough to see a seed make a difference."""
    return [
        DailyRate(f"2024-01-{day:02d}", {"USD": 0.7, "EUR": 0.6, "GBP": 0.5})
        for day in range(1, 21)
    ]
