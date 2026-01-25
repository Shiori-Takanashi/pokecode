# EXPLAIN06：pytest 内部ハンドラーの衝突を発見する

**時刻：T6 | 状態：🔍 再分析**

---

## 問題：テストが再び失敗した

EXPLAIN05 の指摘を受けて、グローバルフラグを廃止し、ハンドラーの実体をチェックする実装に変更しました。

ところが、テストがまた失敗してしまいました。

```
FAILED tests/test_logconfig.py::test_setup_logging_smoke - AssertionError: assert False
FAILED tests/test_logconfig.py::test_setup_logging_creates_file - AssertionError: assert False
```

---

## デバッグプロセス

### ステップ1：conftest に詳細ログを追加

```python
@pytest.fixture(autouse=True)
def reset_root_logger():
    root = logging.getLogger()

    print(f"[conftest] Initial state - handlers: {len(root.handlers)}")
    for i, h in enumerate(root.handlers):
        print(f"  Handler {i}: {h}")
```

### ステップ2：実行して出力を見る

```
[conftest] Initial state - handlers: 4
  Handler 0: <_LiveLoggingNullHandler (NOTSET)>
  Handler 1: <_FileHandler /dev/null (NOTSET)>
  Handler 2: <LogCaptureHandler (NOTSET)>
  Handler 3: <LogCaptureHandler (NOTSET)>
```

**発見：** pytest が自動的に 4 つのハンドラーを追加している！

### ステップ3：conftest の cleanup 後

```python
for h in original_handlers:
    root.removeHandler(h)

root.setLevel(logging.NOTSET)

print(f"[conftest] After cleanup - handlers: {len(root.handlers)}, level: {root.level}")
```

出力：

```
[conftest] After cleanup - handlers: 0, level: 0
```

**確認：** cleanup は成功している

### ステップ4：テスト前の状態確認

```python
# テスト内で
print(f"[test] Before setup_logging - handlers: {len(root.handlers)}")
```

出力：

```
[test] Before setup_logging - handlers: 2
[logconfig] setup_logging called, root.handlers: 2
[logconfig] Early return due to handlers
```

**衝撃：** conftest cleanup 直後は 0 個だったのに、テスト実行時には 2 個に増えている！

---

## 原因の特定

### タイムライン

```
conftest setup（cleanup）
    ↓
handlers: 0  ← 空

      ← テストの実行準備？

test 実行開始
    ↓
handlers: 2  ← 増えてる！
```

### 何が起きたのか

```
conftest setup で handlers をリセット
    ↓
pytest が「ログ capture のため」にハンドラーを追加
    ↓
その後、テスト実行
```

**pytest は、テスト実行時にログをキャプチャするためハンドラーを自動追加している！**

---

## pytest 内部ハンドラーの一覧

### デバッグ出力から判明した内容

```
pytest が追加するハンドラー：

1. _LiveLoggingNullHandler
   目的：stdout/stderr へのログ出力管理

2. _FileHandler /dev/null
   目的：テスト中のログファイル保存（一時的）

3. LogCaptureHandler（2個）
   目的：各テストのログをキャプチャして表示
```

### 通常の root.handlers の状態

```
root.handlers = [
    _LiveLoggingNullHandler (pytest),
    _FileHandler (pytest),
    LogCaptureHandler (pytest),
    LogCaptureHandler (pytest),
    StreamHandler (pokecode),          ← 自分たちのハンドラー
    TimedRotatingFileHandler (pokecode) ← 自分たちのハンドラー
]
```

---

## 問題のメカニズム

### 不完全なコード（改善前）

```python
# logconfig.py
def setup_logging(...) -> None:
    root = logging.getLogger()

    if root.handlers:  # ← pytest のハンドラーがあればスキップ
        return
```

### 実行フロー

```
conftest：
  root.handlers = []  （cleanup）
    ↓
pytest：
  root.handlers = [pytest のハンドラー 4 個]  （自動追加）
    ↓
test：
  setup_logging() 呼び出し
    ↓
  if root.handlers:  → True（pytest のハンドラーがある）
    ↓
  早期リターン  ← ❌ 問題！
    ↓
  pokecode のハンドラーが追加されない
    ↓
  ログファイル作成されない
```

---

## 解決のヒント

この問題を解決するには：

```
❌ 「ハンドラーが存在するか」で判定
   → pytest のハンドラーに引っかかる

✓ 「自分たちのハンドラー（TimedRotatingFileHandler）が存在するか」で判定
   → pytest のハンドラーとの区別可能
```

---

## 重要な気づき

> **ハンドラーの「種類」を区別することが重要**

```python
# 改善版の考え方
for handler in root.handlers:
    if isinstance(handler, TimedRotatingFileHandler):
        # 自分たちのハンドラーだけを判定
        # pytest のハンドラーは無視
```

→ [EXPLAIN07：最終実装へ向けて](EXPLAIN07.md)
