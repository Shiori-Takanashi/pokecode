# pokecode/main.py
import logging
import sys

from pokecode.request_html import request_html
from pokecode.logconfig import setup_logging
from pokecode.loading import load_config
from pokecode.config import Config


def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")

    logger.info("Application Start.")

    try:
        data = load_config(Config.PYPROJECT)
        url = Config.LOCAL_HTML_URL

        html = request_html(url=url)
        logger.info("HTML retrieved: %d characters", len(html))

    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)

    finally:
        logger.info("Application End.")


if __name__ == "__main__":
    main()
