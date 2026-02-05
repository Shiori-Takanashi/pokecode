# PHASE02：`request_html.py` の実装完成

**目的**: `request_html()` 関数を実装し、`request_json.py` と同等のエラーハンドリングを実現

**進捗**: 🟡 開発中

---

## 1. 要件分析

### 機能要件

`request_html()` は以下の動作を満たす必要がある：

1. **HTTPリクエスト送信**
   - URL に対して GET リクエストを送信
   - `Accept: text/html` ヘッダーを指定
   - タイムアウト設定可能（デフォルト: 10秒）

2. **エラーハンドリング**
   - HTTP ステータスエラー（4xx, 5xx）
   - リクエスト失敗（タイムアウト、接続エラー等）
   - Content-Type 検証（HTML として取得できるか確認）
   - 空レスポンス処理

3. **ログ出力**
   - リクエスト開始・完了・失敗を記録
   - エラー発生時は詳細情報を出力

4. **戻り値**
   - 成功時: HTML テキスト（`str`）
   - 失敗時: 例外を raise

### エラークラス設計

`request_json.py` のパターンを参考にする：

```python
class ContractViolationError(RuntimeError):
    """API 契約違反（HTML を返すはずなのに返さない等）"""

class InvalidContentTypeError(ContractViolationError):
    """Content-Type が HTML ではない"""

class EmptyResponseError(ContractViolationError):
    """レスポンスが空"""

# requests.RequestException は既に requests パッケージにある
```

---

## 2. 実装パターン（`request_json.py` との比較）

### request_json.py の構造

```python
def request_json(url: str, *, timeout: float = 10.0) -> JsonResult:
    logger.info("Request start: %s", url)
    try:
        res = requests.get(url, timeout=timeout, headers={"Accept": "application/json"})
        _raise_for_status_with_log(res, url=url)           # HTTP エラーチェック
        _ensure_json_content_type(res, url=url)            # Content-Type 検証
        data = _parse_json_with_log(res, url=url)          # データパース
        logger.debug("Request success: url=%s type=%s", url, type(data).__name__)
        return data
    except requests.RequestException:
        logger.error("Request failed: url=%s", url)
        raise
```

### request_html.py の実装パターン（対応版）

```python
def request_html(url: str, *, timeout: float = 10.0) -> HtmlResult:
    logger.info("Request start: %s", url)
    try:
        res = requests.get(url, timeout=timeout, headers={"Accept": "text/html"})
        _raise_for_status_with_log(res, url=url)           # HTTP エラーチェック
        _ensure_html_content_type(res, url=url)            # Content-Type 検証
        html = _extract_html_with_log(res, url=url)        # HTML 抽出
        logger.debug("Request success: url=%s len=%d", url, len(html))
        return html
    except requests.RequestException:
        logger.error("Request failed: url=%s", url)
        raise
```

---

## 3. 実装スケッチ

```python
# pokecode/request_html.py
import logging
from dataclasses import dataclass

import requests
from requests import Response

logger = logging.getLogger(__name__)

HtmlResult = str


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


def request_html(url: str, *, timeout: float = 10.0) -> HtmlResult:
    logger.info("Request start: %s", url)
    
    try:
        res = requests.get(
            url,
            timeout=timeout,
            headers={"Accept": "text/html"},
        )
        
        _raise_for_status_with_log(res, url=url)
        _ensure_html_content_type(res, url=url)
        html = _extract_html_with_log(res, url=url)
        
        logger.debug("Request success: url=%s len=%d", url, len(html))
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
        raise InvalidContentTypeError(f"Expected HTML Content-Type but got: {ct!r}")


def _extract_html_with_log(res: Response, *, url: str) -> HtmlResult:
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


def _looks_like_html_content_type(content_type: str | None) -> bool:
    """Content-Type が HTML らしいか判定"""
    if not content_type:
        return False
    ct_lower = content_type.lower()
    return "text/html" in ct_lower or "html" in ct_lower


def _build_context(
    res: Response, *, url: str, include_snippet: bool
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
```

---

## 4. 実装チェックリスト

- [ ] `request_html()` メイン関数の実装
- [ ] エラークラスの定義（3種類）
- [ ] `_raise_for_status_with_log()` ヘルパー
- [ ] `_ensure_html_content_type()` ヘルパー
- [ ] `_extract_html_with_log()` ヘルパー
- [ ] `_looks_like_html_content_type()` 判定関数
- [ ] `_build_context()` コンテキスト構築
- [ ] `_response_snippet()` スニペット生成

---

## 5. テスト計画（PHASE04で実施予定）

```python
# テストケース
def test_request_html_success():
    """正常な HTML レスポンスを取得"""
    # モック: status=200, content-type=text/html

def test_request_html_http_error():
    """HTTP エラー（404, 500等）が発生"""
    # モック: status=404

def test_request_html_invalid_content_type():
    """Content-Type が HTML ではない"""
    # モック: status=200, content-type=application/json

def test_request_html_empty_response():
    """レスポンスボディが空"""
    # モック: status=200, body=""

def test_request_html_timeout():
    """リクエストタイムアウト"""
    # モック: requests.Timeout

def test_request_html_connection_error():
    """接続エラー"""
    # モック: requests.ConnectionError
```

---

## 6. 実装前の検討事項

### Q: main.py で何をするのか？

**現在の code（request_html 版）**:
```python
def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")
    logger.info("Application Start.")
    
    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["localhost_html"]
        html = request_html(url=url)
        print(html)  # ← HTML をそのままプリントしている
```

**コメント化されていた code（request_json 版）**:
```python
try:
    data = load_config(PYPROJECT)
    url = data["tool"]["pokecode"]["local"]
    msg = request_json(url)
    logger.info("Response payload: %s", msg)
```

→ **理解が必要**: ローカルサーバーが何を返すのか？HTML と JSON のどちらなのか？

### Q: Content-Type チェックの厳密さ

`_looks_like_html_content_type()` の実装：
- `text/html`: 標準的な HTML
- `application/xhtml+xml`: XHTML
- `text/plain`: テキストとして返す HTML（緩い判定）

現在の実装では「html」を含むかどうかで判定している。これで問題ないか？

---

## 7. 次のステップ

✅ **PHASE02**: この実装を `request_html.py` に適用

📋 **PHASE03**: `main.py` の動作確認と、JSON リクエストの理解

---
