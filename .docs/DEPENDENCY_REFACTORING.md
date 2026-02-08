# 依存関係の問題と改善案

## 現在の依存関係（PHASE07）

```
getpath.py (独立)
    ↑ import
config.py ──┐
    ↑       │モジュール初期化時に
    │       │get_project_root_to_parent()を呼ぶ
    │       └→ 強結合
    │
    ├── loading.py
    ├── logconfig.py
    └── main.py
```

### 問題点

#### 1. **config.py が getpath.py に依存**
```python
# config.py (11行目)
from pokecode.getpath import get_project_root_to_parent

# モジュールレベルで実行（import 時に評価）
PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)
```

- config をインポートするだけで getpath も読み込まれる
- テスト時に PROJECT_ROOT をモックしにくい
- 循環インポートのリスク

#### 2. **モジュール初期化時の副作用**
```python
# config.py (65行目)
_load_env()  # ← import 時に実行される
```

- `import pokecode.config` するだけで .env ファイルを読む
- テストで環境をリセットしにくい

#### 3. **相互依存の複雑さ**
- getpath → (独立)
- config → getpath
- loading → config
- logconfig → config
- main → config + loading

---

## 改善案（推奨）

### 案1: paths モジュールを分離（★推奨）

```
getpath.py (独立ユーティリティ)
    ↓
paths.py (プロジェクトパス定数)
    ↓
config.py (環境変数管理のみ)
    ↓
loading.py, logconfig.py, main.py
```

**実装**:

```python
# paths.py (NEW)
"""プロジェクトパス定数"""
from pathlib import Path
from pokecode.getpath import get_project_root_to_parent

PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV_LOCAL = PROJECT_ROOT / ".env.local"
DOT_ENV = PROJECT_ROOT / ".env"
```

```python
# config.py (改善版)
"""環境変数管理"""
import os
from pathlib import Path
from pokecode.paths import PROJECT_ROOT, DOT_ENV_LOCAL, DOT_ENV

# 以下は変更なし（getpath への依存を削除）
```

**メリット**:
- ✅ 責任の分離（パス検出 vs 環境変数管理）
- ✅ config.py がシンプルになる
- ✅ テストしやすい

**デメリット**:
- ⚠️ ファイルが1つ増える

---

### 案2: 遅延評価（Lazy Loading）

```python
# config.py
from pathlib import Path

_project_root: Path | None = None


def get_project_root() -> Path:
    """プロジェクトルートを取得（遅延評価）"""
    global _project_root
    if _project_root is None:
        from pokecode.getpath import get_project_root_to_parent
        _project_root = get_project_root_to_parent(Path(__file__).parent)
    return _project_root


# 定数をプロパティ化
PROJECT_ROOT = property(lambda self: get_project_root())
```

**メリット**:
- ✅ import 時に getpath を読み込まない
- ✅ 必要になるまで評価を遅延

**デメリット**:
- ❌ 複雑になる
- ❌ `PROJECT_ROOT` が関数呼び出しになる

---

### 案3: 環境変数で PROJECT_ROOT を指定

```python
# config.py
import os
from pathlib import Path

# 環境変数 POKECODE_PROJECT_ROOT があればそれを使う
PROJECT_ROOT = Path(os.getenv(
    "POKECODE_PROJECT_ROOT",
    Path(__file__).parent.parent.parent  # フォールバック
))
```

**メリット**:
- ✅ getpath への依存を完全削除
- ✅ テスト時に環境変数で上書き可能

**デメリット**:
- ❌ .git/.venv の自動検出機能が失われる
- ❌ 手動で環境変数を設定する必要がある

---

## 推奨される実装（案1の詳細）

### ステップ1: paths.py を作成

```python
# src/pokecode/paths.py
"""プロジェクトパス定数モジュール

getpath を使ってプロジェクトルートを検出し、
各種パスの定数を提供します。
"""

from pathlib import Path

from pokecode.getpath import get_project_root_to_parent

# プロジェクトルート検出
PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)

# 各種パス定数
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV_LOCAL = PROJECT_ROOT / ".env.local"
DOT_ENV = PROJECT_ROOT / ".env"
```

### ステップ2: config.py を修正

