# プロジェクトステータス（2026-02-07）

## 概要

**pokecode** は HTTP リクエスト（HTML）を適切にハンドルし、国別フレンドコードを収集・翻訳するための Python プロジェクトです。設定管理、ロギング、エラーハンドリング、翻訳サービスが統合されています。

---

## 現在のフェーズ

🎯 **PHASE08 完了** - スクレイピング機能の統合と翻訳サービスの拡張

```
PHASE01-05: ✅ 実装完了（request_html, request_json）
PHASE06:    ✅ 実装完了（設定管理リファクタリング）
PHASE07:    ✅ 実装完了（関数型 API 統一）
PHASE08:    ✅ 実装完了（スクレイピング統合・翻訳拡張）
PHASE09:    🔴 次のフェーズ（テスト基盤・パフォーマンス改善）
```

---

## 実装済み機能

### 1. HTTP リクエスト処理

| 機能 | 説明 | ファイル |
|------|------|--------|
| `request_html()` | HTML 取得（エラーハンドリング付き） | [request_html.py](../src/pokecode/request_html.py) |

**特徴**:
- 詳細なエラーメッセージ
- Content-Type 検証
- タイムアウト設定
- 構造化ロギング

**使用例**:
```python
from pokecode.request_html import request_html

# HTML 取得
html = request_html("https://example.com")
```

---

### 2. スクレイピング機能

| 機能 | 説明 | ファイル |
|------|------|--------|
| HTML解析 | BeautifulSoup による解析 | [scraping.py](../src/pokecode/scraping.py) |
| 国リスト抽出 | 国名とISO Alpha-3コード抽出 | scraping.py |
| フレンドコード抽出 | トレーナー情報から抽出 | scraping.py |

**使用例**:
```python
from pokecode.scraping import (
    make_soup, scrape_html, scrape_cards_from_html,
    scrape_correct_card, scrape_trainers,
    scrape_friend_code_from_trainer
)

soup = make_soup(html)
html_tag = scrape_html(soup)
cards = scrape_cards_from_html(html_tag)
card = scrape_correct_card(cards, "📱 Friend Codes")
trainers = scrape_trainers(card)
codes = [scrape_friend_code_from_trainer(t) for t in trainers]
```

---

### 3. 翻訳サービス

| 機能 | 説明 | ファイル |
|------|------|--------|
| 国名翻訳 | OpenAI APIによる日本語翻訳 | [translation.py](../src/pokecode/translation.py) |
| キャッシュ機能 | 翻訳結果をローカルキャッシュ | [cache.py](../src/pokecode/cache.py) |
| バッチ処理 | 複数国名を効率的に翻訳 | translation.py |

**使用例**:
```python
from pokecode.translation import TranslationService

ts = TranslationService()
translated = ts.translate_countries_batch(
    countries=data,
    ignore_cache=False,
    batch_size=10,
)
```

---

### 4. URL構築

| 機能 | 説明 | ファイル |
|------|------|--------|
| 動的URL生成 | 国コードからURLを構築 | [url_builder.py](../src/pokecode/url_builder.py) |
| バリデーション | 国コードの検証 | url_builder.py |

**使用例**:
```python
from pokecode.url_builder import build_url_with_code

url = build_url_with_code(code="JPN")
# => "https://example.com/?country=JPN"
```

---

### 5. 設定管理

| 機能 | 説明 | ファイル |
|------|------|--------|
| 環境変数対応 | `POKECODE_*` 環境変数で設定可能 | [config.py](../src/pokecode/config.py) |
| `.env` ファイル対応 | `.env.local` / `.env` をサポート | config.py |
| 型安全 | `mypy --strict` でエラー 0 | config.py |
| 動的取得 | 実行時に値を評価 | config.py |

