# CASE01：StreamHandler の増殖を確認する

**目的：テスト実行ごとに StreamHandler が増えていく現象を実証**

---

## 問題の要約

```
pytest を実行するたびに、root logger の StreamHandler が増殖する現象
├─ 1回目の実行：StreamHandler × 1
├─ 2回目の実行：StreamHandler × 2
├─ 3回目の実行：StreamHandler × 3
└─ N回目の実行：StreamHandler × N
```

---

## 確認方法 1：ログ出力で確認（目視）

### テストコード

```python
# tests/test_handler_duplicate.py
import logging
from pokecode.logconfig import setup_logging


def test_check_stream_handler_duplication_simple():
    """
    StreamHandler の増殖を目視で確認するテスト

    実行方法：
    pytest tests/test_handler_duplicate.py::test_check_stream_handler_duplication_simple -v -s

    複数回実行して、ログ出力が増えるのを確認：
    1回目：[ログが 1回出力]
    2回目：[ログが 2回出力]
    3回目：[ログが 3回出力]
    """
    setup_logging()

    # 同じメッセージを出力
    logger = logging.getLogger("test")
    logger.info("Test message")

    # root logger の StreamHandler をすべてカウント
    root = logging.getLogger()
    stream_handlers = [
        h for h in root.handlers
        if isinstance(h, logging.StreamHandler)
    ]

    print(f"\n📊 StreamHandler count: {len(stream_handlers)}")
    for i, h in enumerate(stream_handlers):
        print(f"  [{i+1}] {type(h).__name__} - stream: {h.stream}")
```

### 実行結果の例

```
pytest を 3回連続実行した場合

1回目:
test_handler_duplicate.py::test_check_stream_handler_duplication_simple -v -s
...
Test message     ← ログが 1回出力
📊 StreamHandler count: 1
  [1] StreamHandler - stream: <_io.TextIOWrapper name='<stdout>' ...>

2回目:
test_handler_duplicate.py::test_check_stream_handler_duplication_simple -v -s
...
Test message     ← ログが 2回出力！
Test message
📊 StreamHandler count: 2
  [1] StreamHandler - stream: <_io.TextIOWrapper name='<stdout>' ...>
  [2] StreamHandler - stream: <_io.TextIOWrapper name='<stdout>' ...>

3回目:
test_handler_duplicate.py::test_check_stream_handler_duplication_simple -v -s
...
Test message     ← ログが 3回出力！！
Test message
Test message
📊 StreamHandler count: 3
  [1] StreamHandler - stream: <_io.TextIOWrapper name='<stdout>' ...>
  [2] StreamHandler - stream: <_io.TextIOWrapper name='<stdout>' ...>
  [3] StreamHandler - stream: <_io.TextIOWrapper name='<stdout>' ...>
```

---

## 確認方法 2：プログラム的に確認（テスト内で検証）

### テストコード

```python
# tests/test_handler_duplicate.py
import logging
import pytest
from pokecode.logconfig import setup_logging
from logging.handlers import TimedRotatingFileHandler


def test_stream_handler_count_in_single_session():
    """
    単一セッション内で StreamHandler がどう増えるかを確認

    実行方法：
    pytest tests/test_handler_duplicate.py::test_stream_handler_count_in_single_session -v
    """
    root = logging.getLogger()

    # setup_logging 前
    stream_before = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        not isinstance(h, TimedRotatingFileHandler)
    )
    print(f"\n前：StreamHandler × {stream_before}")

    # setup_logging を実行
    setup_logging()

    # setup_logging 後
    stream_after = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        not isinstance(h, TimedRotatingFileHandler)
    )
    print(f"後：StreamHandler × {stream_after}")

    # 期待値：1 つだけ追加されるはず（重複なし）
    assert stream_after == stream_before + 1, \
        f"StreamHandler が {stream_after - stream_before} 個追加された（期待値：1 個）"


def test_stream_handler_duplicates_on_setup_logging_multiple_calls():
    """
    同じセッション内で setup_logging を複数回呼んだ場合の動作

    実行方法：
    pytest tests/test_handler_duplicate.py::test_stream_handler_duplicates_on_setup_logging_multiple_calls -v

    期待動作：
    - 2 回目の呼び出しでは、既存の TimedRotatingFileHandler を検出して早期リターン
    - StreamHandler は追加されない（重複しない）

    ただし conftest がないと：
    - StreamHandler がどんどん増える
    """
    root = logging.getLogger()

    # 初期状態
    setup_logging()
    count_1 = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        not isinstance(h, TimedRotatingFileHandler)
    )
    print(f"\n1回目：StreamHandler × {count_1}")

    # 2 回目
    setup_logging()
    count_2 = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        not isinstance(h, TimedRotatingFileHandler)
    )
    print(f"2回目：StreamHandler × {count_2}")

    # 3 回目
    setup_logging()
    count_3 = sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and
        not isinstance(h, TimedRotatingFileHandler)
    )
    print(f"3回目：StreamHandler × {count_3}")

    # 同じセッション内では setup_logging 内の早期リターンで増えないはず
    # （ただし、conftest がハンドラーをリセットしていれば）
    assert count_1 == count_2 == count_3, \
        f"同じセッション内でも StreamHandler が増えた：{count_1} → {count_2} → {count_3}"
```

