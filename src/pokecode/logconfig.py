# pokecode/logconfig.py

import logging
import sys

from logging import Formatter, StreamHandler


def setup_logging(level: str = "INFO") -> None:
    logger = logging.getLogger("pokecode")

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)

    fmt = "%(asctime)s [%(levelname)-5s] %(name)s %(module)s:%(funcName)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter: Formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if not any(isinstance(h, StreamHandler) for h in logger.handlers):
        sh = StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.propagate = False
