import logging
import requests
from requests import Response

logger = logging.getLogger(__name__)


def requests_json(url: str) -> dict | list:
    logger.info("Request start: %s", url)

    res: Response = requests.get(url)
    res.raise_for_status()

    try:
        data = res.json()
    except ValueError as e:
        ct = res.headers.get("Content-Type")
        logger.error("JSON parse failed. content-type=%s", ct)
        raise RuntimeError(f"JSON parse failed. content-type={ct}") from e

    logger.info("Request success: type=%s", type(data).__name__)

    if isinstance(data, dict):
        logger.info("json is dict.")
        return data
    if isinstance(data, list):
        logger.info("json is list.")
        return data

    raise RuntimeError("JSON is invalid.")
