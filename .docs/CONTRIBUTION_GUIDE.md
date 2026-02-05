# 開発プロセスガイド

## 開発フロー（推奨）

### ステップ 1: 要件を確認

PHASE ごとに目的・成果物・チェックリストを確認。

```bash
# PHASE ドキュメントを読む
cat .docs/phase/PHASE0X.md
```

---

### ステップ 2: テストから始める (TDD)

**重要**: 実装 **前に** テストを書きましょう。

```bash
# テストファイルを作成
touch tests/test_new_feature.py
```

```python
# tests/test_new_feature.py
def test_new_feature_success():
    """正常系をテスト"""
    result = new_feature()
    assert result == expected_value

def test_new_feature_error():
    """エラーケースをテスト"""
    with pytest.raises(ValueError):
        new_feature(invalid_input)
```

実行時は **Red** → **Green** → **Refactor** のサイクルを回します。

```bash
# テスト実行（Red: まず失敗する）
pytest tests/test_new_feature.py -v

# 実装（Green: テストが通るまで）
# src/pokecode/ に実装コードを追加

# リファクタリング（整理）
```

---

### ステップ 3: 実装

**原則**:
- 型ヒントを必須で
- docstring を必ず付ける
- 例外を明示的に処理
- ロギングを追加

**実装テンプレート**:

```python
"""モジュールの説明"""

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class MyFeature(Protocol):
    """この機能の説明"""
    pass


def my_function(arg: str) -> int:
    """
    関数の説明

    Args:
        arg: 引数の説明

    Returns:
        戻り値の説明

    Raises:
        ValueError: エラーケースの説明
    """
    logger.info("処理開始: %s", arg)
    
    try:
        # 実装
        result = int(arg)
        logger.debug("処理成功: result=%d", result)
        return result
    except ValueError as e:
        logger.error("invalid input: %s", arg)
        raise ValueError(f"Invalid value: {arg}") from e
```

---

### ステップ 4: 型チェック

```bash
mypy src/pokecode --strict
```

**ゼロエラーが目標**。エラーが出たら修正。

```
error: "str" is not assignable to "int"
        ↓
型ヒントを確認、または型変換を追加
```

---

### ステップ 5: リント・フォーマット

```bash
# チェック
ruff check src/pokecode

# 自動修正
ruff format src/pokecode

# 未使用インポート削除
ruff check --select=F401 src/pokecode
```

---

### ステップ 6: テスト実行

```bash
# 単体テスト
pytest tests/ -v

# カバレッジ確認
pytest tests/ --cov=src/pokecode --cov-report=html

# 特定のテストだけ実行
pytest tests/test_new_feature.py::test_new_feature_success -v
```

**目標**: PHASE ごとに新機能のカバレッジ > 80%

---

### ステップ 7: ドキュメント更新

```bash
# PHASE ドキュメントを更新
echo "---" >> .docs/phase/PHASE0X.md
echo "## 実装内容（詳細）" >> .docs/phase/PHASE0X.md
```

---

### ステップ 8: コミット

```bash
# コミットメッセージは Conventional Commits に従う
git add .
git commit -m "feat: Add new feature

- 実装内容 1
- 実装内容 2

Related-To: #42"
```

**コミット前のチェックリスト**:
- [ ] テストが全て通る（`pytest tests/`）
- [ ] 型チェック通過（`mypy src/pokecode --strict`）
- [ ] リント通過（`ruff check src/pokecode`）
- [ ] ドキュメント更新済み
- [ ] コミットメッセージは分かりやすいか？

---

## 実装パターン例（request モジュール）

### PHASE 11: 非同期リクエスト対応

#### テストから始める

```python
# tests/test_request_async.py
import pytest
from pokecode.request import request_html_async


@pytest.mark.asyncio
async def test_request_html_async_success():
    """非同期 HTML リクエスト（成功ケース）"""
    result = await request_html_async("http://localhost:5000")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_request_html_async_timeout():
    """タイムアウト処理"""
    with pytest.raises(TimeoutError):
        await request_html_async("http://httpbin.org/delay/100", timeout=0.1)
```

#### 実装

```python
# src/pokecode/request/async_.py
import asyncio
import logging
from typing import Callable

import aiohttp

logger = logging.getLogger(__name__)

HtmlResult = str


async def request_html_async(
    url: str, *, timeout: float = 10.0
) -> HtmlResult:
    """
    非同期で HTML をリクエスト

    Args:
        url: リクエスト URL
        timeout: タイムアウト時間（秒）

    Returns:
        HTML テキスト

    Raises:
        aiohttp.ClientError: ネットワークエラー
        asyncio.TimeoutError: タイムアウト
    """
    logger.info("Async request start: %s", url)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={"Accept": "text/html"},
            ) as resp:
                resp.raise_for_status()
                html = await resp.text()

                logger.debug("Async request success: %s (%d bytes)", url, len(html))
                return html

    except asyncio.TimeoutError:
        logger.error("Timeout: %s", url)
        raise
    except aiohttp.ClientError as e:
        logger.error("Request error: %s - %s", url, e)
        raise


async def request_multiple_async(
    urls: list[str], *, timeout: float = 10.0
) -> list[HtmlResult]:
    """複数 URL のリクエスト（並列）"""
    tasks = [request_html_async(url, timeout=timeout) for url in urls]
    return await asyncio.gather(*tasks)
```

#### テスト実行

