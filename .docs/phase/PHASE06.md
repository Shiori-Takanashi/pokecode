# PHASE06：設定管理のリファクタリング

**目的**: 環境変数対応、.env ファイル導入、設定管理の統一化

**進捗**: 🟡 開発中

---

## 1. 現在の問題点

### 1.1 getpath.py の問題

```python
# ❌ 問題：モジュール実行時に副作用がある
p = get_project_root_to_parent(Path(__file__).parent.resolve())
print(p)  # ← テスト用?本番用?不明確
```

- テスト用の実行コードが本来のコードに混在
- インポート時に勝手に print が実行される
- 関数は正当だが、ボイラープレートが不要

### 1.2 config.py の問題

```python
# ❌ 拡張性が低い
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
```

- ハードコードされた相対パス
- 環境変数対応がない
- 複数環境（dev, test, prod）への対応がない

### 1.3 loading.py の問題

```python
def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    # 環境変数フォールバックがない
    # .env ファイル対応がない
```

### 1.4 pyproject.toml の問題

```toml
[tool.pokecode]
logdir = "logs"
logfile = "app.log"

# ❌ ハードコード URL、環境ごとに異なるべき
local = "http://localhost:5000/json"
```

---

## 2. 改善案

### 2.1 環境変数ベースの設定

```
環境変数 → .env ファイル → pyproject.toml → デフォルト値
```

**優先順位**（から上順）:
1. 環境変数（`POKECODE_LOG_DIR` など）
2. .env ファイル（`.env.local` など）
3. pyproject.toml（`[tool.pokecode]`）
4. ハードコード（デフォルト値）

### 2.2 getpath.py のリファクタリング

```python
# ✅ テスト用コードを削除
# ✅ 関数のみを提供
# → 書き込みはテストファイルで行う
```

### 2.3 config.py の拡張

```python
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv  # python-dotenv

class Config:
    # プロジェクトルート
    PROJECT_ROOT: Path = ...
    PYPROJECT: Path = ...
    
    # ログ設定（環境変数対応）
    LOG_DIR: Path = ...
    LOG_FILE: str = ...
    DEBUG_LOG_DIR: Path = ...
    DEBUG_LOG_FILE: str = ...
    
    # サーバー設定（環境変数対応）
    HOST: str = ...
    PORT: int = ...
    
    # API URL（環境ごとに異なる）
    LOCAL_HTML_URL: str = ...
    LOCAL_JSON_URL: str = ...
    REMOTE_API_URL: Optional[str] = ...
    
    @classmethod
    def load(cls) -> 'Config':
        # .env ファイル読み込み
        # 環境変数から値を取得
        # フォールバック処理
        ...
```

### 2.4 .env.example の作成

```
# ログ設定
LOG_DIR=logs
LOG_FILE=app.log
DEBUG_LOG_DIR=debug_log
DEBUG_LOG_FILE=debug.log

# サーバー設定
HOST=127.0.0.1
PORT=5000

# API URL（環境ごとに変更）
LOCAL_HTML_URL=http://localhost:5000
LOCAL_JSON_URL=http://localhost:5000/json
```

---

## 3. リファクタリング計画

### ステップ 1：getpath.py をクリーンアップ

```python
# ❌ 削除対象
p = get_project_root_to_parent(Path(__file__).parent.resolve())
print(p)

# ✅ 保持：関数定義のみ
def get_project_root_to_parent(dirpath: Path) -> Path:
    ...
```

### ステップ 2：config.py を拡張

- `Config` クラスを定義
- 環境変数読み込み
- デフォルト値管理
- `.env` ファイル対応

### ステップ 3：loading.py を改善

- `Config` オブジェクトを返すように変更
- 環境変数フォールバック

### ステップ 4：pyproject.toml をシンプル化

```toml
[tool.pokecode]
# 本当に固定値だけを残す
version = "0.1.0"

# 環境ごとに配置する設定は削除
# logdir, logfile などは .env へ移行
```

### ステップ 5：.env.example を作成

```
cp .env.example .env.local  # 開発環境用
```

---

## 4. 実装スケッチ

### getpath.py（クリーンアップ）

