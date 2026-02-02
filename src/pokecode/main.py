# pokecode/main.py
import logging
import sys

from pokecode.request import request_json
from pokecode.logconfig import setup_logging
from pokecode.loading import load_config
from pokecode.config import PYPROJECT


def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")

    logger.info("Application Start.")

    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["local"]

        msg = request_json(url)
        logger.info("Response payload: %s", msg)

    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)

    finally:
        logger.info("Application End.")


if __name__ == "__main__":
    main()
