# EXPLAIN08：型チェック実装を詳しく解説

**時刻：T8 | 状態：✓ 2 passed**

---

## TimedRotatingFileHandler 型チェックの詳細

### なぜ型チェック（isinstance）を使うのか

```python
# ❌ ダメな判定方法
if root.handlers:
    return  # すべてのハンドラーを無差別に判定

# ✓ 良い判定方法
if isinstance(handler, TimedRotatingFileHandler):
    return  # 特定の型のハンドラーだけを判定
```

### Python の isinstance の仕組み

```python
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler("/var/log/app.log", when="midnight")

print(isinstance(handler, TimedRotatingFileHandler))
# 出力：True

# 別の型のハンドラー
stream_handler = logging.StreamHandler()

print(isinstance(stream_handler, TimedRotatingFileHandler))
# 出力：False
```

---

## logconfig.py の実装詳細

### Step 1：import の追加

```python
from logging.handlers import TimedRotatingFileHandler
```

この import により、`TimedRotatingFileHandler` という特定のクラスを参照できます。

### Step 2：ハンドラーの列挙ループ

```python
for handler in root.handlers:
    # root.handlers に登録されているすべてのハンドラーをループ
    # 例：
    # [_LiveLoggingNullHandler, _FileHandler, LogCaptureHandler,
    #  LogCaptureHandler, StreamHandler, TimedRotatingFileHandler]
```

### Step 3：型チェック

```python
if isinstance(handler, TimedRotatingFileHandler):
    # このハンドラーが TimedRotatingFileHandler 型か確認

    # 例：
    # _LiveLoggingNullHandler → False（スキップ）
    # _FileHandler → False（スキップ）
    # LogCaptureHandler → False（スキップ）
    # LogCaptureHandler → False（スキップ）
    # StreamHandler → False（スキップ）
    # TimedRotatingFileHandler → True（処理継続）
```

### Step 4：ファイルパスの比較

```python
if Path(handler.baseFilename) == filepath:
    # さらに、ハンドラーが指す実際のファイルパス
    # と今回設定しようとしているファイルパスが一致するか確認

    # TimedRotatingFileHandler のメンバ変数：
    # handler.baseFilename = "/tmp/test.log"
    # filepath = Path("/tmp/test.log")

    # 一致していれば、既に設定済みのハンドラーがある
    return
```

---

## 実行フロー（改善版）

### テスト1

```
test_setup_logging_smoke(tmp_path1="/tmp/pytest-xxx1")
    ↓
conftest setup:
    timed_rotating_handlers = []  （pytest のハンドラーのみ）
    ↓
setup_logging(logdir=tmp_path1, logname="test.log")
    filepath = /tmp/pytest-xxx1/test.log

    for handler in root.handlers:
        handler[0] = _LiveLoggingNullHandler
            isinstance(..., TimedRotatingFileHandler) → False

        handler[1] = _FileHandler
            isinstance(..., TimedRotatingFileHandler) → False

        handler[2] = LogCaptureHandler
            isinstance(..., TimedRotatingFileHandler) → False

        handler[3] = LogCaptureHandler
            isinstance(..., TimedRotatingFileHandler) → False

        handler[4] = StreamHandler（新規追加）
            isinstance(..., TimedRotatingFileHandler) → False

        handler[5] = TimedRotatingFileHandler（新規追加）
            isinstance(..., TimedRotatingFileHandler) → True
                Path(handler.baseFilename) = /tmp/pytest-xxx1/test.log
                filepath = /tmp/pytest-xxx1/test.log
                一致？ いいえ（初回なので、このハンドラーが追加される）

    ハンドラーを追加する処理が実行される
    root.addHandler(stream)
    root.addHandler(fileh)

    ✓ ファイル作成される

conftest teardown:
    timed_rotating_handlers = [
        TimedRotatingFileHandler（/tmp/pytest-xxx1/test.log）
    ]
    削除処理実行
```

### テスト2

