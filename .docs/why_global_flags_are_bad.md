# グローバルフラグ管理は避けるべき理由（当プロジェクトでの実装例）

## 実装の経緯

ユーザーから「グローバルフラグの状態管理は実務的には避けるべき。管理対象が間違っている」という指摘を受け、設計を改善しました。

---

## 問題となったグローバルフラグ実装（改善前）

```python
# logconfig.py
_LOGGING_INITIALIZED = False

def setup_logging(..., force: bool = False) -> None:
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED and not force:
        return

    # ... セットアップ処理 ...

    _LOGGING_INITIALIZED = True
```

```python
# conftest.py
pokecode.logconfig._LOGGING_INITIALIZED = False  # ← モジュール内部に手を加える
```

### この実装の問題

| 問題 | 説明 |
|------|------|
| **管理対象が仮想的** | 「初期化済みか」という論理状態をフラグで追跡 |
| **密結合** | conftest が logconfig の内部実装に依存 |
| **二重管理** | ハンドラー実体 + フラグ = 整合性リスク |
| **隠れたバグ** | フラグ操作を忘れると異常動作 |
| **pytest 非互換** | pytest 内部のハンドラーと衝突 |

---

## 改善後の実装 ✅

### 根本的な改善：「管理対象を物理的実体に変更」

#### logconfig.py（改善版）

```python
from logging.handlers import TimedRotatingFileHandler

def setup_logging(
    *,
    level: str = "INFO",
    logdir: Path | str = "logs",
    logname: str = "app.log",
) -> None:
    root = logging.getLogger()
    logdir: Path = Path(logdir)
    filepath = logdir / logname

    # ✓ 管理対象 = ハンドラーの物理的実体
    # ✓ グローバルフラグなし
    # ✓ conftest との密結合なし
    for handler in root.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            if Path(handler.baseFilename) == filepath:
                return  # 既に同じパスのハンドラーがあれば何もしない

    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = "%(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s"
    formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)

    logdir.mkdir(exist_ok=True)

    fileh = TimedRotatingFileHandler(
        filepath,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding=None,
    )
    fileh.setFormatter(formatter)

    root.addHandler(stream)
    root.addHandler(fileh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
```

#### conftest.py（改善版）

```python
from logging.handlers import TimedRotatingFileHandler

@pytest.fixture(autouse=True)
def reset_root_logger():
    """テスト隔離用ロガーリセット"""
    root = logging.getLogger()

    # TimedRotatingFileHandler のみを選別
    timed_rotating_handlers = [
        h for h in root.handlers
        if isinstance(h, TimedRotatingFileHandler)
    ]

    for h in timed_rotating_handlers:
        root.removeHandler(h)
        h.close()

    yield

    # テスト後も同じ処理
    timed_rotating_handlers = [
        h for h in root.handlers
        if isinstance(h, TimedRotatingFileHandler)
    ]

    for h in timed_rotating_handlers:
        root.removeHandler(h)
        h.close()
```

---

## 改善のポイント

### 1. グローバルフラグの廃止

**❌ 改善前（フラグで管理）**
```
logconfig._LOGGING_INITIALIZED = True   ← 論理的な仮想状態
│
└─ conftest で外部から操作
   pokecode.logconfig._LOGGING_INITIALIZED = False
```

**✓ 改善後（ハンドラーで管理）**
```
root.handlers = [StreamHandler, TimedRotatingFileHandler]  ← 物理的な実体
│
└─ conftest で実体を直接削除
   root.removeHandler(handler)
```

### 2. 密結合の排除

**❌ 改善前**
- conftest が `logconfig._LOGGING_INITIALIZED` に依存
- モジュール内部実装の変更が conftest に波及

**✓ 改善後**
- conftest は `TimedRotatingFileHandler` 型 のみを見る
- logconfig の内部実装に依存しない
- `logging.handlers.TimedRotatingFileHandler` は標準ライブラリ

### 3. pytest 互換性

**❌ 改善前の問題**
```
pytest 内部ハンドラー
├─ _LiveLoggingNullHandler
├─ _FileHandler /dev/null
├─ LogCaptureHandler
└─ LogCaptureHandler

pokecode ハンドラー
└─ StreamHandler, TimedRotatingFileHandler

フラグだけでは、どれが pokecode のハンドラーか区別できない
```

**✓ 改善後**
```
conftest は TimedRotatingFileHandler だけを削除
pytest のハンドラーには触らない
→ テスト実行に必要なハンドラーは残存
```

---

## 「管理対象が間違っている」の意味

### ❌ グローバルフラグ

```
管理対象 = 「初期化済みか」という仮想的な状態

問題：
- フラグは嘘をつく可能性がある
- ハンドラーが存在しても、フラグが False の可能性
- ハンドラーが存在しなくても、フラグが True の可能性
- 物理的な状態と論理的な状態が不一致
```

### ✓ ハンドラー実体

```
管理対象 = 「ハンドラーが存在するか」という物理的事実

利点：
- ハンドラー自体が「存在するか」を証明している
- フラグのような嘘の可能性がない
- 物理的な状態と論理的な状態が必ず一致
```

---

## 実務での判断基準

### グローバルフラグが正当な場合

実務ではほぼない。以下は稀：

- **確実に単一インスタンス化が必要**：ただし設計の方が悪い兆候
- **パフォーマンス最適化**：コストが本当に大きい場合のみ（ただし構造を見直すべき）

### ハンドラー（実体）で管理すべき場合

実務の大部分：

- **logging のような状態管理**：既に handlers リストで状態が管理されている
- **リソースの可視性**：何が追加されているか物理的に確認可能
- **テスト隔離**：実体を削除すれば conftest の管理が完結
- **疎結合性**：モジュール間の依存が最小化される

---

## 開発教訓

> **「一見もっともらしい抽象化（グローバルフラグ）より、物理的な実体（ハンドラー）を直接見る方が、堅牢で保守性が高い」**

設計時には以下の問いを自問する：

1. **管理対象は何か？** → ハンドラー（実体）か、フラグ（抽象化）か
2. **外部から見えるか？** → デバッグ時に状態を確認できるか
3. **密結合していないか？** → モジュール内部に依存していないか
4. **テスト性は高いか？** → 仮想的な状態操作が必要ないか

これらを満たすなら、その設計は実務的に堅牢です。
