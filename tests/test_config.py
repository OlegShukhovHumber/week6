import dataclasses
from pathlib import Path

import pytest

from cadrates import SettingsError, load_settings
from cadrates.config import REQUIRED_SETTINGS


def test_a_valid_file_becomes_a_settings_object(write_config, tmp_path):
    settings = load_settings(write_config())
    assert settings.seed == 7
    assert settings.sample_size == 2
    assert settings.timeout == 5.0
    assert settings.output_dir == tmp_path / "out"
    assert settings.start_date_t == (2024, 1, 1)
    assert settings.summary_path == tmp_path / "out" / "summary.json"


def test_settings_cannot_be_changed_after_loading(write_config):
    settings = load_settings(write_config())
    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.seed = 99


def test_log_level_is_accepted_in_any_case(write_config):
    assert load_settings(write_config(log_level="debug")).log_level == "DEBUG"


def test_the_project_settings_file_is_valid():
    settings = load_settings(Path("config/cadrates.toml"))
    assert settings.sample_size > 0


def test_a_missing_file_raises_a_settings_error(tmp_path):
    with pytest.raises(SettingsError, match="not found"):
        load_settings(tmp_path / "nope.toml")


def test_a_file_that_is_not_toml_raises_a_settings_error(tmp_path):
    broken = tmp_path / "broken.toml"
    broken.write_text("this is = = not toml", encoding="utf-8")
    with pytest.raises(SettingsError, match="not valid TOML"):
        load_settings(broken)


@pytest.mark.parametrize("name", REQUIRED_SETTINGS)
def test_every_setting_is_required(write_config, name):
    with pytest.raises(SettingsError, match=f"missing: {name}"):
        load_settings(write_config(drop=[name]))


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"timeout": 0}, "timeout"),
        ({"timeout": "ten"}, "timeout"),
        ({"seed": 1.5}, "seed"),
        ({"seed": True}, "seed"),
        ({"sample_size": -1}, "sample_size"),
        ({"log_level": "LOUD"}, "log_level"),
        ({"start_date": "yesterday"}, "start_date"),
        ({"source_url": ""}, "source_url"),
        ({"end_date": "2023-12-31"}, "must not be before"),
    ],
)
def test_unusable_values_raise_a_settings_error(write_config, override, message):
    with pytest.raises(SettingsError, match=message):
        load_settings(write_config(**override))
