# pokecode/logs.py
import logging
import sys


def setup_logging(*, level=logging.INFO, log_file="all.log") -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-5s] %(name)s %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)

    root.addHandler(sh)
    root.addHandler(fh)
