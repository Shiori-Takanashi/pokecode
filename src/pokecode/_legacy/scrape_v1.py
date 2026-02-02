import random
import time
from logging import Logger

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from requests import Response

import logging

DOMAIN = "https://www.pokemongofriendcodes.com"
DEMO_DOMAIN = "http://127.0.0.1:5000/"

logger = logging.getLogger(__name__)


def get_soup(res: Response) -> BeautifulSoup:
    return BeautifulSoup(res.text, "html.parser")


def scrape_lang(soup: BeautifulSoup) -> str:
    html: Tag = soup.find("html")

    if html is None:
        logger.debug("html tag is not found.")
        raise RuntimeError("html tag is not found.")

    lang = html.get("lang")
    logger.info("Successsfully get lang.")

    return lang
