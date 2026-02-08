# PHASE04：ログシステムの StreamHandler 増殖問題の検証と修正

**目的**: StreamHandler の増殖問題を確認し、修正が有効に機能しているか検証

**進捗**: 🟡 開発中

---

## 1. 問題の概要（CASE01.md より）

### StreamHandler の増殖現象

`pytest` を実行するたびに、root logger の `StreamHandler` が増殖する：

```
1回目実行: log が 1回出力
2回目実行: log が 2回出力
3回目実行: log が 3回出力
N回目実行: log が N回出力
```

**原因**: `setup_logging()` が複数回呼ばれる際、新しい `StreamHandler` が毎回追加される

**現在の対策**: `logconfig.py` で handler.name を確認して重複を防いでいる

---

## 2. 現在の logconfig.py 実装の分析

### 重複チェックの流れ

```python
def setup_logging(
    *,
    logger: Logger,
    level: str = "INFO",
    logdir_name: str = "logs",
    logname: str = "app.log",
) -> None:
    logger.propagate = False
    logger.setLevel(resolved_level)

    # StreamHandler の重複チェック
    sh = None
    for h in logger.handlers:
        if isinstance(h, StreamHandler) and getattr(h, "name", None) == _CONSOLE_NAME:
            sh = h  # 既存のハンドラを再利用
            break

    if sh is None:  # 存在しなければ新規作成
        sh = StreamHandler()
        sh.name = _CONSOLE_NAME
        logger.addHandler(sh)

    sh.setFormatter(formatter)  # フォーマッタを設定
```

### 問題と改善点

**現在の作り**: handler の `name` 属性で重複を判定している
- ✅ 同じ名前の handler を再利用する
- ⚠️ handler.name が None になる可能性

**改善案**:
- handler.name を確実に設定
- エラーハンドリングの強化

---

## 3. テスト計画：StreamHandler 増殖の検証

### テストケース：複数回 setup_logging() を呼び出し

```python
# tests/test_logging_handler_duplication.py
import logging
from pokecode.logconfig import setup_logging


def test_stream_handler_not_duplicated_on_second_call():
    """2回目の setup_logging() で StreamHandler が増殖しないか確認"""

    # 1回目の setup_logging()
    logger1 = logging.getLogger("test_logger_1")
    setup_logging(logger=logger1)
    handlers_count_1 = len([h for h in logger1.handlers if isinstance(h, logging.StreamHandler)])
    assert handlers_count_1 == 1, f"Expected 1 StreamHandler, got {handlers_count_1}"

    # 2回目の setup_logging()（同じ logger）
    setup_logging(logger=logger1)
    handlers_count_2 = len([h for h in logger1.handlers if isinstance(h, logging.StreamHandler)])
    assert handlers_count_2 == 1, f"Expected 1 StreamHandler, got {handlers_count_2}"

    # ハンドラの内容が同じか確認
    print(f"1回目: {handlers_count_1}, 2回目: {handlers_count_2}")


def test_stream_handler_multiple_calls():
    """N回の setup_logging() でも StreamHandler が 1個に保たれるか"""

    logger = logging.getLogger("test_logger_multi")

    for i in range(5):
        setup_logging(logger=logger)
        handlers_count = len([h for h in logger.handlers if isinstance(h, logging.StreamHandler)])
        print(f"After call {i+1}: {handlers_count} StreamHandler(s)")
        assert handlers_count == 1, f"Call {i+1}: Expected 1, got {handlers_count}"
```

### テスト実行方法

```bash
# テストを実行
pytest tests/test_logging_handler_duplication.py -v -s

# 出力例
test_stream_handler_not_duplicated_on_second_call PASSED
test_stream_handler_multiple_calls PASSED
```

---

## 4. ロギングの詳細診断スクリプト

### logger の状態を詳しく確認するツール

```python
# tools/inspect_logger.py
import logging
from pokecode.logconfig import setup_logging


def inspect_logger(logger: logging.Logger) -> None:
    """logger の状態をダンプ"""
    print(f"\n=== Logger: {logger.name} ===")
    print(f"Level: {logging.getLevelName(logger.level)}")
    print(f"Propagate: {logger.propagate}")
    print(f"Handlers: {len(logger.handlers)}")

    for i, handler in enumerate(logger.handlers):
        print(f"\n  Handler {i}:")
        print(f"    Type: {type(handler).__name__}")
        print(f"    Name: {getattr(handler, 'name', '<no name>')}")
        print(f"    Level: {logging.getLevelName(handler.level)}")
        print(f"    Formatter: {handler.formatter}")


# 使用例
logger = logging.getLogger("pokecode")
setup_logging(logger=logger, level="INFO")
inspect_logger(logger)

setup_logging(logger=logger, level="DEBUG")
inspect_logger(logger)
```

---

## 5. 修正提案（もし問題が報告される場合）

### 現在の対策の強化版

```python
def setup_logging(
    *,
    logger: Logger,
    level: str = "INFO",
    logdir_name: str = "logs",
    logname: str = "app.log",
) -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(resolved_level)
    logger.propagate = False

    # StreamHandler の処理（現在のやり方を維持）
    sh = None
    for h in logger.handlers:
        if isinstance(h, logging.StreamHandler) and getattr(h, "name", None) == _CONSOLE_NAME:
            sh = h
            break

    if sh is None:
        sh = logging.StreamHandler()
        sh.name = _CONSOLE_NAME  # 必ず name を設定
        logger.addHandler(sh)

    sh.setFormatter(formatter)
    sh.setLevel(resolved_level)  # handler レベルも設定（推奨）

    # FileHandler の処理（同様に重複チェック）
    filepath = _resolve_logfile(logdir_name=logdir_name, logname=logname)

    fh = None
    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler) and getattr(h, "name", None) == _FILE_NAME:
            fh = h
            break

    if fh is None:
        fh = RotatingFileHandler(
            filepath,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
        )
        fh.name = _FILE_NAME  # 必ず name を設定
        logger.addHandler(fh)

    fh.setFormatter(formatter)
    fh.setLevel(resolved_level)
```

---

## 6. 実装チェックリスト（PHASE04）

- [ ] テストを実装（test_logging_handler_duplication.py）
- [ ] テスト実行（各パターンで検証）
- [ ] logger インスペクション スクリプト作成（tools/inspect_logger.py）
- [ ] 手動で複数回 setup_logging() を呼んで確認
- [ ] 問題がなければ現在の実装を採用
- [ ] 問題があれば修正提案を適用

---

## 7. ログ関連の既知ドキュメント

`.docs/` に既に以下が存在：

- **CASE01.md**: StreamHandler 増殖の確認方法
- **CASE02.md**: 別のログ問題（未確認）
- **CASE03.md**: 別のログ問題（未確認）

→ これらも参照して、全体的なログ解決状況を把握する必要がある

---

## 8. 次のステップ

✅ **PHASE04**: StreamHandler 問題の検証テストを実施

📋 **PHASE05**: 全体統合テストと最終整理

---