```
test_setup_logging_creates_file(tmp_path2="/tmp/pytest-xxx2")
    ↓
conftest setup:
    timed_rotating_handlers = [
        TimedRotatingFileHandler（/tmp/pytest-xxx1/test.log）← テスト1の残骸
    ]
    削除処理実行（テスト1のハンドラーを削除）
    ↓
setup_logging(logdir=tmp_path2, logname="test.log")
    filepath = /tmp/pytest-xxx2/test.log

    for handler in root.handlers:
        # pytest のハンドラーをループ（4個）
        handler = _LiveLoggingNullHandler
            isinstance(..., TimedRotatingFileHandler) → False

        handler = _FileHandler
            isinstance(..., TimedRotatingFileHandler) → False

        handler = LogCaptureHandler (x2)
            isinstance(..., TimedRotatingFileHandler) → False

        ✓ TimedRotatingFileHandler が見つからない
        ✓ ハンドラー追加処理が実行される

    root.addHandler(stream)
    root.addHandler(fileh)

    ✓ ファイル作成される

conftest teardown:
    timed_rotating_handlers = [
        TimedRotatingFileHandler（/tmp/pytest-xxx2/test.log）← テスト2のハンドラー
    ]
    削除処理実行
```

---

## 型チェックの利点を図解

```
root.handlers の内容：
┌─────────────────────────────────────────────┐
│ [0] _LiveLoggingNullHandler                 │
│ [1] _FileHandler(/dev/null)                 │
│ [2] LogCaptureHandler                       │
│ [3] LogCaptureHandler                       │
│ [4] StreamHandler                           │
│ [5] TimedRotatingFileHandler("/tmp/test.log")│
└─────────────────────────────────────────────┘
                    ↓
        isinstance チェック
                    ↓
┌─────────────────────────────────────────────┐
│                    ↓                         │
│ TimedRotatingFileHandler のみ抽出             │
│                    ↓                         │
│ [0] TimedRotatingFileHandler("/tmp/test.log")│
└─────────────────────────────────────────────┘
```

---

## conftest での型チェック

```python
# リスト内包表記で型チェック
timed_rotating_handlers = [
    h for h in root.handlers
    if isinstance(h, TimedRotatingFileHandler)
]

# 上記は以下と同等
timed_rotating_handlers = []
for h in root.handlers:
    if isinstance(h, TimedRotatingFileHandler):
        timed_rotating_handlers.append(h)
```

---

## 重要：ファイルパスの比較

### なぜファイルパスも比較するのか

同じ `TimedRotatingFileHandler` 型でも、複数の異なるファイルパスを指す可能性があります：

```python
# 例1：ログディレクトリ1
handler1 = TimedRotatingFileHandler("/var/log/app/app.log")

# 例2：ログディレクトリ2（同じプロセス内）
handler2 = TimedRotatingFileHandler("/var/log/audit/audit.log")

# 型だけでは区別できない
isinstance(handler1, TimedRotatingFileHandler)  # True
isinstance(handler2, TimedRotatingFileHandler)  # True

# ファイルパスで初めて区別できる
handler1.baseFilename  # "/var/log/app/app.log"
handler2.baseFilename  # "/var/log/audit/audit.log"
```

テストでも同様：

```python
# テスト1：tmp_path1/test.log
setup_logging(logdir=tmp_path1, logname="test.log")

# テスト2：tmp_path2/test.log
setup_logging(logdir=tmp_path2, logname="test.log")

# 同じファイル名だが、異なるパス → 別ハンドラーが必要
```

---

## テスト結果

```
================================================ test session starts =================================================
tests/test_logconfig.py::test_setup_logging_smoke PASSED                                                       [ 50%]
tests/test_logconfig.py::test_setup_logging_creates_file PASSED                                                [100%]

================================================= 2 passed in 0.02s ==================================================
```

✅ **完全成功**

→ [EXPLAIN09：設計原則とまとめ](EXPLAIN09.md)