**設定取得**:
```python
from pokecode.config import ConfigGetter

cg = ConfigGetter()
port = cg.get_port()  # 5000
host = cg.get_host()  # 127.0.0.1
log_dir = cg.get_log_dir()  # logs
domain = cg.get_domain()  # 環境変数 DOMAIN から取得
```

**優先順位**:
```
環境変数 > .env.local > .env > デフォルト値
```

---

### 6. ロギング

| 機能 | 説明 | ファイル |
|------|------|--------|
| ストリームログ | コンソール出力 | [logconfig.py](../src/pokecode/logconfig.py) |
| ファイルログ | ファイル出力（ローテーション対応） | logconfig.py |
| ログレベル設定 | DEBUG, INFO, WARNING など | logconfig.py |

**使用例**:
```python
import logging
from pokecode.logconfig import setup_logging

logger = logging.getLogger(__name__)
setup_logging(logger=logger, level="INFO")

logger.info("メッセージ")
```

---

### 7. プロジェクト構成

```
pokecode/
├── .docs/
│   ├── phase/
│   │   ├── PHASE01.md
│   │   ├── PHASE02.md
│   │   ├── ...
│   │   └── PHASE07.md
│   ├── CONFIG_BEST_PRACTICES.md
│   ├── DEVELOPMENT_ROADMAP.md
│   ├── CONTRIBUTION_GUIDE.md
│   └── (このファイル)
│
├── src/pokecode/
│   ├── __init__.py
│   ├── config.py              # ✅ 設定管理（関数型）
│   ├── getpath.py             # プロジェクトパス検出
│   ├── loading.py             # TOML 読み込み
│   ├── logconfig.py           # ロギング設定
│   ├── main.py                # エントリーポイント
│   ├── request_html.py        # ✅ HTML 取得
│   ├── request_json.py        # ✅ JSON 取得
│   └── __pycache__/
│
├── tests/
│   ├── conftest.py            # pytest設定
│   ├── test_logging.py        # ロギングテスト
│   └── (PHASE08 で拡張予定)
│
├── server/
│   ├── app.py                 # Flask アプリ（テスト用）
│   ├── create_qr.py
│   ├── paths.py
│   ├── static/
│   └── templates/
│
├── .env.example               # 環境変数テンプレート
├── .gitignore                 # Git除外設定
├── .github/
│   └── workflows/             # (PHASE09 で追加予定)
├── Makefile                   # コマンド集
├── pyproject.toml             # 依存関係
└── README.md
```

---

## 品質指標（PHASE07 現在）

| 指標 | 目標値 | 現状 | 状態 |
|------|--------|------|------|
| Pylance エラー | 0 | 0 | ✅ |
| mypy エラー | 0（--strict） | 0 | ✅ |
| Ruff エラー | 0 | 0 | ✅ |
| テストカバレッジ | >= 80% | 計測中 | 📊 |
| ドキュメント | 全関数に docstring | 進行中 | 🟡 |

---

## 依存関係

### 主要パッケージ

```
beautifulsoup4>=4.14.3  # HTML パース（未使用[PHASE08以降]）
flask>=3.1.2            # テストサーバー
pillow>=12.1.0          # 画像処理
requests>=2.32.5        # HTTP リクエスト
python-dotenv>=1.0.0    # .env 対応
qrcode>=8.2             # QR コード生成
```

### 開発パッケージ

```
mypy>=1.19.1            # 型チェック
pytest>=9.0.2           # テストフレームワーク
ruff>=0.1.0             # リント・フォーマット（CI に追加予定）
```

---

## 次のステップ（推奨順）

### PHASE08: テスト基盤構築（🔴 High Priority）

**目的**: 品質保証メカニズムの構築

**実装内容**:
- `test_config.py` - 環境変数の動的取得
- `test_request_html.py` - 各エラーケース
- `test_request_json.py` - パース検証
- `test_logconfig.py` - ロギング設定

**所要時間**: 2-3 日

**実装ガイド**: [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) の PHASE08 セクション

---

