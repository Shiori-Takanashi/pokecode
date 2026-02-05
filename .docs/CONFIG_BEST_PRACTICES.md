# 設定管理: ベストプラクティス解説

## なぜシンプルな関数型が最適か

### 1. Python の哲学

> **Zen of Python**: "Simple is better than complex."

```python
# ❌ 複雑な設定（不要なクラス）
class Config:
    @classmethod
    def get_log_dir(cls):
        return Path(_get_env(...))

# ✅ シンプルな設定（関数）
def get_log_dir():
    return Path(_get_env(...))
```

### 2. 型システムの安全性

Pylance と mypy は単純な関数をより正しく型推論できます。

```python
# ❌ classmethod + 複雑な型
@classmethod
def get_port(cls) -> int:
    return int(...)  # → Pylance が型チェック失敗

# ✅ 単純な関数
def get_port() -> int:
    return int(...)  # → Pylance が完全にチェック
```

### 3. テスト容易性

```python
# ✅ 関数は簡単にモック可能
import unittest.mock as mock

with mock.patch('pokecode.config.os.getenv', return_value='9000'):
    assert get_port() == 9000
```

### 4. IDE サポート

- **オートコンプリート**: `config.get_` で全関数がリスト表示
- **ドキュメンテーション**: `config.get_port()` ホバーでドキュメント表示
- **リファクタリング**: `get_port` に名前変更すると自動で追跡

## 設定値の読み込み層

```
実行環境の環境変数
         ↓
    _load_env()
         ↓
 .env.local / .env
         ↓
    os.getenv()
         ↓
  get_port() などの関数
         ↓
 アプリケーション層
```

### 優先順位

1. **環境変数** (最優先)
   ```bash
   export POKECODE_PORT=9000
   python -m pokecode.main  # → port=9000
   ```

2. **.env.local** (ローカル開発用)
   ```dotenv
   # .env.local
   POKECODE_PORT=7000
   POKECODE_HOST=0.0.0.0
   ```

3. **.env** (チーム全体の設定)
   ```dotenv
   # .env
   POKECODE_PORT=5000
   ```

4. **デフォルト値** (フォールバック)
   ```python
   def get_port() -> int:
       return int(_get_env("POKECODE_PORT", "5000"))
   ```

## 実装パターンの比較

### パターン1: グローバル辞書（非推奨）

```python
# ❌ グローバルなので副作用が多い
_config = {
    "port": int(os.getenv("POKECODE_PORT", "5000"))
}

def get_port():
    return _config["port"]
```

**問題点**:
- テスト時に環境変数を変更しても反映されない（既に初期化済み）
- 設定値を追加する際に `_config` dict のメンテナンスが必要

### パターン2: 関数型（推奨）

```python
# ✅ 呼ぶたびに新鮮な値を取得
def get_port() -> int:
    return int(_get_env("POKECODE_PORT", "5000"))
```

**メリット**:
- テスト時に環境変数を変更するだけで反映
- 設定値の追加は新しい関数を追加するだけ
- 型安全

### パターン3: Dataclass（小規模向け）

```python
# △ 小規模プロジェクトなら OK
@dataclass
class Config:
    port: int = field(default_factory=lambda: int(os.getenv(...)))
    host: str = field(default_factory=lambda: os.getenv(...))
```

**注意**:
- `default_factory` が評価される時点は `dataclass` の生成時
- 環境変数の動的変更には対応しない

## パフォーマンス考慮

### .env 読み込みのオーバーヘッド

```python
# モジュール初期化時：1 回だけ実行（python-dotenv で .env をパース）
_load_env()  # ← コスト高（ファイル I/O）

# 関数呼び出し：毎回メモリ操作のみ
def get_port():
    return int(os.getenv(...))  # ← コスト低（メモリ参照）
```

### 呼び出しコスト

```python
# `get_port()` は約 1-2 マイクロ秒
# 10000 回呼んでも 10-20 ミリ秒程度
```

→ 実用上の問題なし。シンプルさを優先。

## 本番環境での設定

### 開発環境

```bash
# .env.local
POKECODE_LOG_DIR=logs
POKECODE_HOST=127.0.0.1
POKECODE_PORT=5000
```

### ステージング環境

```bash
# 環境変数で設定
export POKECODE_HOST=0.0.0.0
export POKECODE_PORT=8080
export POKECODE_LOG_DIR=/var/log/pokecode
python -m pokecode.main
```

### 本番環境

```bash
# Docker 環境変数
docker run \
  -e POKECODE_HOST=0.0.0.0 \
  -e POKECODE_PORT=80 \
  -e POKECODE_LOG_DIR=/logs \
  pokecode:latest
```

## チェックリスト（設定を追加する際）

新しい設定値 `FOO` を追加する場合:

- [ ] 環境変数の命名規則に従う: `POKECODE_FOO`
- [ ] デフォルト値を決める
- [ ] ヘルパー関数を追加: `def get_foo() -> Type:`
- [ ] `.env.example` に記載
- [ ] ドキュメント（このファイル）に追加
- [ ] テストを追加: `os.environ["POKECODE_FOO"] = ...`

## トラブルシューティング

### 設定値が変わらない

```python
# ❌ 間違い（初期化時に評価される）
PORT = int(os.getenv("POKECODE_PORT", "5000"))
app.run(port=PORT)

# ✅ 正解（実行時に評価）
app.run(port=config.get_port())
```

### テスト中に設定を変更したい

```python
import os
import pokecode.config as config

def test_custom_port():
    os.environ["POKECODE_PORT"] = "9000"
    assert config.get_port() == 9000
```

### .env ファイルが読み込まれない

```bash
# 確認方法
python -c "from pokecode import config; print(config.get_all())"

# ファイルパスをチェック
ls -la .env.local  # あるか確認
# または
ls -la .env        # あるか確認
```

## 参考資料

- [12-Factor App Config Factor](https://12factor.net/config)
- [Python os.getenv()](https://docs.python.org/3/library/os.html#os.getenv)
- [python-dotenv Documentation](https://python-dotenv.readthedocs.io/)