---

## 確認方法 3：異なるテストセッション間での増殖確認

### テストコード

```python
# tests/test_handler_duplicate.py
import logging
import pytest
from pokecode.logconfig import setup_logging


@pytest.mark.parametrize("test_num", [1, 2, 3])
def test_stream_handler_count_across_sessions(test_num):
    """
    複数のテストセッション（パラメータ化）で StreamHandler がどう増えるかを確認

    実行方法：
    pytest tests/test_handler_duplicate.py::test_stream_handler_count_across_sessions -v

    出力例：
    test_handler_duplicate.py::test_stream_handler_count_across_sessions[1] PASSED
    [Session 1] StreamHandler × 1

    test_handler_duplicate.py::test_stream_handler_count_across_sessions[2] PASSED
    [Session 2] StreamHandler × 2  ← 増えてる！

    test_handler_duplicate.py::test_stream_handler_count_across_sessions[3] PASSED
    [Session 3] StreamHandler × 3  ← さらに増えてる！
    """
    setup_logging()

    root = logging.getLogger()
    stream_handlers = [
        h for h in root.handlers
        if isinstance(h, logging.StreamHandler)
    ]

    count = len(stream_handlers)
    print(f"\n[Session {test_num}] StreamHandler × {count}")

    # 本来はこれが失敗するはず（conftest がない場合）
    # conftest で reset_root_logger fixture があれば、毎回 1 になる
    # conftest がなければ、1 → 2 → 3 と増える
```

---

## 確認方法 4：詳細な診断コード

### テストコード（最も詳しい）

```python
# tests/test_handler_duplicate.py
import logging
import sys
from pokecode.logconfig import setup_logging
from logging.handlers import TimedRotatingFileHandler


def test_detailed_handler_diagnosis():
    """
    root logger のハンドラー全体を詳しく診断

    実行方法：
    pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s
    """
    print("\n" + "="*60)
    print("🔍 ハンドラー診断レポート")
    print("="*60)

    root = logging.getLogger()

    print(f"\n📊 合計ハンドラー数：{len(root.handlers)}")

    stream_handlers = []
    file_handlers = []
    other_handlers = []

    for i, h in enumerate(root.handlers):
        handler_info = {
            'index': i,
            'type': type(h).__name__,
            'instance': h,
        }

        if isinstance(h, TimedRotatingFileHandler):
            file_handlers.append(handler_info)
        elif isinstance(h, logging.StreamHandler):
            stream_handlers.append(handler_info)
            handler_info['stream'] = getattr(h, 'stream', None)
            handler_info['formatter'] = h.formatter
        else:
            other_handlers.append(handler_info)

    # StreamHandler の詳細
    print(f"\n✅ StreamHandler × {len(stream_handlers)}")
    for info in stream_handlers:
        print(f"  [{info['index']}] {info['type']}")
        print(f"      stream: {info['stream']}")
        if info['formatter']:
            print(f"      format: {info['formatter']._fmt[:50]}...")

    # TimedRotatingFileHandler の詳細
    print(f"\n📁 TimedRotatingFileHandler × {len(file_handlers)}")
    for info in file_handlers:
        h = info['instance']
        print(f"  [{info['index']}] {info['type']}")
        print(f"      file: {h.baseFilename}")

    # その他のハンドラー
    if other_handlers:
        print(f"\n❓ その他のハンドラー × {len(other_handlers)}")
        for info in other_handlers:
            print(f"  [{info['index']}] {info['type']}")

    # 実行前後での動作確認
    print("\n" + "-"*60)
    print("🔄 setup_logging() を実行...\n")

    setup_logging()

    # 実行後の状態
    root_after = logging.getLogger()
    stream_handlers_after = [
        h for h in root_after.handlers
        if isinstance(h, logging.StreamHandler)
    ]

    print(f"\n📊 setup_logging() 後の StreamHandler：× {len(stream_handlers_after)}")

    print("\n" + "="*60)

    # 推奨：conftest.py で reset_root_logger fixture がないと
    # このテストを複数回実行すると StreamHandler が増える
```

