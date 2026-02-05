# PHASE05：統合テストと最終整理

**目的**: PHASE01-04 の変更を統合的に検証し、プロジェクトを安定化させる

**進捗**: 🟡 開発中

---

## 1. これまでの変更内容

### PHASE02：request_html.py の実装

✅ **完了**:
- `request_html()` 関数を完全実装
- エラークラスを 3 種類定義（ContractViolationError, InvalidContentTypeError, EmptyResponseError）
- ロギング機能充実
- `request_json.py` と同等のエラーハンドリング

### PHASE03：main.py の整理

✅ **完了**:
- コメント化されたコードを削除
- `request_html()` を正しく呼び出し
- HTML ページ取得後、その長さをログ出力

### PHASE04：ログシステムの検証

⏳ **予定**:
- StreamHandler 重複チェック テストの実装
- ログシステムの妥当性確認

---

## 2. 統合テスト計画

### 2.1 ユニットテスト（既存）

```bash
# 既存テストの実行
pytest tests/test_logging.py -v
```

### 2.2 request_html() のテスト

**テストファイル**: `tests/test_request_html.py`（新規作成予定）

```python
import pytest
from unittest.mock import Mock, patch
from pokecode.request_html import (
    request_html,
    InvalidContentTypeError,
    EmptyResponseError,
)


def test_request_html_success():
    """正常な HTML レスポンスを取得"""
    with patch('pokecode.request_html.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        html = request_html("http://localhost:5000")
        assert "<html>" in html
        assert len(html) > 0


def test_request_html_invalid_content_type():
    """Content-Type が JSON の場合"""
    with patch('pokecode.request_html.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"key": "value"}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(InvalidContentTypeError):
            request_html("http://localhost:5000")


def test_request_html_empty_response():
    """レスポンスが空の場合"""
    with patch('pokecode.request_html.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = ""  # 空
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(EmptyResponseError):
            request_html("http://localhost:5000")


def test_request_html_http_error():
    """HTTP 404 エラーの場合"""
    with patch('pokecode.request_html.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = "<html>404</html>"
        mock_response.raise_for_status = Mock(
            side_effect=Exception("404 Not Found")
        )
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            request_html("http://localhost:5000/notfound")
```

### 2.3 main() のエンドツーエンドテスト

**テストファイル**: `tests/test_main.py`（新規または拡張）

```python
import pytest
from unittest.mock import patch, Mock
from pokecode.main import main


def test_main_with_html_success(capsys):
    """main() が正常に HTML を取得して実行終了"""
    mock_html = "<html><body>Pokemon</body></html>"
    
    with patch('pokecode.main.load_config') as mock_config, \
         patch('pokecode.main.request_html') as mock_request:
        
        mock_config.return_value = {
            "tool": {"pokecode": {"localhost_html": "http://localhost:5000"}}
        }
        mock_request.return_value = mock_html
        
        # main() を実行（例外が出ないことを確認）
        try:
            main()
        except SystemExit:
            pytest.fail("main() should not raise SystemExit on success")


def test_main_with_request_failure():
    """main() が request_html の例外をキャッチして終了"""
    with patch('pokecode.main.load_config') as mock_config, \
         patch('pokecode.main.request_html') as mock_request, \
         patch('sys.exit') as mock_exit:
        
        mock_config.return_value = {
            "tool": {"pokecode": {"localhost_html": "http://localhost:5000"}}
        }
        mock_request.side_effect = ConnectionError("Connection failed")
        
        main()
        
        # sys.exit(1) が呼ばれたことを確認
        mock_exit.assert_called_once_with(1)
```

### 2.4 ログシステムのテスト

**テストファイル**: `tests/test_logging_integration.py`（新規）

```python
import logging
from pokecode.logconfig import setup_logging


def test_setup_logging_no_duplication():
    """複数回の setup_logging() で handler が増殖しないか"""
    logger = logging.getLogger("test_integration")
    
    for i in range(3):
        setup_logging(logger=logger, level="INFO")
        stream_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) == 1, \
            f"After call {i+1}: expected 1 StreamHandler, got {len(stream_handlers)}"


def test_setup_logging_formatter_applied():
    """setup_logging() で formatter が正しく設定されるか"""
    logger = logging.getLogger("test_formatter")
    setup_logging(logger=logger, level="INFO")
    
    stream_handlers = [
        h for h in logger.handlers
        if isinstance(h, logging.StreamHandler)
    ]
    
    assert len(stream_handlers) == 1
    handler = stream_handlers[0]
    assert handler.formatter is not None
    assert "%(asctime)s" in handler.formatter._fmt
```

---

