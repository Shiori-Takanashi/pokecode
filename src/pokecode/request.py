import logging

import requests
from requests import Response

logger = logging.getLogger(__name__)

JsonResult = dict | list


def request_json(url: str, *, timeout: float = 10.0) -> JsonResult:
    logger.info("Request start: %s", url)

    try:
        res: Response = requests.get(
            url,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )
        _raise_for_status_with_log(res)
        data = _parse_json_with_log(res)
    except requests.RequestException as e:
        # 接続失敗・タイムアウト・HTTPError など、requests 系はここに集約
        logger.error("Request failed: %s", e.__class__.__name__)
        raise

    logger.info("Request success: type=%s", type(data).__name__)

    if isinstance(data, (dict, list)):
        logger.debug("json is %s.", type(data).__name__)
        return data

    raise RuntimeError("JSON is invalid.")


def _raise_for_status_with_log(res: Response) -> None:
    try:
        res.raise_for_status()
    except requests.HTTPError:
        logger.error(
            "HTTP Error: status_code=%d, reason=%s",
            res.status_code,
            res.reason,
        )
        raise


def _parse_json_with_log(res: Response):
    try:
        return res.json()
    except ValueError as e:
        ct = res.headers.get("Content-Type")
        logger.error("JSON parse failed. content-type=%s", ct)
        raise RuntimeError(f"JSON parse failed. content-type={ct}") from e
