# pokecode/logconfig.py

import logging
import sys

from logging import Formatter, StreamHandler


def setup_logging(level: str = "INFO") -> None:
    app_logger = logging.getLogger("pokecode")
    app_logger.propagate = False
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    app_logger.setLevel(resolved_level)

    fmt = "%(asctime)s [%(levelname)-5s]: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter: Formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    sh = StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    app_logger.addHandler(sh)
