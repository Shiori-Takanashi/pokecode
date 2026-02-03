import logging
from dataclasses import dataclass

import requests
from requests import Response

logger = logging.getLogger(__name__)

JsonResult = dict | list


@dataclass(frozen=True)
class ResponseContext:
    url: str
    status_code: int | None
    reason: str | None
    content_type: str | None
    snippet: str | None


class ContractViolationError(RuntimeError):
    """API 契約違反（JSON を返すはずなのに返さない等）"""


class InvalidContentTypeError(ContractViolationError):
    """Content-Type が JSON ではない"""


class InvalidJSONError(ContractViolationError):
    """JSON としてパースできない"""


class InvalidJSONTypeError(ContractViolationError):
    """JSON ではあるが dict/list ではない"""


def request_json(url: str, *, timeout: float = 10.0) -> JsonResult:
    logger.info("Request start: %s", url)

    try:
        res = requests.get(
            url,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

        _raise_for_status_with_log(res, url=url)
        _ensure_json_content_type(res, url=url)

        data = _parse_json_with_log(res, url=url)

        logger.debug("Request success: url=%s type=%s", url, type(data).__name__)
        return data

    except requests.RequestException:
        logger.error("Request failed: url=%s", url)
        raise


def _raise_for_status_with_log(res: Response, *, url: str) -> None:
    try:
        res.raise_for_status()
    except requests.HTTPError:
        ctx = _build_context(res, url=url, include_snippet=True)
        logger.error(
            "HTTP error: url=%s status=%s reason=%s content-type=%s snippet=%s",
            ctx.url,
            ctx.status_code,
            ctx.reason,
            ctx.content_type,
            ctx.snippet,
        )
        raise


def _ensure_json_content_type(res: Response, *, url: str) -> None:
    ct = res.headers.get("Content-Type")
    if not _looks_like_json_content_type(ct):
        ctx = _build_context(res, url=url, include_snippet=True)
        logger.error(
            "Invalid content-type: url=%s status=%s content-type=%s snippet=%s",
            ctx.url,
            ctx.status_code,
            ctx.content_type,
            ctx.snippet,
        )
        raise InvalidContentTypeError(f"Expected JSON Content-Type but got: {ct!r}")


def _parse_json_with_log(res: Response, *, url: str) -> JsonResult:
    try:
        data = res.json()
    except ValueError as e:
        ctx = _build_context(res, url=url, include_snippet=True)
        logger.error(
            "JSON parse failed: url=%s status=%s content-type=%s snippet=%s err=%s",
            ctx.url,
            ctx.status_code,
            ctx.content_type,
            ctx.snippet,
            str(e),
        )
        raise InvalidJSONError("Response body is not valid JSON") from e

    if isinstance(data, (dict, list)):
        return data

    logger.error("Invalid JSON type: url=%s type=%s", url, type(data).__name__)
    raise InvalidJSONTypeError(f"Expected dict or list but got: {type(data).__name__}")


def _looks_like_json_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    return "json" in content_type.lower()


def _build_context(
    res: Response, *, url: str, include_snippet: bool
) -> ResponseContext:
    status_code = getattr(res, "status_code", None)
    reason = getattr(res, "reason", None)
    content_type = res.headers.get("Content-Type")

    snippet = None
    if include_snippet:
        snippet = _response_snippet(res, limit_chars=400)

    return ResponseContext(
        url=url,
        status_code=status_code,
        reason=reason,
        content_type=content_type,
        snippet=snippet,
    )


def _response_snippet(res: Response, *, limit_chars: int) -> str:
    try:
        text = res.text
    except Exception:
        return "<unavailable>"

    compact = " ".join(text.replace("\t", " ").splitlines())
    if len(compact) > limit_chars:
        return compact[:limit_chars] + "…"
    return compact
