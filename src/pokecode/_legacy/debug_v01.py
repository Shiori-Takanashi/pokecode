from bs4 import BeautifulSoup
import requests
import logging

from requests import Response
from logging import Logger


def main() -> None:
    logger: Logger = logging.getLogger("main")
    url: str = "https://feeld-uni.com"
    res: Response = requests.get(url)
    if not res.status_code == 200:
        raise
    soup = BeautifulSoup(res.text, "html.parser")
    logger.info(type(soup))


if __name__ == "__main__":
    main()
