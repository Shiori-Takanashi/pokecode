import logging
from dataclasses import dataclass

import requests
from requests import Response

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResponseContext:
    url: str
    status_code: int | None
    reason: str | None
    content_type: str | None
    snippet: str | None


class ContractViolationError(RuntimeError):
    """API 契約違反（HTML を返すはずなのに返さない等）"""


class InvalidContentTypeError(ContractViolationError):
    """Content-Type が HTML ではない"""


class EmptyResponseError(ContractViolationError):
    """レスポンスが空"""


def request_html(url: str, *, timeout: float = 30.0) -> str:
    logger.info("Request start: %s", url)

    try:
        res = requests.get(
            url,
            timeout=(5.0, timeout),
            headers={
                "Accept": "text/html",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        )

        _raise_for_status_with_log(res, url=url)
        _ensure_html_content_type(res, url=url)
        html = _extract_html_with_log(res, url=url)

        logger.debug(
            "Request success: url=%s len=%d",
            url,
            len(html),
        )
        return html

    except requests.RequestException:
        logger.error("Request failed: url=%s", url)
        raise


def _raise_for_status_with_log(res: Response, *, url: str) -> None:
    """HTTP ステータスエラーをチェック"""
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


def _ensure_html_content_type(res: Response, *, url: str) -> None:
    """Content-Type が HTML であることを確認"""
    ct = res.headers.get("Content-Type")
    if not _looks_like_html_content_type(ct):
        ctx = _build_context(res, url=url, include_snippet=True)
        logger.error(
            "Invalid content-type: url=%s status=%s content-type=%s snippet=%s",
            ctx.url,
            ctx.status_code,
            ctx.content_type,
            ctx.snippet,
        )
        raise InvalidContentTypeError(
            f"Expected HTML Content-Type but got: {ct!r}"
        )


def _extract_html_with_log(res: Response, *, url: str) -> str:
    """HTML テキストを抽出"""
    html = res.text

    if not html:
        ctx = _build_context(res, url=url, include_snippet=False)
        logger.error(
            "Empty response: url=%s status=%s content-type=%s",
            ctx.url,
            ctx.status_code,
            ctx.content_type,
        )
        raise EmptyResponseError("Response body is empty")

    return html


def _looks_like_html_content_type(
    content_type: str | None,
) -> bool:
    """Content-Type が HTML らしいか判定"""
    if not content_type:
        return False
    ct_lower = content_type.lower()
    return "text/html" in ct_lower or "html" in ct_lower


def _build_context(
    res: Response,
    *,
    url: str,
    include_snippet: bool,
) -> ResponseContext:
    """レスポンスコンテキストを構築"""
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
    """レスポンスボディのスニペットを生成"""
    try:
        text = res.text
    except Exception:
        return "<unavailable>"

    compact = " ".join(text.replace("\t", " ").splitlines())
    if len(compact) > limit_chars:
        return compact[:limit_chars] + "…"
    return compact
