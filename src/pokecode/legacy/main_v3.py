import random
import time
from logging import Logger

import logging
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from requests import Response

from pokecode.request import get_request
from pokecode.scrape import get_soup, scrape_lang

from pokecode.logs import setup_logging

DEMO_DOMAIN = "http://127.0.0.1:5000/"

setup_logging()
logger = logging.getLogger("pokecode.main")


def main() -> None:
    logger.info("start")
    res: Response = get_request(DEMO_DOMAIN)
    soup: BeautifulSoup = get_soup(res)
    result = scrape_lang(soup)
    if isinstance(result, str):
        logger.info(result)
    else:
        raise RuntimeError("result is invalid.")


if __name__ == "__main__":
    main()
