# 開発ロードマップと改善方針

## プロジェクト概要

**pokecode** は、HTTP リクエスト（HTML/JSON）を適切にハンドルし、環境に応じた設定を管理するための Python アプリケーションです。

### 現状（PHASE07 完了）

✅ **実装済み**
- `request_html()` - HTML 取得と詳細なエラーハンドリング
- `request_json()` - JSON 取得とパース
- 設定管理 - モジュールレベルの関数型 API
- ロギング設定 - Stream & File handlers
- 環境変数サポート - .env ファイル対応
- .gitignore 設定 - Python/IDE ファイル除外
- pyproject.toml - 依存関係管理

❌ **未実装**
- テストスイート (pytest) の本体コード
- 統合テスト
- CI/CD パイプライン
- API ドキュメント (Sphinx など)
- パフォーマンスプロファイリング
- セキュリティ監査

---

## 改善方針（推奨順）

### Level 1: 基盤整備（今後 2-3 PHASE）

#### PHASE08: テスト基盤の構築

**目的**: 品質保証メカニズムの構築

**実装内容**:
```
tests/
├── conftest.py               # 既存
├── test_config.py            # NEW
├── test_request_html.py      # NEW
├── test_request_json.py      # NEW
├── test_logconfig.py         # NEW
├── fixtures/                 # NEW
│   ├── sample_responses.py
│   └── mock_server.py
```

**チェックリスト**:
- [ ] `test_config.py`: 環境変数の動的取得をテスト
- [ ] `test_request_html.py`: 成功ケース、エラーケースをカバー
- [ ] `test_request_json.py`: 形式検証、パースエラーテスト
- [ ] Coverage 目標: 80% 以上
- [ ] `pytest --cov` で計測

**参考**:
```bash
# テスト実行例
pytest tests/ -v
pytest tests/ --cov=src/pokecode --cov-report=html
```

---

#### PHASE09: CI/CD パイプラインの実装

**目的**: 自動品質チェック、テスト自動実行

**実装内容** (.github/workflows/):
```yaml
# Python テスト
- pytest テスト実行
- mypy 型チェック
- Ruff リント・フォーマット
- Coverage レポート

# コード品質
- 未使用インポート検出
- 複雑度チェック
- セキュリティスキャン
```

**チェックリスト**:
- [ ] `.github/workflows/test.yml` を作成
- [ ] `pytest`, `mypy`, `ruff` を自動実行
- [ ] PR 時に自動実行
- [ ] Main ブランチへのマージ前にすべてパス

---

#### PHASE10: ドキュメント整備

**目的**: ユーザーと開発者向けドキュメント作成

**実装内容**:
```
.docs/
├── ARCHITECTURE.md           # システム構成
├── API.md                    # 関数・クラス仕様
├── CONFIGURATION.md          # 設定ガイド
├── TESTING.md                # テスト実行方法
├── CONTRIBUTING.md           # 開発貢献ガイド
└── TROUBLESHOOTING.md        # トラブルシューティング
```

**内容例**:
- モジュール構成図（Mermaid）
- 関数シグネチャ
- ユースケース
- トラブルシューティング集

---

### Level 2: 機能拡張（PHASE11-13）

#### PHASE11: 非同期リクエスト対応

**目的**: 複数リクエストの並列処理

**実装内容**:
```python
# 非同期バージョンのCreate API
async def request_html_async(url: str) -> HtmlResult:
    ...

async def request_json_async(url: str) -> JsonResult:
    ...

# 複数 URL の並列リクエスト
async def fetch_multiple(urls: list[str]) -> list[HtmlResult]:
    ...
```

**依存関係**: `aiohttp` または `httpx`

---

#### PHASE12: キャッシング機構

**目的**: 同一 URL への重複リクエストを削減

**実装内容**:
```python
# キャッシュデコレータ
@cached(ttl=3600)  # 1 時間キャッシュ
def request_html(url: str) -> HtmlResult:
    ...
```

**オプション**:
- メモリキャッシュ (dict)
- Redis キャッシュ
- ファイルベースキャッシュ

---

#### PHASE13: リトライロジック

**目的**: ネットワークエラー時の自動リトライ

**実装内容**:
```python
@retry(
    max_attempts=3,
    backoff=ExponentialBackoff(initial=1),
    exceptions=(ConnectionError, Timeout)
)
def request_html(url: str) -> HtmlResult:
    ...
```

---

### Level 3: 運用・最適化（PHASE14+）

#### PHASE14: ロギング・監視の強化

- 構造化ログ (JSON ログ)
- 外部ログサービス連携（CloudWatch, Datadog）
- メトリクス収集 (Prometheus)
- トレーシング対応 (OpenTelemetry)

#### PHASE15: セキュリティ対応

