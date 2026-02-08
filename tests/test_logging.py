import logging
import pytest
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

from pokecode.logconfig import setup_logging


@pytest.mark.usefixtures("reset_logging")
def test_setup_logging_adds_console_handler():
    """ """
    logger = logging.getLogger("pokecode.test")

    setup_logging(logger=logger)

    configured_handlers = logger.handlers

    console_handlers = [
        h
        for h in configured_handlers
        if isinstance(h, StreamHandler)
        and getattr(h, "name", None) == "console"
    ]

    file_handlers = [
        h
        for h in configured_handlers
        if isinstance(h, TimedRotatingFileHandler)
        and getattr(h, "name", None) == "file"
    ]

    assert len(console_handlers) == 1
    assert len(file_handlers) == 1
