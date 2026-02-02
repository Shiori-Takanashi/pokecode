import random
import time
from logging import Logger

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from requests import Response

from pokecode.logs import create_logger

DOMAIN = "https://www.pokemongofriendcodes.com"
DEMO_DOMAIN = "http://127.0.0.1:5000/"

# このモジュール用のロガー
logger = create_logger(__name__)


def get_request(url: str, logger: Logger, max_retries: int = 5) -> Response:
    """
    指定されたURLからコンテンツを取得し、Responseオブジェクトを返す。
    503(Service Unavailable) の場合のみリトライを行う。
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    logger.info(f"Fetching URL: {url}")

    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(url, headers=headers, timeout=(10, 30))

            if res.status_code == 503:
                wait = min(2 ** (attempt - 1), 30) + random.random()
                logger.warning(
                    f"503 Service Unavailable (attempt {attempt}/{max_retries}), "
                    f"retrying after {wait:.1f}s"
                )
                time.sleep(wait)
                continue

            res.raise_for_status()
            logger.info(
                f"Successfully fetched URL: {url} (status code {res.status_code})"
            )
            return res

        except requests.RequestException as e:
            logger.warning(f"Request attempt {attempt}/{max_retries} failed: {e}")
            if attempt >= max_retries:
                logger.error(f"Giving up fetching URL: {url}")
                raise

            wait = min(2 ** (attempt - 1), 30) + random.random()
            time.sleep(wait)

    raise RuntimeError(f"Failed to fetch URL after {max_retries} retries: {url}")


def get_soup(res: Response) -> BeautifulSoup:
    return BeautifulSoup(res.text, "html.parser")


def scrape_tag_from_soup(
    parent: BeautifulSoup,
    elm: str,
    attribute_name: str | None,
    attribute_value: str | None,
    logger: Logger,
) -> ResultSet:
    if parent is None:
        raise RuntimeError("parent is None.")

    if (attribute_name is None) != (attribute_value is None):
        raise ValueError(
            "attribute_name and attribute_value must be both None or both set."
        )
    if attribute_name is None:
        results = parent.find_all(elm)
    else:
        results = parent.find_all(elm, attrs={attribute_name: attribute_value})

    logger.debug(
        f"Found {len(results)} <{elm}> elements ({attribute_name}={attribute_value})"
    )

    if isinstance(results, ResultSet):
        pass
    else:
        raise TypeError("results is not ResultSet.")

    if len(results) == 1:
        result = results[0]
    else:
        raise RuntimeError("results length is not one.")

    if isinstance(result, Tag):
        return result
    else:
        raise TypeError("result is not Tag.")


def scrape_resultset_from_soup(
    parent: BeautifulSoup,
    elm: str,
    attribute_name: str | None,
    attribute_value: str | None,
    logger: Logger,
) -> ResultSet:
    if parent is None:
        raise RuntimeError("parent is None.")

    if (attribute_name is None) != (attribute_value is None):
        raise ValueError(
            "attribute_name and attribute_value must be both None or both set."
        )
    if attribute_name is None:
        results = parent.find_all(elm)
    else:
        results = parent.find_all(elm, attrs={attribute_name: attribute_value})

    logger.debug(
        f"Found {len(results)} <{elm}> elements ({attribute_name}={attribute_value})"
    )

    if isinstance(results, ResultSet):
        return results
    else:
        raise TypeError("results is not ResultSet.")


def scrape_tag_from_tag():
    pass


def scrape_resultset_from_tag():
    pass


def scrape_tag_from_resultset():
    pass


def scrape_resultset_from_resultset():
    pass


def scrape_targets_from_parent(
    parent: BeautifulSoup | Tag,
    elm: str,
    attribute_name: str | None,
    attribute_value: str | None,
    logger: Logger,
) -> list[Tag]:
    """
    条件に一致する要素をすべて返す。
    「単一である」という前提は置かない。
    """
    if parent is None:
        raise RuntimeError("parent is None.")

    if (attribute_name is None) != (attribute_value is None):
        raise ValueError(
            "attribute_name and attribute_value must be both None or both set."
        )

    if attribute_name is None:
        results = parent.find_all(elm)
    else:
        results = parent.find_all(elm, attrs={attribute_name: attribute_value})

    logger.debug(
        f"Found {len(results)} <{elm}> elements ({attribute_name}={attribute_value})"
    )
    return results


def scrape_from_soup(soup: BeautifulSoup, logger: Logger) -> Tag:
    bodies = scrape_targets_from_parent(
        parent=soup,
        elm="body",
        attribute_name=None,
        attribute_value=None,
        logger=logger,
    )

    if not bodies:
        raise RuntimeError("<body> not found.")
    body = bodies[0]

    sections = scrape_targets_from_parent(
        parent=body,
        elm="section",
        attribute_name="id",
        attribute_value="countries",
        logger=logger,
    )

    if not sections:
        raise RuntimeError("<section id='countries'> not found.")

    # 必要ならここで複数対応も可能
    return sections[0]


res = get_request(DEMO_DOMAIN, logger)
soup = get_soup(res)
