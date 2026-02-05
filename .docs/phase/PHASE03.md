# PHASE03：リクエスト処理の統合理解と main.py の整理

**目的**: `request_html()` と `request_json()` の使い分けを明確化し、`main.py` を整理

**進捗**: 🟡 開発中

---

## 1. 問題整理：「requestのjsonを未理解。」

### コミットメッセージの背景

最新のコミット `07a9383` のメッセージ: **"requestのjsonを未理解。"**

これは、以下の混乱を示唆している：

1. **`request_json()` の実装は完了しているが、何を返すべきなのか不明確**
2. **`main.py` で `request_html` を使用している理由が不明確**
3. **ローカルサーバー (`localhost:5000`) が何を返すのか不明確**
4. **コード内にコメント化された旧実装が存在し、混乱を招いている**

---

## 2. 現在の main.py の動作フロー

### 現在の code（request_html 版）

```python
def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")
    logger.info("Application Start.")
    
    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["localhost_html"]
        html = request_html(url=url)
        print(html)  # ← HTML をそのままプリント
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
    finally:
        logger.info("Application End.")
```

**問題**: `print(html)` だけなので、HTML をどう処理するのか不明確

### コメント化された code（request_json 版）

```python
try:
    data = load_config(PYPROJECT)
    url = data["tool"]["pokecode"]["local"]  # ← localhost_html ではなく "local"
    msg = request_json(url)
    logger.info("Response payload: %s", msg)  # ← JSON を logger に出力
except Exception:
    logger.exception("Unhandled exception")
```

**問題**: `localhost_html` と `local` の違いが不明確

---

## 3. ローカルサーバーの仕様確認（server/app.py 分析）

まず `server/app.py` を確認して、何を返すサーバーか理解する必要がある。

### Flask サーバーの役割

**推測**:
- `/` → HTML ページを返す
- `/json` → JSON データを返す

**確認項目**:
- [ ] `server/app.py` の実装内容
- [ ] エンドポイント定義
- [ ] レスポンス形式

---

## 4. `request_html()` vs `request_json()` の使い分け

### 機能比較表

| 機能 | request_html | request_json | 用途 |
|------|--------------|--------------|------|
| **リクエストヘッダー** | `Accept: text/html` | `Accept: application/json` | コンテンツネゴシエーション |
| **レスポンス形式** | 文字列（HTML） | dict/list（JSON） | メソッドの戻り値型 |
| **Content-Type チェック** | `text/html` 検証 | `application/json` 検証 | 契約確認 |
| **パース処理** | `res.text` 取得のみ | `res.json()` でパース | データ構造 |
| **エラー種別** | `InvalidContentTypeError` `EmptyResponseError` | `InvalidContentTypeError` `InvalidJSONError` `InvalidJSONTypeError` | 問題点の詳細化 |
| **ログ出力** | HTML 長さ | JSON 型 | 診断情報 |

### 使い分けのルール

1. **HTML を取得したい**
   - ↓ `request_html()` を使用
   - 例: `http://localhost:5000/` → HTML ページ取得
   - API が `text/html` を明示的に返す場合

2. **JSON を取得したい**
   - ↓ `request_json()` を使用
   - 例: `http://localhost:5000/json` → JSON データ取得
   - API が `application/json` を明示的に返す場合

3. **判定が必要な場合**
   - Content-Type の値を確認
   - `text/html` なら `request_html()`
   - `application/json` なら `request_json()`

---

## 5. 推奨される main.py の構造

### オプション A：HTML 処理に特化

**目的**: ポケモン情報の HTML ページをスクレイピング

```python
from bs4 import BeautifulSoup

def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")
    logger.info("Application Start.")
    
    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["localhost_html"]
        html = request_html(url=url)
        
        # HTML をパース
        soup = BeautifulSoup(html, "html.parser")
        # ... ポケモン情報を抽出 ...
        logger.info("Scraping completed")
        
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
    finally:
        logger.info("Application End.")
```

### オプション B：JSON 処理に特化

**目的**: ポケモン API から JSON データ取得

```python
def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")
    logger.info("Application Start.")
    
    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["localhost_json"]
        json_data = request_json(url)
        
        # JSON データを処理
        logger.info("Response type: %s", type(json_data).__name__)
        logger.info("Response: %s", json_data)
        
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
    finally:
        logger.info("Application End.")
```

### オプション C：両者の柔軟な処理

**目的**: Content-Type に応じた処理

```python
from pokecode.request_html import request_html
from pokecode.request_json import request_json

def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")
    logger.info("Application Start.")
    
    try:
        data = load_config(PYPROJECT)
        url = data["tool"]["pokecode"]["localhost"]  # generic URL
        
        # server の応答を確認
        import requests
        res = requests.head(url)
        ct = res.headers.get("Content-Type", "").lower()
        
        if "json" in ct:
            json_data = request_json(url)
            logger.info("Received JSON: %s", json_data)
        elif "html" in ct:
            html = request_html(url)
            logger.info("Received HTML of length: %d", len(html))
        else:
            raise ValueError(f"Unexpected content-type: {ct}")
        
    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)
    finally:
        logger.info("Application End.")
```

---

## 6. main.py の現在の問題点と修正案

### 問題点 1：コメント化されたコードが残っている

**現在**:
```python
# def main() -> None:
#     logger = logging.getLogger("pokecode")
#     ...
```

**修正**: 不要なコメント化コードは削除する

### 問題点 2：HTML を print() で出力している

**現在**:
```python
html = request_html(url=url)
print(html)  # 何もしないただの出力
```

**修正案**:
- HTML をファイルに保存
- HTML をパースして情報抽出
- HTML の長さをログ出力
- いずれかの処理を追加

### 問題点 3：`localhost_html` を hardcode している

**現在**:
```python
url = data["tool"]["pokecode"]["localhost_html"]
```

**改善案**:
- 環境変数で URL を指定可能にする
- コマンドラインオプションで HTML/JSON を切り替え
- pyproject.toml で複数の URL を定義

---

## 7. 実装チェックリスト（PHASE03）

- [ ] `server/app.py` の仕様を確認
- [ ] `localhost_html` と `localhost_json` のエンドポイントを確認
- [ ] `main.py` のコメント化コードを削除
- [ ] `main.py` で HTML/JSON の処理を追加実装
- [ ] テスト実行して動作確認
- [ ] Git コミット

---

## 8. テスト計画

### ローカルサーバー起動

```bash
# server/app.py を実行
python -m flask --app server.app run
```

### request_html() のテスト

```bash
python -c "
from pokecode.request_html import request_html
html = request_html('http://localhost:5000')
print(f'Success: {len(html)} characters')
"
```

### request_json() のテスト

```bash
python -c "
from pokecode.request_json import request_json
json_data = request_json('http://localhost:5000/json')
print(f'Success: {json_data}')
"
```

### main.py の実行テスト

```bash
python -m pokecode
```

---

## 9. 次のステップ

✅ **PHASE03**: request_html と request_json の理解を深める

📋 **PHASE04**: ログシステムの StreamHandler 問題検証

📋 **PHASE05**: 全体統合テストと最終整理

---
