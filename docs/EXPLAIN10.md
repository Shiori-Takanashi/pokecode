# EXPLAIN10：StreamHandler の重複問題と解決策

**時刻：T10 | 状態：🔍 新規発見**

---

## 問題の発見

### EXPLAIN07-09での盲点

EXPLAIN07～09では `TimedRotatingFileHandler` だけの削除を議論してきましたが、**StreamHandler も pokecode が追加するもの** です。

```python
# logconfig.py の現在の実装
stream = logging.StreamHandler(sys.stdout)
stream.setFormatter(formatter)
root.addHandler(stream)  ← 毎回追加される
```

---

## StreamHandler 重複の影響

### テスト実行時のハンドラー蓄積

```
初期状態：
  root.handlers = []

test_logconfig_A 実行：
  setup_logging() が呼ばれる
  → StreamHandler × 1 追加
  → TimedRotatingFileHandler × 1 追加
  root.handlers = [StreamHandler, TimedRotatingFileHandler]

conftest の reset_root_logger (teardown)：
  ✓ TimedRotatingFileHandler は削除
  ✗ StreamHandler は削除されない ← 問題！
  root.handlers = [StreamHandler]

test_logconfig_B 実行：
  setup_logging() が呼ばれる
  → StreamHandler × 1 追加（重複！）
  → TimedRotatingFileHandler × 1 追加
  root.handlers = [StreamHandler ×2, TimedRotatingFileHandler]

結果：
  ❌ 同じログメッセージが 2回、3回... と出力される
  ❌ テストが複数回走ると どんどん重複が増える
```

---

## 根本原因

### 現在の conftest.py の問題

```python
# tests/conftest.py（現在）
timed_rotating_handlers = [
    h for h in root.handlers
    if isinstance(h, TimedRotatingFileHandler)
]

for h in timed_rotating_handlers:
    root.removeHandler(h)
    h.close()

# ❌ StreamHandler は残ったまま
# ❌ 毎回の setup_logging() で新しい StreamHandler が追加される
```

---

## 解決策 1：型で削除（シンプル版）

### 問題点

`logging.StreamHandler` は pytest **自体も使う可能性**があります。

```
pytest のハンドラー：
├─ _LiveLoggingNullHandler
├─ _FileHandler
└─ LogCaptureHandler

pokecode のハンドラー：
├─ StreamHandler ← pytest も使うかもしれない
└─ TimedRotatingFileHandler ← pokecode のみ
```

単純に `isinstance(h, logging.StreamHandler)` で削除すると、pytest のハンドラーを誤って削除するリスクがあります。

---

## 解決策 2：カスタム属性でマーク（推奨）

### 設計

pokecode が追加したハンドラーに **カスタム属性を付ける** ことで、確実に識別します。

#### 1. logconfig.py を改善

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

    # 既存の pokecode ハンドラーを確認
    for handler in root.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            # 自分たちが付けた属性があるかチェック
            if hasattr(handler, '_pokecode_managed') and \
               Path(handler.baseFilename) == filepath:
                return  # 既に設定済み

    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = "%(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s"
    formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    # ✅ カスタム属性を付ける
    stream._pokecode_managed = True

    logdir.mkdir(exist_ok=True)

    fileh = TimedRotatingFileHandler(
        filepath,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding=None,
    )
    fileh.setFormatter(formatter)
    # ✅ カスタム属性を付ける
    fileh._pokecode_managed = True

    root.addHandler(stream)
    root.addHandler(fileh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
```

#### 2. conftest.py を改善

```python
# tests/conftest.py
import logging
import pytest


@pytest.fixture(autouse=True)
def reset_root_logger():
    """テスト隔離用ロガーリセット（pokecode のハンドラーのみ削除）"""
    root = logging.getLogger()

    # pokecode のハンドラーだけを削除（_pokecode_managed 属性で判定）
    pokecode_handlers = [
        h for h in root.handlers
        if hasattr(h, '_pokecode_managed') and h._pokecode_managed
    ]

    for h in pokecode_handlers:
        root.removeHandler(h)
        h.close()  # リソースクローズ

    yield

    # テスト後も同じ
    pokecode_handlers = [
        h for h in root.handlers
        if hasattr(h, '_pokecode_managed') and h._pokecode_managed
    ]

    for h in pokecode_handlers:
        root.removeHandler(h)
        h.close()
```

---

## 解決策 2 の利点

| 側面 | 説明 |
|------|------|
| **安全性** | ✓ pytest のハンドラーに影響しない |
| **識別確実性** | ✓ カスタム属性で確実に区別 |
| **拡張性** | ✓ 新しいハンドラー追加時もマークするだけ |
| **保守性** | ✓ conftest と logconfig の意図が明確 |
| **パフォーマンス** | ✓ hasattr チェックは軽量 |

---

## 実装の流れ

### Before（現在の実装）

```python
# logconfig.py
stream = logging.StreamHandler(sys.stdout)
root.addHandler(stream)  # マークなし

# conftest.py
timed_rotating_handlers = [
    h for h in root.handlers
    if isinstance(h, TimedRotatingFileHandler)
]
# ❌ StreamHandler は残ったまま
```

### After（推奨実装）

```python
# logconfig.py
stream = logging.StreamHandler(sys.stdout)
stream._pokecode_managed = True  # ✓ マークを付ける
root.addHandler(stream)

# conftest.py
pokecode_handlers = [
    h for h in root.handlers
    if hasattr(h, '_pokecode_managed') and h._pokecode_managed
]
# ✓ すべての pokecode ハンドラーを削除
```

---

## テスト例

### 改善後の動作確認

```python
# tests/test_logconfig.py
def test_no_duplicate_streams(reset_root_logger):
    """StreamHandler が重複しないことを確認"""
    import logging
    from pokecode.logconfig import setup_logging

    root = logging.getLogger()

    # テスト実行 1回目
    setup_logging()
    stream_count_1 = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        hasattr(h, '_pokecode_managed')
    )
    assert stream_count_1 == 1, "StreamHandler は 1 つだけ"

    # テスト実行 2回目（同じロガーで）
    setup_logging()
    stream_count_2 = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        hasattr(h, '_pokecode_managed')
    )
    assert stream_count_2 == 1, "StreamHandler はまだ 1 つ（重複していない）"
```

---

## 更新すべきファイル

| ファイル | 内容 |
|----------|------|
| [src/pokecode/logconfig.py](../src/pokecode/logconfig.py) | `_pokecode_managed` 属性の追加 |
| [tests/conftest.py](../tests/conftest.py) | hasattr チェックに更新 |

---

## まとめ

| 要点 | 説明 |
|------|------|
| **問題** | StreamHandler も毎回追加されて重複する |
| **原因** | conftest で TimedRotatingFileHandler だけ削除している |
| **解決策** | カスタム属性 `_pokecode_managed` でマーク |
| **効果** | pytest との衝突なく、完全な隔離が可能 |

→ [実装を完了させる](complete_logging_implementation.md)
