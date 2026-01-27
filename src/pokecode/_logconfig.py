import logging
import sys
from pathlib import Path

from logging import Logger
from logging.handlers import TimedRotatingFileHandler
from logging import StreamHandler


def setup_logging(
    *,
    level: str = "INFO",
    logdir: Path | str = "logs",
    logname: str = "app.log",
    enable_stream: bool = True,
    enable_file: bool = True,
) -> None:
    app_logger: Logger = logging.getLogger("pokecode")
    app_logger.propagate = False
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    app_logger.setLevel(resolved_level)

    fmt = "%(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if enable_stream:
        for h in list(app_logger.handlers):
            if isinstance(h, StreamHandler):
                if getattr(h, "stream", None) == sys.stdout:
                    app_logger.removeHandler(h)
                    try:
                        h.flush()
                    except Exception:
                        pass

    if enable_file:
        for h in list(app_logger.handlers):
            if isinstance(h, TimedRotatingFileHandler):
                if hasattr(h, "baseFilename"):
                    if (
                        Path(h.baseFilename).resolve()
                        == Path(logdir, logname).resolve()
                    ):
                        app_logger.removeHandler(h)
                        try:
                            h.close()
                        except Exception:
                            pass

    if enable_stream:
        # Make Handler
        sh = StreamHandler(sys.stdout)

        # Setting Handler
        sh.setFormatter(formatter)

        # Add Handler
        app_logger.addHandler(sh)

    if enable_file:
        # 前処理
        logdir = Path(logdir)
        logdir.mkdir(exist_ok=True)
        filepath = logdir / logname

        # Make Handler
        fh = TimedRotatingFileHandler(
            filepath,
            when="midnight",
            interval=1,
            backupCount=0,
            encoding="utf-8",
            delay=True,
        )

        # Setting Handler
        fh.setFormatter(formatter)

        # Adding Handler
        app_logger.addHandler(fh)