```python
# pokecode/getpath.py
from pathlib import Path


class DirectoryNotFoundError(Exception):
    pass


def get_project_root_to_parent(dirpath: Path) -> Path:
    """
    ディレクトリから親方向へ探索し、プロジェクトルートを検出

    .git または .venv を見つけたら、その親ディレクトリをプロジェクトルートとする
    """
    if not dirpath.is_dir():
        raise ValueError(f"引数がディレクトリではありません: {dirpath}")

    if (dirpath / ".git").exists() or (dirpath / ".venv").exists():
        return dirpath.resolve()

    if dirpath == dirpath.parent:
        raise DirectoryNotFoundError("プロジェクトルートが見つかりませんでした。")

    return get_project_root_to_parent(dirpath.parent)


def get_pyproject_to_parent(dirpath: Path) -> Path:
    """
    ディレクトリから親方向へ探索し、pyproject.toml を検出
    """
    if dirpath.is_file():
        raise ValueError(f"引数がファイルです: {dirpath}")

    pyproject = dirpath / "pyproject.toml"

    if pyproject.is_file():
        return pyproject

    if (dirpath / ".git").exists() or (dirpath / ".venv").exists():
        raise FileNotFoundError(
            "プロジェクトルートまで遡りましたが、pyproject.toml がありません。"
        )

    if dirpath == dirpath.parent:
        raise FileNotFoundError("ルートディレクトリまで到達しましたが、pyproject.toml が見つかりません。")

    return get_pyproject_to_parent(dirpath.parent)
```

### config.py（拡張版）

```python
# pokecode/config.py
import os
from pathlib import Path
from typing import Optional
import logging

from pokecode.getpath import get_project_root_to_parent

logger = logging.getLogger(__name__)

# プロジェクトルート（動的検出）
PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV = PROJECT_ROOT / ".env.local"  # または .env


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    環境変数を取得（.env ファイルを先に読み込み）
    """
    # .env ファイルを読み込み（python-dotenv の load_dotenv）
    if DOT_ENV.exists():
        from dotenv import load_dotenv
        load_dotenv(DOT_ENV)
    
    return os.getenv(key, default)


class Config:
    """プロジェクト設定の一元化"""
    
    # プロジェクトパス
    PROJECT_ROOT: Path = PROJECT_ROOT
    PYPROJECT: Path = PYPROJECT
    
    # ログ設定（環境変数 → デフォルト値）
    LOG_DIR: Path = Path(_get_env("POKECODE_LOG_DIR", "logs"))
    LOG_FILE: str = _get_env("POKECODE_LOG_FILE", "app.log")
    DEBUG_LOG_DIR: Path = Path(_get_env("POKECODE_DEBUG_LOG_DIR", "debug_log"))
    DEBUG_LOG_FILE: str = _get_env("POKECODE_DEBUG_LOG_FILE", "debug.log")
    
    # サーバー設定
    HOST: str = _get_env("POKECODE_HOST", "127.0.0.1")
    PORT: int = int(_get_env("POKECODE_PORT", "5000"))
    
    # API URL（環境ごとに異なる）
    LOCAL_HTML_URL: str = _get_env(
        "POKECODE_LOCAL_HTML_URL",
        "http://localhost:5000"
    )
    LOCAL_JSON_URL: str = _get_env(
        "POKECODE_LOCAL_JSON_URL",
        "http://localhost:5000/json"
    )
    
    @classmethod
    def to_dict(cls) -> dict:
        """設定をdict に変換（デバッグ用）"""
        return {
            "PROJECT_ROOT": str(cls.PROJECT_ROOT),
            "PYPROJECT": str(cls.PYPROJECT),
            "LOG_DIR": str(cls.LOG_DIR),
            "LOG_FILE": cls.LOG_FILE,
            "DEBUG_LOG_DIR": str(cls.DEBUG_LOG_DIR),
            "DEBUG_LOG_FILE": cls.DEBUG_LOG_FILE,
            "HOST": cls.HOST,
            "PORT": cls.PORT,
            "LOCAL_HTML_URL": cls.LOCAL_HTML_URL,
            "LOCAL_JSON_URL": cls.LOCAL_JSON_URL,
        }
    
    @classmethod
    def log_current(cls) -> None:
        """現在の設定をログ出力（デバッグ用）"""
        logger.debug("Current configuration: %s", cls.to_dict())


# 下位互換性のため、従来のエクスポート
config = Config
```

### loading.py（改善版）