```bash
pytest tests/test_request_async.py -v

# 非同期テストは pytest-asyncio が必要
# 追加: pip install pytest-asyncio
```

---

## ドキュメント作成のチェックリスト

各 PHASE で以下のドキュメントを作成してください。

### 1. PHASE0X.md（実装ドキュメント）

```yaml
# 必須セクション
- 目的
- 実装内容（コード例）
- チェックリスト
- テスト結果
- 次のステップ（参考）
```

### 2. .docs/ 配下の共通ドキュメント

- **DEVELOPMENT_ROADMAP.md** - 全体ロードマップ
- **ARCHITECTURE.md** - システム構成（新規作成推奨[PHASE10]）
- **TESTING.md** - テスト実行方法（新規作成推奨[PHASE10]）
- **CONTRIBUTING.md** - 貢献ガイド（このファイル）

---

## よくあるタスク

### タスク1: 既存コードを改善したい

1. テストを書く（現在の動作を記録）
2. リファクタリング
3. テスト確認
4. コミット: `refactor: Improve X functionality`

```bash
pytest tests/test_target.py -v
# ↓ コード改善
ruff format src/pokecode
mypy src/pokecode --strict
pytest tests/test_target.py -v
git commit -m "refactor: Improve request handling"
```

---

### タスク2: 新しい依存関係を追加したい

1. `pyproject.toml` に追加
2. インストール
3. テスト
4. ドキュメント更新

```bash
# pyproject.toml の dependencies に追加
# e.g. "aiohttp>=3.9.0"

# インストール
pip install aiohttp

# テスト
pytest tests/ -v

# コミット
git commit -m "chore: Add aiohttp dependency"
```

---

### タスク3: バグを修正したい

1. **バグを再現するテストを書く**（重要！）
2. 修正実装
3. テスト確認
4. コミット: `fix: Fix X bug`

```bash
# テストを追加（バグを再現）
tests/test_fix.py:
def test_bug_scenario():
    with pytest.raises(ValueError):
        buggy_function()

# テスト実行（Red）
pytest tests/test_fix.py::test_bug_scenario -v
# FAILED

# コードを修正（Green）
# ...

# テスト確認
pytest tests/test_fix.py::test_bug_scenario -v
# PASSED

# コミット
git commit -m "fix: Fix ValueError in buggy_function

Previously, the function raised an unhandled exception
when passed invalid input. Now it properly validates
and raises a descriptive error message."
```

---

## CI/CD パイプラインで実行されるチェック

目標（PHASE09 実装後）:

| チェック項目 | コマンド | 目標 |
|-----------|--------|-----|
| テスト実行 | `pytest tests/` | 全件通過 |
| 型チェック | `mypy src/pokecode --strict` | エラー 0 |
| リント | `ruff check src/pokecode` | エラー 0 |
| フォーマット | `ruff format --check src/pokecode` | 完全準拠 |
| カバレッジ | `pytest --cov` | >= 80% |

ローカル開発時も同じチェックを実行してください。

---

## 開発環境セットアップ（新規メンバー向け）

```bash
# 1. リポジトリをクローン
git clone https://github.com/yourusername/pokecode.git
cd pokecode

# 2. 仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate      # Windows

# 3. 依存関係をインストール
pip install -e ".[dev]"    # dev グループも含む

# 4. VS Code 設定（オプション）
code --install-extension ms-python.python
code --install-extension charliermarsh.ruff

# 5. テストを実行して確認
pytest tests/ -v
```

---

## 作業中によくあるエラーと対処

### Error: "Type str | None is not assignable to str"

```python
# ❌ 間違い
def get_value(key: str) -> str:
    return os.getenv(key)  # None の可能性あり

# ✅ 正解1: デフォルト値を指定
def get_value(key: str) -> str:
    return os.getenv(key, "default")

# ✅ 正解2: Optional を返す
def get_value(key: str) -> str | None:
    return os.getenv(key)
```

---

### Error: "Unused import"

```bash
# 自動削除
ruff check --select=F401 src/pokecode --fix
```

---

### Error: "Expected exception not raised"

```python
# ❌ 間違い
def test_error():
    with pytest.raises(ValueError):
        valid_function()  # 例外が発生しない

# ✅ 正解
def test_error():
    with pytest.raises(ValueError):
        invalid_function(invalid_arg)  # 例外が発生する
```

---

## 進捗レポート（テンプレート）

PHASE 完了時にこれを記載してください:

```markdown
## PHASE 0X 完了報告

**実装日**: YYYY-MM-DD
**所要時間**: X 時間
**担当者**: Name

### 実装内容

- [ ] 機能 1 実装
- [ ] 機能 2 実装
- [ ] テスト追加
- [ ] ドキュメント更新

### テスト結果

```
pytest tests/ -v
============ 42 passed in 1.23s =============
```

### 品質指標

- 型チェック: ✅ エラー 0
- リント: ✅ エラー 0
- カバレッジ: 85%

### 次の予定

PHASE 0(X+1): ...
```

---

## まとめ

### キーポイント💡

1. **テストから始める** - 実装前にテストを書く（TDD）
2. **型安全** - `mypy --strict` でエラー 0 を維持
3. **ドキュメント** - 実装と同時にドキュメント更新
4. **コミット** - 意味のある小分けにコミット
5. **レビュー** - コミット前に自分でレビュー

Happy coding! 🚀
