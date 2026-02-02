import random
import time

import logging

import requests
from requests import Response


DOMAIN = "https://www.pokemongofriendcodes.com"
DEMO_DOMAIN = "http://127.0.0.1:5000/"

# このモジュール用のロガー
logger = logging.getLogger(__name__)


def get_request(parts_of_url: list[str], max_retries: int = 5) -> Response:
    """
    指定されたURLからコンテンツを取得し、Responseオブジェクトを返す。
    503(Service Unavailable) の場合のみリトライを行う。
    """
    url = ""
    for p in parts_of_url:
        url + p

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
