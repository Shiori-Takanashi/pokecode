import logging
from logging import Logger, StreamHandler


def setup_logging(*, logger: Logger, level: str = "INFO"):
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)
    logger.propagate = False

    sh = None
    for h in logger.handlers:
        if (
            isinstance(h, StreamHandler)
            and getattr(h, "name", None) == "pokecode-console"
        ):
            sh = h
            break

    if sh is None:
        sh = StreamHandler()
        sh.name = "console"
        logger.addHandler(sh)

    sh.setFormatter(formatter)
