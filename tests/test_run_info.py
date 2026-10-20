import json
import platform

from cadrates import build_run_info, write_run_info
from cadrates.run_info import package_version


def test_run_info_records_settings_python_and_tool_versions(settings):
    info = build_run_info(settings)
    assert info["settings"]["seed"] == 7
    assert info["settings"]["output_dir"].endswith("out")
    assert info["python_version"] == platform.python_version()
    assert set(info["tool_versions"]) == {"pytest", "mypy", "ruff"}


def test_run_info_can_be_written_as_json(settings, tmp_path):
    target = tmp_path / "run_info.json"
    write_run_info(build_run_info(settings), target)
    assert (
        json.loads(target.read_text(encoding="utf-8"))["settings"]["sample_size"] == 2
    )


def test_a_package_that_is_not_installed_is_reported_and_logged(caplog):
    version = package_version("package-that-does-not-exist")
    assert version == "not installed"
    assert "not installed" in caplog.text