- 依存関係脆弱性スキャン (Dependabot)
- シークレット管理 (Vault など)
- SSL/TLS 設定
- 入力値検証の強化

#### PHASE16: パフォーマンス最適化

- リクエストタイムアウト最適化
- メモリ使用量プロファイリング
- CPU 使用率最適化
- 接続プーリング実装

---

## 開発ガイドライン

### コード品質基準

#### 1. 型チェック (mypy)

```bash
mypy src/pokecode --strict
```

**目標**: エラー = 0

#### 2. リント・フォーマット (Ruff)

```bash
ruff check src/pokecode
ruff format src/pokecode
```

#### 3. テストカバレッジ

```bash
pytest --cov=src/pokecode --cov-report=term-missing
```

**目標**: 80% 以上

#### 4. ドキュメント

- 全パブリック関数に docstring
- モジュール単位のモジュール docstring
- 複雑なロジックにはコメント

### コミットメッセージ規約

```
<type>: <subject>

<body>

<footer>
```

**type**:
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `chore`: 依存関係、設定など

**例**:
```
feat: Add async support to request_html

- Implement async/await pattern
- Add aiohttp dependency
- Backward compatible with sync version

Related-To: #42
```

---

## 各 PHASE の目的と対応ファイル

| PHASE | 目的 | 対応ファイル | 優先度 |
|-------|------|------------|--------|
| 01-05 | プロジェクト整理、request* 実装 | request_html.py, request_json.py | ✅ Done |
| 06 | 設定管理リファクタリング | config.py | ✅ Done |
| 07 | 関数型への統一 | config.py, loading.py | ✅ Done |
| 08 | テスト基盤 | tests/* | 🔴 High |
| 09 | CI/CD パイプライン | .github/workflows | 🔴 High |
| 10 | ドキュメント整備 | .docs/* | 🟡 Medium |
| 11 | 非同期対応 | request_html.py, request_json.py | 🟡 Medium |
| 12 | キャッシング | cache.py (NEW) | 🟢 Low |
| 13 | リトライロジック | retry.py (NEW) | 🟢 Low |
| 14+ | 運用・最適化 | - | 🟢 Low |

---

## プロジェクト構造の進化

現在（PHASE07）:
```
src/pokecode/
├── __init__.py
├── config.py              ← PHASE07: 関数型 API
├── getpath.py
├── loading.py
├── logconfig.py
├── main.py
├── request_html.py        ← PHASE02-05
├── request_json.py        ← PHASE02-05
```

目標（PHASE15）:
```
src/pokecode/
├── __init__.py
├── config.py              # 設定管理
├── getpath.py
├── loading.py
├── logconfig.py
├── monitoring.py          # メトリクス・トレーシング
├── security.py            # 認証・検証
├── request/               # NEW: リクエスト関連
│   ├── __init__.py
│   ├── html.py            # (request_html.py を移行)
│   ├── json.py            # (request_json.py を移行)
│   ├── async_.py          # PHASE11
│   ├── cache.py           # PHASE12
│   └── retry.py           # PHASE13
├── main.py
```

---

## よくある質問 (FAQ)

### Q1: どの PHASE から始めるべき？

**A**: PHASE08（テスト基盤）から。現在のコードの品質を保証するのが先。

### Q2: すべての PHASE を実装すべき？

**A**: いいえ。プロジェクトの要件に応じて選択してください。
- 小規模プロジェクト: PHASE07 で満足
- チーム開発: PHASE08-10 必須
- 本番運用: PHASE14-16 推奨

### Q3: PHASE の実装順序は変更可能？

**A**: Level 1 は順序を守ってください。Level 2 以降は並列実装可能。

### Q4: 既存ファイルへの影響は？

**A**: PHASE08-10 はテストとドキュメントのみなので既存コード改変なし。PHASE11 以降は必要に応じてリファクタリング。

### Q5: 依存関係の追加は？

**A**: PHASE ごとに新規依存関係を記載。`pyproject.toml` の `dependencies` へ追加。

---

## リソース

- [Python 标准库](https://docs.python.org/3/)
- [pytest Documentation](https://docs.pytest.org/)
- [Type hints - mypy](https://mypy-lang.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [12 Factor App](https://12factor.net/)
- [Semantic Versioning](https://semver.org/)

---

## 進捗トラッキング

```
# .docs/PROGRESS.md で定期更新
PHASE 07: ✅ 完了 (2026-02-05)
PHASE 08: 🔄 計画中
PHASE 09: ⏳ 予定中
...
```

最後のチェック: 各 PHASE 完了時に `git tag` でマイルストーンを記録

```bash
git tag PHASE07-complete-2026-02-05
git push origin PHASE07-complete-2026-02-05
```
