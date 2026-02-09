# モジュール依存関係ドキュメント

## 概要

このドキュメントでは、pokecode プロジェクトにおけるモジュール間の依存関係を説明します。

## 循環インポートの問題

### 現在の依存関係

```
getpath.py → logconfig.py → config.py → paths.py → getpath.py
```

### 詳細な依存チェーン

1. **getpath.py**
   - `from pokecode.logconfig import setup_logging`
   - `get_project_root_to_parent()`: プロジェクトルートを検出する低レベル関数
   - `get_pyproject_to_parent()`: pyproject.toml を検出する低レベル関数

2. **logconfig.py**
   - `from pokecode.config import PROJECT_ROOT`
   - `setup_logging()`: ロガーのセットアップを行う

3. **config.py**
   - `from pokecode.paths import DOT_ENV, DOT_ENV_LOCAL, PROJECT_ROOT`
   - プロジェクト設定を管理

4. **paths.py**
   - `from pokecode.getpath import get_project_root_to_parent`
   - `PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)`
   - プロジェクトパス定数を提供

### 問題点

`getpath.py` に logger を導入しようとすると、以下の循環が発生します：

```python
# getpath.py が読み込まれる
import logging
from pokecode.logconfig import setup_logging  # logconfig を読み込み開始

# logconfig.py が読み込まれる
from pokecode.config import PROJECT_ROOT  # config を読み込み開始

# config.py が読み込まれる
from pokecode.paths import PROJECT_ROOT  # paths を読み込み開始

# paths.py が読み込まれる
from pokecode.getpath import get_project_root_to_parent  # getpath が未完成なのでエラー
```

### エラーメッセージ

```
ImportError: cannot import name 'get_project_root_to_parent' from partially initialized module 'pokecode.getpath'
(most likely due to a circular import)
```

## 解決策の選択肢

### オプション 1: 遅延インポート（関数内でimport）

getpath.py の各関数内で `setup_logging` をインポートする：

```python
def get_project_root_to_parent(dirpath: Path) -> Path:
    from pokecode.logconfig import setup_logging  # ここでインポート
    setup_logging(logger=logger)
    # ...
```

**メリット:**
- ロガー機能を維持できる
- モジュールレベルの循環を回避

**デメリット:**
- 毎回関数呼び出し時にインポートのオーバーヘッドがある
- PEP8 スタイルから外れる

### オプション 2: ロガーを削除

getpath.py は低レベルユーティリティなので、ロギングを行わない：

```python
# logconfig のインポートを削除
# logger を使用しない
```

**メリット:**
- シンプルで依存関係がクリーン
- getpath は基盤モジュールとして適切

**デメリット:**
- デバッグ情報が得られない

### オプション 3: ロガーをオプション化

try-except で logconfig が利用可能な場合のみ使用：

```python
try:
    from pokecode.logconfig import setup_logging
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False

def get_project_root_to_parent(dirpath: Path) -> Path:
    if LOGGING_AVAILABLE:
        setup_logging(logger=logger)
        logger.debug(...)
    # ...
```

**メリット:**
- 柔軟性が高い
- 循環インポート時は単にロギングをスキップ

**デメリット:**
- コードが複雑になる

### オプション 4: アーキテクチャの再設計

logconfig.py が PROJECT_ROOT に依存しないようにする：

```python
# logconfig.py
def setup_logging(
    logger: Logger,
    project_root: Path,  # 引数として受け取る
    # ...
):
    logdir = project_root / logdir_name
    # ...
```

**メリット:**
- 依存関係が明確
- 各モジュールの責任が明確

**デメリット:**
- API の変更が必要
- 既存コードの修正が必要

## モジュールの役割

### getpath.py（基盤レイヤー）
- 最も低レベルのユーティリティ
- ファイルシステム操作のみ
- 他の pokecode モジュールに依存すべきではない

### paths.py（設定レイヤー）
- getpath を使ってパス定数を提供
- 他のモジュールから参照される

### config.py（設定レイヤー）
- paths を使って環境変数を読み込む
- アプリケーション設定を提供

### logconfig.py（ユーティリティレイヤー）
- config を使ってログ設定を行う
- 他のモジュールから利用される

## 推奨事項

**短期的な解決策:**
getpath.py からロガーを削除し、基盤モジュールとしてシンプルに保つ。

**長期的な解決策:**
logconfig.py が PROJECT_ROOT をハードコードせず、引数として受け取るようにアーキテクチャを再設計する。

## 実装結果

**2026-02-09 時点:**
getpath.py からロガーを削除し、循環インポートの問題を解決しました。

- ✓ getpath.py は他の pokecode モジュールに依存しない基盤モジュールとして維持
- ✓ 循環インポートエラーは解消
- ✓ すべての機能が正常に動作を確認

## 更新履歴

- 2026-02-09: 初版作成、循環インポート問題を文書化
- 2026-02-09: getpath.py からロガーを削除し、問題を解決