## 3. 統合テストの実行タイプ

### 3.1 単純実行

```bash
# すべてのテストを実行
pytest tests/ -v

# 特定のテストだけ
pytest tests/test_request_html.py -v
pytest tests/test_main.py -v
pytest tests/test_logging_integration.py -v
```

### 3.2 詳細ログ付き実行

```bash
# `-s` オプションで stdout/stderr をキャプチャしない（ログ見える）
pytest tests/test_main.py -v -s
```

### 3.3 カバレッジ確認

```bash
# coverage をインストール
pip install coverage pytest-cov

# テストカバレッジを測定
pytest tests/ --cov=pokecode --cov-report=html
```

---

## 4. 手動テスト：ローカルサーバーでの動作確認

### 4.1 Flask サーバー起動

```bash
cd /home/tani09/snk-projects/pokecode

# Flask アプリを起動
python -m flask --app server.app run
```

### 4.2 別ターミナルで main.py 実行

```bash
cd /home/tani09/snk-projects/pokecode

# main.py を実行（request_html で localhost:5000 にリクエスト）
python -m pokecode

# または
python -c "from pokecode.main import main; main()"
```

**期待される出力**:
```
[時刻] [INFO] pokecode: Application Start.
[時刻] [INFO] pokecode: Request start: http://localhost:5000
[時刻] [DEBUG] pokecode: Request success: url=http://localhost:5000 len=XXX
[時刻] [INFO] pokecode: HTML retrieved: XXX characters
[時刻] [INFO] pokecode: Application End.
```

### 4.3 request_html() を直接テスト

```bash
python -m flask --app server.app run &  # バックグラウンド起動
sleep 2

python -c "
from pokecode.request_html import request_html
html = request_html('http://localhost:5000')
print(f'Success! Retrieved {len(html)} characters')
print(f'Content preview: {html[:200]}')
"
```

---

## 5. チェックリスト

### 実装完了度

- [x] PHASE02：request_html.py 実装完了
- [x] PHASE03：main.py 整理完了
- [ ] PHASE04：ログシステムテスト（予定）
- [ ] PHASE05：統合テスト実行

### テスト実装状況

- [ ] tests/test_request_html.py（新規）
- [ ] tests/test_main.py（新規または拡張）
- [ ] tests/test_logging_integration.py（新規）

### ドキュメント整理

- [x] .docs/phase/PHASE01.md（状況概要）
- [x] .docs/phase/PHASE02.md（request_html 実装案）
- [x] .docs/phase/PHASE03.md（リクエスト処理統合）
- [x] .docs/phase/PHASE04.md（ログシステム検証）
- [x] .docs/phase/PHASE05.md（統合テスト計画）

---

## 6. Git コミット計画

各 PHASE の完了後にコミットする：

```bash
# PHASE02: request_html.py 実装完了
git add src/pokecode/request_html.py .docs/phase/PHASE02.md
git commit -m "PHASE02: request_html() を完全実装"

# PHASE03: main.py 整理完了
git add src/pokecode/main.py .docs/phase/PHASE03.md
git commit -m "PHASE03: main.py を整理し request_html を正しく統合"

# PHASE04: ログシステム検証テスト
git add tests/test_logging_integration.py .docs/phase/PHASE04.md
git commit -m "PHASE04: ログシステムの StreamHandler 問題を検証"

# PHASE05: 統合テスト完了
git add tests/test_request_html.py tests/test_main.py .docs/phase/PHASE05.md
git commit -m "PHASE05: 統合テスト完了、プロジェクト安定化"
```

---

## 7. 今後の改善項目（今仕事ではなく、フューチャー）

### 短期（PHASE06）

- [ ] request_json() の使用例実装（main.py の オプション B または C）
- [ ] Flask サーバーのエラーハンドリング強化
- [ ] ログ出力のより詳細な情報

### 中期（PHASE07+）

- [ ] QR コード生成機能（server/create_qr.py）の統合
- [ ] ポケモン情報の HTML スクレイピング実装
- [ ] データベース連携（必要なら）

### 長期

- [ ] CI/CD パイプライン構築（GitHub Actions）
- [ ] Docker コンテナ化
- [ ] API ドキュメント生成（OpenAPI等）

---

## 8. まとめ

### 現在の状態
- ✅ `request_html()` が実装された
- ✅ `main.py` が整理された
- ✅ ドキュメント化が完了
- ⏳ テストが必要

### 次の即座のアクション
1. テストコードの実装
2. ローカルサーバーでの手動テスト
3. Git コミット・push

### 最終目標
プロジェクトを安定動作させ、以降の拡張開発がしやすい状態にする

---
