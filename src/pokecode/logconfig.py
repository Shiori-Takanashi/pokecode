# pokecode/logconfig.py
from datetime import datetime
import logging
from pokecode.config import ConfigGetter
from logging import (
    Logger,
    StreamHandler,
    FileHandler,
)

from pokecode.paths import PROJECT_ROOT


def resolve_level(level: str) -> int:
    try:
        resolved_level = getattr(logging, level.upper())
    except AttributeError:
        raise ValueError(f"Invalid log level: {level}")
    return resolved_level


def setup_logging(
    logger: Logger,
    level: str = "INFO",
    dirname: str | None = None,
    filename: str | None = None,
) -> None:
    """
    logger をセットアップ

    Args:
        logger: セットアップ対象の Logger
        level: ログレベル（"DEBUG", "INFO" など）
        logdir_name: ログディレクトリ名
        logname: ログファイル名
    """
    cget = ConfigGetter()

    formatter = logging.Formatter(
        fmt=cget.get_base_fmt(), datefmt=cget.get_date_fmt()
    )

    # directoryの処理
    if dirname is None:
        dirname = cget.get_dirname_of_log()
    dirpath = PROJECT_ROOT / dirname
    dirpath.mkdir(exist_ok=True)

    # fileの処理
    if filename is None:
        filename = cget.get_filename_log()
    full_filename = f"{filename}.log.{datetime.now():%Y-%m-%d}"
    full_filepath = dirpath / full_filename

    # level設定
    logger.setLevel(resolve_level(level))

    # propagete設定
    logger.propagate = False

    # StreamHandler（重複チェック）
    sh = None
    stream_hander_name = cget.get_stream_handler_name()
    for h in logger.handlers:
        if (
            isinstance(h, StreamHandler)
            and getattr(h, "name", None) == stream_hander_name
        ):
            sh = h
            break

    if sh is None:
        sh = StreamHandler()
        sh.name = stream_hander_name
        logger.addHandler(sh)

    sh.setFormatter(formatter)

    # FileHandler（重複チェック）
    fh = None
    file_handler_name = cget.get_file_handler_name()
    for h in logger.handlers:
        if (
            isinstance(h, FileHandler)
            and getattr(h, "name", None) == file_handler_name
        ):
            fh = h
            break

    if fh is None:
        fh = FileHandler(
            filename=full_filepath,
            mode="a",
            encoding="utf-8",
            delay=False,
            errors="strict",
        )
        fh.name = file_handler_name
        logger.addHandler(fh)

    fh.setFormatter(formatter)


def main() -> None:
    logger = logging.getLogger("ForDebug")
    setup_logging(logger)
    logger.info("this is debug")


if __name__ == "__main__":
    main()
