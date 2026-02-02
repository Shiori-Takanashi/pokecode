# pokecode/logconfig.py
import logging
from logging import Logger, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from pokecode.config import PROJECT_ROOT

_CONSOLE_NAME = "console"
_FILE_NAME = "file"


def _resolve_logfile(*, logdir_name: str, logname: str) -> Path:
    logdir = PROJECT_ROOT / logdir_name
    logdir.mkdir(parents=True, exist_ok=True)
    return logdir / logname


def setup_logging(
    *,
    logger: Logger,
    level: str = "INFO",
    logdir_name: str = "logs",
    logname: str = "app.log",
) -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)
    logger.propagate = False

    sh = None
    for h in logger.handlers:
        if isinstance(h, StreamHandler) and getattr(h, "name", None) == _CONSOLE_NAME:
            sh = h
            break

    if sh is None:
        sh = StreamHandler()
        sh.name = _CONSOLE_NAME
        logger.addHandler(sh)

    sh.setFormatter(formatter)

    filepath = _resolve_logfile(logdir_name=logdir_name, logname=logname)

    fh = None
    for h in logger.handlers:
        if (
            isinstance(h, TimedRotatingFileHandler)
            and getattr(h, "name", None) == _FILE_NAME
        ):
            fh = h
            break

    if fh is None:
        fh = TimedRotatingFileHandler(
            filename=filepath,
            when="D",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        fh.name = _FILE_NAME
        logger.addHandler(fh)

    fh.setFormatter(formatter)
