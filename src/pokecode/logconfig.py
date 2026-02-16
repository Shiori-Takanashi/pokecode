# pokecode/logconfig.py

from datetime import datetime
import logging
from logging import Logger, StreamHandler, FileHandler
from pathlib import Path

from pokecode.config.env import require
from pokecode.config.paths import PROJECT_ROOT


def _resolve_level(level: str) -> int:
    try:
        return getattr(logging, level.upper())
    except AttributeError:
        raise ValueError(f"Invalid log level: {level}")


def _get_or_create_stream_handler(
    logger: Logger,
    name: str,
) -> StreamHandler:
    for h in logger.handlers:
        if isinstance(h, StreamHandler) and getattr(h, "name", None) == name:
            return h

    sh = StreamHandler()
    sh.name = name
    logger.addHandler(sh)
    return sh


def _get_or_create_file_handler(
    logger: Logger,
    name: str,
    filepath: Path,
) -> FileHandler:
    for h in logger.handlers:
        if isinstance(h, FileHandler) and getattr(h, "name", None) == name:
            return h

    fh = FileHandler(
        filename=filepath,
        mode="a",
        encoding="utf-8",
        delay=False,
        errors="strict",
    )
    fh.name = name
    logger.addHandler(fh)
    return fh


def setup_logging(
    logger: Logger,
    level: str | None = None,
    dirname: str | None = None,
    basename: str | None = None,
) -> None:
    # ===== 設定値取得 =====
    level = level or require("LOG_LEVEL")
    log_fmt = require("LOG_FMT")
    log_date_fmt = require("LOG_DATE_FMT")
    dirname = dirname or require("LOG_DIR")
    basename = basename or require("LOG_FILE_BASE")

    stream_handler_name = require("STREAM_HANDLER_NAME")
    file_handler_name = require("FILE_HANDLER_NAME")

    # ===== レベル設定 =====
    logger.setLevel(_resolve_level(level))
    logger.propagate = False

    # ===== formatter =====
    formatter = logging.Formatter(
        fmt=log_fmt,
        datefmt=log_date_fmt,
    )

    # ===== directory =====
    dirpath = PROJECT_ROOT / dirname
    dirpath.mkdir(parents=True, exist_ok=True)

    # ===== file path =====
    filename = f"{basename}.log.{datetime.now():%Y-%m-%d}"
    filepath = dirpath / filename

    # ===== handlers =====
    sh = _get_or_create_stream_handler(logger, stream_handler_name)
    sh.setFormatter(formatter)

    fh = _get_or_create_file_handler(
        logger,
        file_handler_name,
        filepath,
    )
    fh.setFormatter(formatter)