---

## 実行手順

### ステップ 1：テストファイルを作成

```bash
# テストコードを tests/test_handler_duplicate.py に作成
```

### ステップ 2：**conftest なし** で実行（増殖を確認）

```bash
cd /home/tani09/snk-projects/pokecode

# pytest キャッシュをクリア
rm -rf .pytest_cache __pycache__ tests/__pycache__

# テストを実行（1回目）
pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s

# テストを実行（2回目）
pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s

# テストを実行（3回目）
pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s
```

**結果：** StreamHandler × 1 → × 2 → × 3 と増える

### ステップ 3：conftest.py で修正（増殖を停止）

```python
# tests/conftest.py
import logging
import pytest


@pytest.fixture(autouse=True)
def reset_root_logger():
    """テスト隔離用ロガーリセット"""
    root = logging.getLogger()

    pokecode_handlers = [
        h for h in root.handlers
        if hasattr(h, '_pokecode_managed') and h._pokecode_managed
    ]

    for h in pokecode_handlers:
        root.removeHandler(h)
        h.close()

    yield

    pokecode_handlers = [
        h for h in root.handlers
        if hasattr(h, '_pokecode_managed') and h._pokecode_managed
    ]

    for h in pokecode_handlers:
        root.removeHandler(h)
        h.close()
```

### ステップ 4：修正後に実行（増殖が停止することを確認）

```bash
# テストを実行（1回目）
pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s

# テストを実行（2回目）
pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s

# テストを実行（3回目）
pytest tests/test_handler_duplicate.py::test_detailed_handler_diagnosis -v -s
```

**結果：** StreamHandler × 1 → × 1 → × 1 と一定に保たれる

---

## 予想される出力

### conftest **なし**（問題がある状態）

```
🔍 ハンドラー診断レポート
============================================================

📊 合計ハンドラー数：2

✅ StreamHandler × 1
  [0] StreamHandler
      stream: <_io.TextIOWrapper name='<stdout>' mode='w' encoding='utf-8'>
      format: %(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s

📁 TimedRotatingFileHandler × 1
  [1] TimedRotatingFileHandler
      file: /home/tani09/snk-projects/pokecode/logs/app.log

============================================================

2回目実行時：

📊 合計ハンドラー数：4

✅ StreamHandler × 2  ← 増えた！
  [0] StreamHandler
  [1] StreamHandler

📁 TimedRotatingFileHandler × 2  ← これも増えた！
  [2] TimedRotatingFileHandler
  [3] TimedRotatingFileHandler
```

### conftest **あり**（修正済み状態）

```
🔍 ハンドラー診断レポート
============================================================

📊 合計ハンドラー数：2

✅ StreamHandler × 1
  [0] StreamHandler
      stream: <_io.TextIOWrapper name='<stdout>' mode='w' encoding='utf-8'>
      format: %(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s

📁 TimedRotatingFileHandler × 1
  [1] TimedRotatingFileHandler
      file: /home/tani09/snk-projects/pokecode/logs/app.log

============================================================

2回目実行時：

📊 合計ハンドラー数：2  ← 変わらない！

✅ StreamHandler × 1  ← 増えていない
  [0] StreamHandler

📁 TimedRotatingFileHandler × 1  ← 増えていない
  [1] TimedRotatingFileHandler
```

---

## まとめ

| 項目 | 説明 |
|------|------|
| **確認方法 1** | 目視で重複ログの増加を見る（最もわかりやすい） |
| **確認方法 2** | プログラムで StreamHandler の数を検証 |
| **確認方法 3** | パラメータ化テストで複数セッションをシミュレート |
| **確認方法 4** | 詳細な診断レポートを生成 |

最も実証的な検証は **確認方法 1**（目視）と **確認方法 4**（詳細診断）の組み合わせです。

→ [EXPLAIN10：StreamHandler の重複問題と解決策](EXPLAIN10.md)