```python
# pokecode/loading.py
import logging
import tomllib
from pathlib import Path

from pokecode.config import Config

logger = logging.getLogger(__name__)


def load_config(pyproject_path: Path = Config.PYPROJECT) -> dict:
    """
    pyproject.toml から設定を読み込む
    """
    logger.info("Loading config: %s", pyproject_path)

    if not pyproject_path.exists():
        logger.error("Config file not found: %s", pyproject_path)
        raise FileNotFoundError(f"pyproject.toml not found: {pyproject_path}")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    logger.info("Config loaded successfully")
    return data


def get_app_config() -> dict:
    """
    アプリケーション設定を取得（pyproject.toml + 環境変数）
    """
    pyproject = load_config()
    
    # pyproject.toml の設定をマージ（必要に応じて）
    # 環境変数が優先される
    return {
        "log_dir": str(Config.LOG_DIR),
        "log_file": Config.LOG_FILE,
        "debug_log_dir": str(Config.DEBUG_LOG_DIR),
        "debug_log_file": Config.DEBUG_LOG_FILE,
        "host": Config.HOST,
        "port": Config.PORT,
        "local_html_url": Config.LOCAL_HTML_URL,
        "local_json_url": Config.LOCAL_JSON_URL,
        **pyproject.get("tool", {}).get("pokecode", {}),
    }
```

### .env.example

```
# ログ設定
POKECODE_LOG_DIR=logs
POKECODE_LOG_FILE=app.log
POKECODE_DEBUG_LOG_DIR=debug_log
POKECODE_DEBUG_LOG_FILE=debug.log

# サーバー設定
POKECODE_HOST=127.0.0.1
POKECODE_PORT=5000

# API URL
POKECODE_LOCAL_HTML_URL=http://localhost:5000
POKECODE_LOCAL_JSON_URL=http://localhost:5000/json

# 将来の拡張用
# POKECODE_REMOTE_API_URL=https://api.example.com
# POKECODE_DATABASE_URL=sqlite:///app.db
```

### pyproject.toml（簡潔版）

```toml
[tool.common]
host = "127.0.0.1"
port = "5000"

[tool.pokecode]
# 環境ごとに変わる設定は .env へ移行
# ここには固定値と説明のみ

# ログ関連（.env で上書き可能）
logdir = "logs"
logfile = "app.log"
debug_logdir = "debug_log"
debug_logfile = "debug.log"
```

---

## 5. 依存パッケージの追加

### python-dotenv の導入

```bash
pip install python-dotenv
# または
uv add python-dotenv
```

pyproject.toml に追加：

```toml
[project]
dependencies = [
    ...
    "python-dotenv>=1.0.0",
    ...
]
```

---

## 6. 実装チェックリスト

### getpath.py
- [x] テスト用の実行コードを削除
- [x] 関数定義をクリーンアップ
- [x] docstring を追加

### config.py
- [ ] Config クラスを定義
- [ ] 環境変数読み込み
- [ ] `.env` ファイル対応
- [ ] デフォルト値管理
- [ ] `to_dict()` メソッド
- [ ] `log_current()` メソッド

### loading.py
- [ ] `get_app_config()` 関数を追加
- [ ] 環境変数フォールバック対応

### .env.example
- [ ] テンプレート作成
- [ ] .gitignore に `.env*` を追加（`.env.example` は除外）

### pyproject.toml
- [ ] python-dotenv を追加
- [ ] `[tool.pokecode]` を簡潔化

### main.py, logconfig.py など での使用
- [ ] `Config` クラスを使うように修正
- [ ] 旧来の `PYPROJECT` import を `Config.PYPROJECT` に変更

---

## 7. マイグレーション手順

### 個別ファイルの更新順序

1. **getpath.py**: テスト用コード削除
2. **config.py**: Config クラス実装
3. **loading.py**: `get_app_config()` 追加
4. **.env.example**: テンプレート作成
5. **pyproject.toml**: python-dotenv 追加
6. **各実装ファイル**: Config を使用するように修正
   - `main.py`
   - `logconfig.py`
   - `server/app.py`
7. **.gitignore**: `.env*` 追加（`.env.example` は除外）

### テスト

```bash
# 1. .env.local を作成（.env.example からコピー）
cp .env.example .env.local

# 2. 環境変数を確認
python -c "from pokecode.config import Config; print(Config.to_dict())"

# 3. 実行テスト
python -m pokecode
```

---

## 8. 下位互換性

### 旧コード
```python
from pokecode.config import PYPROJECT
```

### 新コード（推奨）
```python
from pokecode.config import Config
path = Config.PYPROJECT
```

### 下位互換性維持（オプション）
```python
# config.py の最後に
PYPROJECT = Config.PYPROJECT
PROJECT_ROOT = Config.PROJECT_ROOT
```

---

## 9. 次のステップ

✅ **PHASE06**: 設定管理のリファクタリング計画

📋 **実装**: 上記のコードを適用

📋 **PHASE07** (今後): 設定管理統合テスト

---
