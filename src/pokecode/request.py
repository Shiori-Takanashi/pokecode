import logging
import requests
from requests import Response

logger = logging.getLogger(__name__)


def request_json(url: str) -> dict | list:
    logger.info("Request start: %s", url)

    res: Response = requests.get(url)
    res.raise_for_status()

    try:
        data = res.json()
    except ValueError as e:
        ct = res.headers.get("Content-Type")
        logger.error("JSON parse failed. content-type=%s", ct)
        raise RuntimeError(f"JSON parse failed. content-type={ct}") from e

    if isinstance(data, dict):
        logger.debug("json is dict.")
        return data
    if isinstance(data, list):
        logger.debug("json is list.")
        return data

    raise RuntimeError("JSON is invalid.")
