import json
import logging

import pytest
import requests

from cadrates.main import main


def error_lines(captured):
    return [line for line in captured.err.splitlines() if line.startswith("Error:")]


def test_a_successful_run_returns_0_and_writes_both_files(
    write_config, fake_api, api_payload, tmp_path, capsys
):
    fake_api(api_payload)
    code = main(["--config", str(write_config())])
    assert code == 0
    assert "Processed 3 records." in capsys.readouterr().out
    summary = json.loads((tmp_path / "out" / "summary.json").read_text("utf-8"))
    assert summary["records_processed"] == 3
    assert len(summary["featured_days"]) == 2
    assert (tmp_path / "out" / "run_info.json").exists()


def test_two_runs_with_the_same_seed_feature_the_same_days(
    write_config, fake_api, api_payload, tmp_path
):
    fake_api(api_payload)
    config = str(write_config(seed=11, sample_size=2))
    main(["--config", config])
    path = tmp_path / "out" / "summary.json"
    first = json.loads(path.read_text("utf-8"))["featured_days"]
    main(["--config", config])
    second = json.loads(path.read_text("utf-8"))["featured_days"]
    assert first == second


def test_a_failed_download_returns_1_with_one_error_line(
    write_config, fake_api, capsys
):
    fake_api(error=requests.ConnectionError("no network"))
    code = main(["--config", str(write_config())])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert len(error_lines(captured)) == 1
    assert "Could not reach" in captured.err
    assert "Traceback" not in captured.err


def test_an_unexpected_response_returns_1(write_config, fake_api, capsys):
    fake_api({"unexpected": True})
    assert main(["--config", str(write_config())]) == 1
    assert "Unexpected response format" in capsys.readouterr().err


def test_a_missing_settings_file_returns_1(tmp_path, capsys):
    code = main(["--config", str(tmp_path / "nope.toml")])
    captured = capsys.readouterr()
    assert code == 1
    assert error_lines(captured) == [
        f"Error: Settings file not found: {tmp_path / 'nope.toml'}"
    ]
    assert "Traceback" not in captured.err


def test_the_default_config_path_is_used_when_none_is_given(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 1
    assert "config/cadrates.toml" in capsys.readouterr().err


def test_an_unwritable_output_folder_returns_1(
    write_config, fake_api, api_payload, tmp_path, capsys
):
    blocker = tmp_path / "file.txt"
    blocker.write_text("in the way")
    fake_api(api_payload)
    code = main(
        ["--config", str(write_config(output_dir=(blocker / "out").as_posix()))]
    )
    assert code == 1
    assert "Could not write" in capsys.readouterr().err


def test_a_failed_run_is_logged_at_error_level(write_config, fake_api, caplog):
    fake_api(error=requests.Timeout("too slow"))
    with caplog.at_level(logging.DEBUG, logger="cadrates"):
        main(["--config", str(write_config())])
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "too slow" in errors[0].getMessage()


def test_an_unknown_option_is_rejected_by_argparse():
    with pytest.raises(SystemExit) as caught:
        main(["--nonsense"])
    assert caught.value.code == 2
