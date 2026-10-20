"""One place that decides where log messages go and how they look."""

import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
HANDLER_NAME = "cadrates-stderr"


def configure_logging(level: str | int = "INFO") -> None:
    """Send log messages to stderr at the given level.

    The handler sits on the root logger because a module run with
    ``python -m cadrates.main`` is named ``__main__``, not ``cadrates.main``.
    Calling this again replaces the handler instead of adding a second one.
    """
    root = logging.getLogger()
    for handler in list(root.handlers):
        if handler.get_name() == HANDLER_NAME:
            root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(level.upper() if isinstance(level, str) else level)
    # urllib3 is chatty at DEBUG and we only want our own messages.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