```python
# src/pokecode/config.py
"""プロジェクト設定モジュール

環境変数または .env ファイルから設定値を読み込みます。
優先順位: 環境変数 → .env.local → .env → デフォルト値
"""

import logging
import os
from pathlib import Path

from pokecode.paths import PROJECT_ROOT, PYPROJECT, DOT_ENV_LOCAL, DOT_ENV

logger = logging.getLogger(__name__)

# 以降は変更なし...
```

### ステップ3: 他のファイルも修正

```python
# loading.py
from pokecode import config
from pokecode.paths import PYPROJECT  # config.PYPROJECT の代わり

def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    ...
```

```python
# logconfig.py
from pokecode import config
from pokecode.paths import PROJECT_ROOT

def _resolve_logfile(*, logdir_name: str, logname: str) -> Path:
    logdir = PROJECT_ROOT / logdir_name
    ...
```

---

## 依存関係の Before/After

### Before（PHASE07）
```
[独立] getpath.py
         ↑ (強結合)
       config.py
         ↑
    ┌────┼────┐
    ↑    ↑    ↑
loading logconfig main
```

### After（PHASE08 推奨）
```
[独立] getpath.py
         ↓ (弱結合)
       paths.py
         ↓
       config.py
         ↑
    ┌────┼────┐
    ↑    ↑    ↑
loading logconfig main
```

**変化**:
- ✅ config.py が getpath に直接依存しない
- ✅ paths.py が責任を持つ（単一責任の原則）
- ✅ テスト時に paths をモック可能

---

## テストのしやすさ比較

### Before
```python
# テストで PROJECT_ROOT を変えたい
import pokecode.config as config

# ❌ 難しい：モジュールレベルで既に評価済み
config.PROJECT_ROOT = Path("/tmp/test")  # 効果なし
```

### After
```python
# テストで PROJECT_ROOT を変えたい
import pokecode.paths as paths

# ✅ 簡単：paths モジュールをモック
with mock.patch("pokecode.paths.PROJECT_ROOT", Path("/tmp/test")):
    # テストコード
    ...
```

---

## 実装チェックリスト（PHASE08）

- [ ] `src/pokecode/paths.py` を作成
- [ ] `config.py` から getpath のインポートを削除
- [ ] `config.py` で `from pokecode.paths import ...` に変更
- [ ] `loading.py` で `PYPROJECT` を paths からインポート
- [ ] `logconfig.py` で `PROJECT_ROOT` を paths からインポート
- [ ] テスト実行（`pytest tests/ -v`）
- [ ] 型チェック（`mypy src/pokecode --strict`）
- [ ] ドキュメント更新

---

## まとめ

| 案 | シンプルさ | 保守性 | テスト容易性 | 推奨度 |
|----|----------|--------|------------|--------|
| 案1: paths分離 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ★★★ |
| 案2: 遅延評価 | ⭐ | ⭐⭐ | ⭐⭐ | ★ |
| 案3: 環境変数 | ⭐⭐ | ⭐ | ⭐⭐⭐ | ★ |

**推奨**: **案1（paths.py を分離）** が最もバランスが良い。

---

## 実装完了（2026-02-05）

✅ **案1（paths.py 分離）を実装しました**

### 変更内容

1. **新規ファイル**: [src/pokecode/paths.py](../src/pokecode/paths.py)
   - プロジェクトパス定数を管理
   - getpath のみに依存

2. **修正ファイル**:
   - [config.py](../src/pokecode/config.py) - paths から定数をインポート
   - [loading.py](../src/pokecode/loading.py) - paths.PYPROJECT 使用
   - [logconfig.py](../src/pokecode/logconfig.py) - paths.PROJECT_ROOT 使用
   - [main.py](../src/pokecode/main.py) - paths.PYPROJECT 使用

### 動作確認

```bash
✅ paths モジュール: OK
✅ config モジュール（再エクスポート）: OK
✅ 設定値取得: OK
✅ main.py 実行: OK
✅ Pylance エラー: 0
```

### 新しい依存関係

```
getpath.py (独立ユーティリティ)
    ↓
paths.py (プロジェクトパス定数)
    ↓
config.py (環境変数管理)
    ↑
    ├── loading.py
    ├── logconfig.py
    └── main.py
```

**効果**:
- ✅ 責任の分離が明確
- ✅ config.py がシンプルに
- ✅ テストしやすい構造
- ✅ 下位互換性維持（config.PROJECT_ROOT も使える）
