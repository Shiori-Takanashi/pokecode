import logging

import requests
from requests import Response

logger = logging.getLogger(__name__)

HtmlResult = str | None


def request_html(url: str, *, timeout: float = 10.0) -> HtmlResult:
    logger.info("Request start: %s", url)

    # 試行
    try:
        res: Response = requests.get(
            url,
            timeout=timeout,
            headers={"Accept": "text/html"},
        )
        raise_for_status_with_log(res)
        data = res.text

    # 例外
    except requests.RequestException as e:
        logger.error("Request failed: %s", e.__class__.__name__)
        raise

    logger.info("Request success: type=%s", type(data).__name__)

    return data


def raise_for_status_with_log(res: Response) -> None:
    try:
        res.raise_for_status()
    except requests.HTTPError:
        logger.error(
            "HTTP Error: status_code=%d, reason=%s",
            res.status_code,
            res.reason,
        )
        raise


def parse_html_with_log(res: Response) -> HtmlResult:
    try:
        html_text = res.text
        if not html_text:
            ct = res.headers.get("Content-Type")
            logger.error("HTML parse failed: empty response. content-type=%s", ct)
            raise RuntimeError(f"HTML parse failed: empty response. content-type={ct}")
        return html_text
    except Exception as e:
        ct = res.headers.get("Content-Type")
        logger.error("HTML parse failed. content-type=%s", ct)
        raise RuntimeError(f"HTML parse failed. content-type={ct}") from e
