import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


def setup_logging(
    *,
    level: str = "INFO",
    logdir: Path | str = "logs",
    logname: str = "app.log",
) -> None:
    root = logging.getLogger()
    logdir: Path = Path(logdir)
    filepath = logdir / logname

    # 既に同じファイルパスのハンドラーが存在するかチェック
    for handler in root.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            if Path(handler.baseFilename).resolve() == filepath.resolve():
                return

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(resolved_level)

    fmt = "%(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)

    logdir.mkdir(exist_ok=True)

    fileh = TimedRotatingFileHandler(
        filepath,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding=None,
    )
    fileh.setFormatter(formatter)

    root.addHandler(stream)
    root.addHandler(fileh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
