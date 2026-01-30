import logging
import sys
from logging import Logger, StreamHandler


def setup_logging(logger: Logger, *, level: str = "INFO") -> None:
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    target_stream = sys.stderr
    stream_handler = None

    for h in logger.handlers:
        if isinstance(h, StreamHandler) and getattr(h, "stream", None) is target_stream:
            stream_handler = h
            break

    if stream_handler is None:
        stream_handler = StreamHandler(target_stream)
        logger.addHandler(stream_handler)

    stream_handler.setFormatter(formatter)

    logger.propagate = False
