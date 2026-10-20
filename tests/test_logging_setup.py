import logging

import pytest

from cadrates.logging_setup import HANDLER_NAME, configure_logging


def package_handlers():
    return [
        h
        for h in logging.getLogger("cadrates").handlers
        if h.get_name() == HANDLER_NAME
    ]


@pytest.mark.parametrize(
    ("name", "expected"),
    [("DEBUG", logging.DEBUG), ("info", logging.INFO), ("WARNING", logging.WARNING)],
)
def test_configure_logging_sets_the_level(name, expected):
    configure_logging(name)
    assert logging.getLogger("cadrates").level == expected


def test_configuring_twice_keeps_a_single_handler():
    configure_logging("INFO")
    configure_logging("DEBUG")
    assert len(package_handlers()) == 1


def test_messages_reach_stderr_not_stdout(capsys):
    configure_logging("INFO")
    logging.getLogger("cadrates.test").info("hello %s", "world")
    captured = capsys.readouterr()
    assert "hello world" in captured.err
    assert captured.out == ""
