"""One place that decides where log messages go and how they look."""

import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
HANDLER_NAME = "cadrates-stderr"


def configure_logging(level="INFO"):
    """Send the package's log messages to stderr at the given level.

    Calling it again replaces the handler instead of adding a second one.
    """
    logger = logging.getLogger("cadrates")
    for handler in list(logger.handlers):
        if handler.get_name() == HANDLER_NAME:
            logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(level.upper() if isinstance(level, str) else level)
