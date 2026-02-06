# pokecode/logconfig.py
import logging
from logging import Logger, StreamHandler, FileHandler
from pathlib import Path

from pokecode.paths import PROJECT_ROOT

_CONSOLE_NAME = "console"
_FILE_NAME = "file"


def _resolve_logfile(*, logdir_name: str, logname: str) -> Path:
    """ログファイルのパスを解決"""
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
    """
    logger をセットアップ

    Args:
        logger: セットアップ対象の Logger
        level: ログレベル（"DEBUG", "INFO" など）
        logdir_name: ログディレクトリ名
        logname: ログファイル名
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)
    logger.propagate = False

    # StreamHandler（重複チェック）
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

    # FileHandler（重複チェック）
    filepath = _resolve_logfile(logdir_name=logdir_name, logname=logname)

    fh = None
    for h in logger.handlers:
        if isinstance(h, FileHandler) and getattr(h, "name", None) == _FILE_NAME:
            fh = h
            break

    if fh is None:
        fh = FileHandler(
            filename=filepath, mode="a", encoding="utf-8", delay=False, errors="strict"
        )
        fh.name = _FILE_NAME
        logger.addHandler(fh)

    fh.setFormatter(formatter)
