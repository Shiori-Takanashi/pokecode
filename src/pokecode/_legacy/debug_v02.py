import logging
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Response
from logging import Logger


def log_type(logger: Logger, label: str, obj) -> None:
    logger.info("%s: %s", label, type(obj))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("type-check")

    url = "https://feeld-uni.com"
    res: Response = requests.get(url, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # 1. BeautifulSoup 自体
    log_type(logger, "soup", soup)

    # 2. find の戻り値
    title = soup.find("title")
    log_type(logger, "soup.find('title')", title)

    # 3. Tag からの遷移
    if isinstance(title, Tag):
        log_type(logger, "title.name", title.name)
        log_type(logger, "title.string", title.string)

        if title.string:
            log_type(logger, "type(title.string)", title.string)

    # 4. find_all の戻り値
    links = soup.find_all("a")
    log_type(logger, "soup.find_all('a')", links)

    if links:
        log_type(logger, "links[0]", links[0])


if __name__ == "__main__":
    main()
