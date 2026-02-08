# Ruff 使い方と設定ガイド

本プロジェクトでは **Ruff 0.14.14** を使用しています。

## Ruffとは

Ruffは、Rustで書かれた高速なPythonのLinterおよびFormatterです。Flake8、isort、Black、pylint等の機能を統合し、従来のツールと比較して10-100倍高速に動作します。

## インストール

本プロジェクトでは、`pyproject.toml`に既にRuffが含まれています。

```toml
dependencies = [
    "ruff>=0.14.14",
]
```

uvを使用してインストール：

```bash
uv sync
```

## 基本的な使い方

### 1. Linting（リント）

コードをチェックして問題を検出：

```bash
# プロジェクト全体をチェック
uv run ruff check .

# 特定のファイルやディレクトリをチェック
uv run ruff check src/pokecode/

# 自動修正可能なエラーを修正
uv run ruff check --fix .

# すべての自動修正（安全でないものも含む）
uv run ruff check --fix --unsafe-fixes .

# 特定のルールを無視
uv run ruff check --ignore E501 .
```

### 2. Formatting（フォーマット）

コードを自動整形：

```bash
# プロジェクト全体をフォーマット
uv run ruff format .

# 特定のファイルをフォーマット
uv run ruff format src/pokecode/main.py

# 変更をプレビュー（実際には変更しない）
uv run ruff format --check .

# diff形式で変更内容を表示
uv run ruff format --diff .
```

### 3. Linting + Formatting（一括実行）

```bash
# リントしてからフォーマット
uv run ruff check --fix . && uv run ruff format .
```

## 対象ファイル・拡張子

### デフォルトで対象となる拡張子

Ruffは以下の拡張子を持つファイルをデフォルトで処理します：

- **`.py`** - 通常のPythonソースファイル
- **`.pyi`** - Pythonスタブファイル（型情報）

### 追加可能な拡張子

設定により以下のファイルタイプも対象に含めることができます：

- **`.ipynb`** - Jupyter Notebook（`extend-include`で指定）

```toml
[tool.ruff]
# Jupyter Notebookも対象に含める
extend-include = ["*.ipynb"]
```

### ファイル検出パターン

Ruffは指定されたディレクトリから再帰的にファイルを検索します。`.gitignore`や`exclude`設定で除外されたファイル以外がすべて対象になります。

## pyproject.tomlでの設定

Ruffの設定は`pyproject.toml`の`[tool.ruff]`セクションで行います。

### 基本設定例

```toml
[tool.ruff]
# Python 3.14以上を対象
target-version = "py314"

# 行の最大長
line-length = 88

# チェック対象から除外するパス
exclude = [
    ".git",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

# チェック対象とするファイルパターン
extend-include = ["*.ipynb"]
```

### Linting設定

```toml
[tool.ruff.lint]
# 有効化するルールセット
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]

# 無視するルール
ignore = [
    "E501",  # line too long (formatter が処理するため)
    "B008",  # function calls in argument defaults
]

# ファイルごとに無視するルール
[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # unused imports
"tests/*" = ["ARG", "S101"]  # test files

# isortの設定
[tool.ruff.lint.isort]
known-first-party = ["pokecode"]
section-order = [
    "future",
    "standard-library",
    "third-party",
    "first-party",
    "local-folder"
]
```

### Formatting設定

```toml
[tool.ruff.format]
# クォートのスタイル（"double" または "single"）
quote-style = "double"

# インデントのスタイル（"space" または "tab"）
indent-style = "space"

# マジックトレイリングカンマを尊重
skip-magic-trailing-comma = false

# 行末の改行を保証
line-ending = "auto"

# docstringのフォーマット
docstring-code-format = true
docstring-code-line-length = "dynamic"
```

## 主要なルールセット