### PHASE09: CI/CD パイプライン（🔴 High Priority）

**目的**: 自動品質チェック、テスト自動実行

**実装内容**:
- `.github/workflows/test.yml` を作成
- pytest, mypy, ruff を自動実行
- PR マージ前にチェック

**所要時間**: 1 日

---

### PHASE10: ドキュメント整備（🟡 Medium Priority）

**目的**: ユーザー・開発者向けドキュメント完成

**実装内容**:
- ARCHITECTURE.md（システム構成図）
- API.md（関数リファレンス）
- TESTING.md（テスト実行ガイド）

**所要時間**: 1-2 日

---

## クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/pokecode.git
cd pokecode

# 仮想環境作成
python3 -m venv .venv
source .venv/bin/activate

# インストール
pip install -e .
```

### 使用例

```python
from pokecode.request_html import request_html
from pokecode import config

# HTML を取得
html = request_html(config.get_local_html_url())

print(f"Retrieved {len(html)} bytes")
```

### テスト実行

```bash
pytest tests/ -v
```

### ロギング有効化

```python
import logging
from pokecode.logconfig import setup_logging

logger = logging.getLogger("pokecode")
setup_logging(logger=logger, level="DEBUG")
```

---

## 環境変数設定

### .env.local の作成（ローカル開発用）

```ini
# .env.local
POKECODE_LOG_DIR=logs
POKECODE_LOG_FILE=app.log
POKECODE_HOST=127.0.0.1
POKECODE_PORT=5000
POKECODE_LOCAL_HTML_URL=http://localhost:5000
POKECODE_LOCAL_JSON_URL=http://localhost:5000/json
```

### 環境変数で上書き

```bash
export POKECODE_PORT=8080
export POKECODE_HOST=0.0.0.0
python -m pokecode.main
```

---

## コードの状態

### 健全なコード

✅ **request_html.py**
- エラーハンドリング完全
- ロギング統合
- 型ヒント完全

✅ **request_json.py**
- エラーハンドリング完全
- JSON 検証完全
- 型ヒント完全

✅ **config.py**
- 型安全（mypy --strict OK）
- 環境変数対応
- シンプルで保守性高い

### 改善が必要な部分

🟡 **testing**
- テストスイートが最小限
- カバレッジ不明
- PHASE08 で拡張

🟡 **CI/CD**
- GitHub Actions 未設定
- PHASE09 で実装

---

## コントリビューション

新機能や修正を追加したい場合は、[CONTRIBUTION_GUIDE.md](./CONTRIBUTION_GUIDE.md) を参照してください。

**基本フロー**:
1. テストを書く（TDD）
2. 実装
3. `mypy`, `ruff` でチェック
4. コミット（Conventional Commits）

---

## よくある質問

### Q: このプロジェクトの用途は？

A: HTTP リクエスト（HTML/JSON）を処理する際の定型コードを提供します。エラーハンドリング、ロギング、設定管理が統合されています。

### Q: すぐに本番環境で使える？

A: テストスイートが最小限なので、PHASE08 完了後の使用をお勧めします。

### Q: どの Python バージョンが必要？

A: Python 3.14 以上（pyproject.toml で指定）

### Q: 非同期リクエストは対応？

A: PHASE11 で実装予定

---

## リソース

- [開発ロードマップ](./DEVELOPMENT_ROADMAP.md) - 全体計画
- [貢献ガイド](./CONTRIBUTION_GUIDE.md) - 開発方法
- [設定ベストプラクティス](./CONFIG_BEST_PRACTICES.md) - 設定管理の詳説
- [PHASE ドキュメント](./phase/) - 各段階の詳細

---

## サポート

質問やバグ報告は GitHub Issues を利用してください。

```bash
# または開発チーム宛にメール
# your-email@example.com
```

---

**最終更新**: 2026-02-05
**メンテナー**: Development Team
**ステータス**: 🟡 Active Development
