# pokecode/main.py
import logging

from pokecode.request import requests_json
from pokecode.logconfig import setup_logging
from pokecode.loading import load_config
from pokecode.config import PYPROJECT


def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger, level="INFO")

    logger.info("Application Start.")

    data = load_config(PYPROJECT)
    url = data["tool"]["pokecode"]["local"]

    msg = requests_json(url)
    logger.info("Response payload: %s", msg)

    logger.info("Application End.")


if __name__ == "__main__":
    main()