| コード | 説明 | 対応ツール |
|--------|------|------------|
| E, W | pycodestyleのエラーと警告 | pycodestyle |
| F | 論理エラー | Pyflakes |
| I | import文の整理 | isort |
| N | 命名規則 | pep8-naming |
| D | docstring | pydocstyle |
| B | よくあるバグ | flake8-bugbear |
| S | セキュリティ | bandit |
| C4 | 内包表記の改善 | flake8-comprehensions |
| UP | Python構文の更新 | pyupgrade |
| ARG | 未使用の引数 | flake8-unused-arguments |
| SIM | コードの簡略化 | flake8-simplify |
| RUF | Ruff固有のルール | - |

全ルールのリスト: https://docs.astral.sh/ruff/rules/

## VS Code統合

### 拡張機能のインストール

1. VS Code拡張機能「Ruff」をインストール
2. `.vscode/settings.json`に以下を追加：

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "ruff.lineLength": 88,
  "ruff.lint.enable": true,
  "ruff.format.enable": true
}
```

## CI/CDでの使用

### GitHub Actions例

```yaml
name: Lint and Format Check

on: [push, pull_request]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync
      - name: Run Ruff linter
        run: uv run ruff check .
      - name: Run Ruff formatter check
        run: uv run ruff format --check .
```

## pre-commitフックでの使用

`.pre-commit-config.yaml`を作成：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.14
    hooks:
      # Linter
      - id: ruff
        args: [--fix]
      # Formatter
      - id: ruff-format
```

インストール：

```bash
pip install pre-commit
pre-commit install
```

## Makefileでの統合

プロジェクトの`Makefile`に以下を追加：

```makefile
.PHONY: lint format check

# Lintingのみ（修正あり）
lint:
	uv run ruff check --fix .

# Formattingのみ
format:
	uv run ruff format .

# Linting + Formatting
check: lint format

# CI用（修正なし、エラーで終了）
ci-check:
	uv run ruff check .
	uv run ruff format --check .
```

使用例：

```bash
make check      # ローカル開発で使用
make ci-check   # CI/CDで使用
```

## トラブルシューティング

### 設定が反映されない場合

**症状**: `line-length`などの設定を変更しても反映されない

**よくある原因と解決方法**:

1. **セクション名のタイポ**
   ```toml
   # ❌ 間違い
   [tool.rull]
   line-length = 60

   # ✅ 正しい
   [tool.ruff]
   line-length = 60
   ```

2. **設定の確認方法**
   ```bash
   # 現在の設定を表示
   uv run ruff check --show-settings .

   # line-length関連の設定を確認
   uv run ruff check --show-settings . 2>&1 | grep -i "line"
   ```

   出力例（デフォルト値88）:
   ```
   linter.line_length = 88
   formatter.line_width = 88
   ```

3. **uv syncは不要**
   - Ruffの設定変更には`uv sync`は不要です
   - `pyproject.toml`の変更は即座に反映されます
   - ただし、設定ファイルにタイポがある場合は読み込まれません

4. **検証方法**
   ```bash
   # line-lengthを変更後、確認
   # 実際に長い行があるファイルをフォーマット
   uv run ruff format --diff <ファイル名>
   ```

   変更が反映されていれば、60文字を超える行が分割されます。
   「unchanged」と表示される場合は、設定が読み込まれていない可能性があります。

### キャッシュの削除

Ruffがおかしな動作をする場合、キャッシュをクリア：

```bash
rm -rf .ruff_cache
```

### 設定の確認

現在の設定を表示：

```bash
uv run ruff check --show-settings .
```

### 特定の行でルールを無視

```python
# 特定の行のみ無視
result = dangerous_function()  # noqa: S101

# 特定のルールのみ無視
import unused_module  # noqa: F401

# ファイル全体で無視（ファイルの先頭に記載）
# ruff: noqa: E501
```

## 参考リンク

- [Ruff公式ドキュメント](https://docs.astral.sh/ruff/)
- [Ruff設定リファレンス](https://docs.astral.sh/ruff/configuration/)
- [Ruffルール一覧](https://docs.astral.sh/ruff/rules/)
- [RuffのGitHubリポジトリ](https://github.com/astral-sh/ruff)

## バージョン情報

- 本ドキュメントは **Ruff 0.14.14** を対象としています
- 作成日: 2026年2月8日
