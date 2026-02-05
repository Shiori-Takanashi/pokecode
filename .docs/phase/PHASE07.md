# PHASE 07: シンプルで型安全な設定管理

## 目的

前段階の複雑な Config クラス実装を、Python のベストプラクティスに従ったシンプルな関数ベースの設定モジュールに置き換える。

## 変更内容

### 1. 設計方針の転換

**旧実装 (PHASE06)**
```python
class Config:
    @classmethod
    def get_log_dir(cls) -> Path:
        return Path(_get_env("POKECODE_LOG_DIR", "logs"))
    
    # ... 大量のメソッド定義
```

**新実装 (PHASE07)**
```python
def get_log_dir() -> Path:
    """ログディレクトリを取得"""
    return Path(_get_env("POKECODE_LOG_DIR", "logs"))

# 関数をモジュールレベルで直接提供
```

### 2. メリット

| 項目 | 旧実装 | 新実装 |
|------|--------|--------|
| **型安全性** | ❌ `@classmethod` + `@property` の併用で型エラー多発 | ✅ 単純な関数で Pylance エラー 0 |
| **シンプルさ** | ❌ クラス定義が 167 行 | ✅ 120 行に削減 |
| **保守性** | ❌ クラスメタが複雑 | ✅ 単純な関数の組み合わせ |
| **Pythonic さ** | ❌ 不要なクラス使用 | ✅ モジュールレベルの関数 API |
| **テスト性** | △ `Config` をモック必要 | ✅ 関数を直接モック可能 |

### 3. 型定義の修正

**_get_env() 関数**
```python
def _get_env(key: str, default: str) -> str:
    """環境変数を取得（デフォルト値必須）"""
    return os.getenv(key, default)  # → str (None ではない)
```

**変更点**: `Optional[str]` → `str`（デフォルト値を必須にすることで型安全性を確保）

## ファイル構成

### src/pokecode/config.py (120 行)

```python
# モジュール定数（不変）
PROJECT_ROOT: Path = ...
PYPROJECT: Path = ...

# ヘルパー関数
def _load_env() -> None: ...
def _get_env(key: str, default: str) -> str: ...

# 設定アクセス関数（小文字）
def get_log_dir() -> Path: ...
def get_log_file() -> str: ...
def get_host() -> str: ...
def get_port() -> int: ...
def get_local_html_url() -> str: ...
def get_local_json_url() -> str: ...

# ユーティリティ
def get_all() -> dict: ...  # デバッグ用に全設定を辞書で返す
```

### 使用パターン

```python
from pokecode import config

# 個別の設定を取得
url = config.get_local_html_url()  # "http://localhost:5000"
port = config.get_port()  # 5000

# すべての設定を取得
all_settings = config.get_all()  # dict

# 定数にアクセス
root = config.PROJECT_ROOT  # Path
```

## 迁移ガイド

### 旧コード → 新コード

```python
# PHASE06 (旧)
from pokecode.config import Config
url = Config.local_html_url()  # classmethod

# PHASE07 (新)
from pokecode import config
url = config.get_local_html_url()  # function
```

変更ファイル:
- ✅ [src/pokecode/main.py](../src/pokecode/main.py)
- ✅ [src/pokecode/loading.py](../src/pokecode/loading.py)
- ✅ [src/pokecode/logconfig.py](../src/pokecode/logconfig.py)

## 環境変数 → 設定値のマッピング

| 環境変数 | 関数 | デフォルト値 |
|---------|------|----------|
| `POKECODE_LOG_DIR` | `get_log_dir()` | `"logs"` |
| `POKECODE_LOG_FILE` | `get_log_file()` | `"app.log"` |
| `POKECODE_DEBUG_LOG_DIR` | `get_debug_log_dir()` | `"debug_log"` |
| `POKECODE_DEBUG_LOG_FILE` | `get_debug_log_file()` | `"debug.log"` |
| `POKECODE_HOST` | `get_host()` | `"127.0.0.1"` |
| `POKECODE_PORT` | `get_port()` | `5000` |
| `POKECODE_LOCAL_HTML_URL` | `get_local_html_url()` | `"http://localhost:5000"` |
| `POKECODE_LOCAL_JSON_URL` | `get_local_json_url()` | `"http://localhost:5000/json"` |

## .env ファイル設定例

**.env.local または .env**
```dotenv
POKECODE_LOG_DIR=logs
POKECODE_LOG_FILE=myapp.log
POKECODE_HOST=0.0.0.0
POKECODE_PORT=8080
POKECODE_LOCAL_HTML_URL=http://myserver:8080
```

## Pylance エラー解決

### 問題点（PHASE06）
```
型 "str | None" の引数を、関数 "__new__" の型 "StrPath" のパラメーター "args" に割り当てることはできません
```

### 原因
`_get_env()` が `str | None` を返すのに、戻り値の型を `str` と宣言していた

### 解決策
型シグネチャを修正（デフォルト値を必須に）
```python
# 旧
def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)

# 新
def _get_env(key: str, default: str) -> str:
    return os.getenv(key, default)
```

## ベストプラクティス

### 1. 単一責任の原則
- 設定モジュール: 環境変数から値を読み込むだけ
- ロジックはこのモジュールに含めない

### 2. 構成可能性 (Composability)
- 小さな関数の組み合わせ
- 各関数が独立して動作

### 3. テスト性
```python
# テスト内で環境変数を変更可能
import os
os.environ["POKECODE_PORT"] = "9000"
assert config.get_port() == 9000  # 即座に反映
```

### 4. パフォーマンス
- `.env` ファイルはモジュール初期化時に 1 回だけ読み込み
- 以降は `os.getenv()` で取得（メモリ操作のみ）

## テスト結果

✅ `get_log_dir()` 正常動作
✅ `get_host()` 正常動作  
✅ `get_port()` 正常動作  
✅ `get_local_html_url()` 正常動作  
✅ `get_all()` 全設定を辞書で返却  
✅ Pylance エラー = 0  
✅ main.py 実行可能  
✅ 動的設定（環境変数変更に対応）

## 次のステップ

- PHASE08: ロギング検証と統合テスト
- PHASE09: サーバー固有設定（Flask）の統合
- PHASE10: プロダクション設定ガイド
