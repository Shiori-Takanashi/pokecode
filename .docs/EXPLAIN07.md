# EXPLAIN07：最終実装へ向けて

**時刻：T7 | 状態：✓ 改善**

---

## 新しい戦略：ハンドラーの「型」で判定

### 問題の根本

「ハンドラーがあるか」だけでなく、「自分たちのハンドラーがあるか」を判定する必要があります。

```
pytest のハンドラー：
├─ _LiveLoggingNullHandler
├─ _FileHandler
└─ LogCaptureHandler

pokecode のハンドラー：
├─ StreamHandler
└─ TimedRotatingFileHandler  ← これだけを判定したい
```

### 解決策

```python
from logging.handlers import TimedRotatingFileHandler

for handler in root.handlers:
    # TimedRotatingFileHandler だけをチェック
    if isinstance(handler, TimedRotatingFileHandler):
        # さらにファイルパスをチェック
        if Path(handler.baseFilename) == filepath:
            return  # 既に設定済み
```

---

## 改善版 logconfig.py

```python
# src/pokecode/logconfig.py
import logging
import sys
from pathlib import Path
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

    # ✓ 改善点1：型で判定
    # ✓ 改善点2：ファイルパスで判定
    # ✓ 改善点3：グローバルフラグなし
    for handler in root.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            if Path(handler.baseFilename) == filepath:
                return  # 既に同じパスのハンドラーがある

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

### コードの詳しい説明

#### 1. ハンドラー候補を列挙

```python
for handler in root.handlers:
    # すべてのハンドラーをチェック
    # pytest のハンドラーも pokecode のハンドラーも含まれている
```

#### 2. 型で絞り込む

```python
if isinstance(handler, TimedRotatingFileHandler):
    # TimedRotatingFileHandler のみ（pokecode のハンドラー）
    # pytest のハンドラーはスキップ
```

#### 3. ファイルパスで最終確認

```python
if Path(handler.baseFilename) == filepath:
    # さらに、同じファイルパスなら設定済み
    return
```

---

## 改善版 conftest.py

同時に、conftest も改善します：

```python
# tests/conftest.py
import logging
import pytest
from logging.handlers import TimedRotatingFileHandler


@pytest.fixture(autouse=True)
def reset_root_logger():
    """テスト隔離用ロガーリセット（TimedRotatingFileHandler のみ削除）"""
    root = logging.getLogger()

    # pytest のハンドラーは残す
    # pokecode の TimedRotatingFileHandler だけ削除
    timed_rotating_handlers = [
        h for h in root.handlers
        if isinstance(h, TimedRotatingFileHandler)
    ]

    for h in timed_rotating_handlers:
        root.removeHandler(h)
        h.close()  # リソースクローズ

    yield

    # テスト後も同じ
    timed_rotating_handlers = [
        h for h in root.handlers
        if isinstance(h, TimedRotatingFileHandler)
    ]

    for h in timed_rotating_handlers:
        root.removeHandler(h)
        h.close()
```

### conftest の改善点

```python
❌ 改善前：
for h in root.handlers[:]:
    root.removeHandler(h)  # すべてのハンドラーを削除
    pokecode.logconfig._LOGGING_INITIALIZED = False  # フラグも操作

✓ 改善後：
timed_rotating_handlers = [
    h for h in root.handlers
    if isinstance(h, TimedRotatingFileHandler)  # pokecode だけ
]

for h in timed_rotating_handlers:
    root.removeHandler(h)  # pokecode のハンドラーのみ削除
    # フラグ操作なし
```

---

## 改善の効果

### 1. グローバルフラグ廃止

```
❌ 仮想的な状態を管理
✓ 物理的な実体を直接見る
```

### 2. 密結合解除

```
❌ conftest が logconfig._LOGGING_INITIALIZED に依存
✓ conftest が TimedRotatingFileHandler（標準ライブラリ）のみを参照
```

### 3. pytest 互換性

```
❌ すべてのハンドラーをリセット → pytest のハンドラーが消える
✓ TimedRotatingFileHandler だけを削除 → pytest のハンドラーは残る
```

### 4. 保守性向上

```
❌ フラグのリセット忘れのリスク
✓ 物理的な削除なので忘れようがない
```

---

## 実装の比較図

```
═════════════════════════════════════════════════

    改善前              改善後

═════════════════════════════════════════════════

logconfig:          logconfig:
if root.handlers    for handler in root.handlers:
    return              if isinstance(handler, TRF):
                            if Path(...) == filepath:
❌ 全ハンドラーで判定  ✓ 特定型で判定

conftest:          conftest:
for h in all:       timed_rotating = [
    remove()            h for h in all
    logconfig...        if isinstance(h, TRF)
                    ]
❌ すべて削除       ✓ 特定型のみ削除
❌ フラグ操作      ✓ フラグなし

結果：              結果：
❌ pytest 衝突     ✓ pytest 互換
❌ フラグバグ      ✓ 堅牢

═════════════════════════════════════════════════
```

→ [EXPLAIN08：型チェック実装を詳しく](EXPLAIN08.md)
