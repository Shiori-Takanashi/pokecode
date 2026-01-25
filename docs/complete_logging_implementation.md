# ロギングテスト隔離の実装：問題から解決まで【完全な実装記録】

目次：
1. [問題の発見](#問題の発見)
2. [根本原因の分析](#根本原因の分析)
3. [初期の解決策の検討](#初期の解決策の検討)
4. [conftest.py の導入](#conftest.pyの導入)
5. [グローバルフラグの問題](#グローバルフラグの問題)
6. [最終的な実装](#最終的な実装)

---

# 問題の発見

## 初期状態：テスト失敗

```
FAILED tests/test_logconfig.py::test_setup_logging_smoke - AssertionError: assert False
FAILED tests/test_logconfig.py::test_setup_logging_creates_file - AssertionError: assert False
```

両テストともログファイルが作成されていない状態でスタートしました。

### テストの内容

```python
def test_setup_logging_smoke(tmp_path):
    from pokecode.logconfig import setup_logging

    setup_logging(logdir=tmp_path, logname="test.log")

    log_file = tmp_path / "test.log"
    assert log_file.exists()  # ← ファイルが存在しない


def test_setup_logging_creates_file(tmp_path):
    from pokecode.logconfig import setup_logging
    import logging

    setup_logging(logdir=tmp_path, logname="test.log")

    logging.getLogger(__name__).info("hello")

    assert (tmp_path / "test.log").exists()  # ← ファイルが存在しない
```

---

# 根本原因の分析

## 問題1：二重初期化防止ガード機構の欠陥

### 当初の logconfig.py

```python
def setup_logging(...) -> None:
    root = logging.getLogger()

    if root.handlers:
        return  # ← 問題：ハンドラーが存在するとリターン
```

### テスト実行の流れで何が起きたか

```
テスト1 実行
├─ root.handlers = []（最初は空）
├─ if root.handlers: → False（スキップ）
├─ ハンドラー追加実行 ✓
└─ ログファイル作成 ✓

テスト2 実行
├─ root.handlers = [前回のハンドラー]（生きている！）
├─ if root.handlers: → True（早期リターン）
├─ ハンドラー追加されない ✗
└─ ログファイル作成されない ✗
```

### 検証実験

Python シェルで連続2回の `setup_logging()` を呼び出した結果：

```
First call - Temp dir: /tmp/tmpmcu7uhqq
First call - Root handlers: 2

Second call - Temp dir: /tmp/tmpdh0w74ji
Second call - Root handlers: 2
Second call - File exists: False  ← ファイルが作成されない
```

**結論：** ロギングシステムはプロセス全体で共有されるため、テスト間でハンドラーが残存する。

---

## 問題2：pytest の内部ハンドラーとの衝突（後で発覚）

後のステップで判明することですが、pytest 自体が以下のハンドラーを追加します：

```
pytest 内部ハンドラー：
├─ _LiveLoggingNullHandler
├─ _FileHandler /dev/null
├─ LogCaptureHandler (x2)
└─ 合計4個

pokecode のハンドラー：
├─ StreamHandler
└─ TimedRotatingFileHandler
```

この衝突を正しく処理する必要があります。

---

# 初期の解決策の検討

## オプション1：テスト側でハンドラーをクリア（採択）

```python
@pytest.fixture(autouse=True)
def reset_logging():
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    yield
```

**判断：** ✅ ライブラリ関数（logconfig.py）は本番環境の要件に応じて設計すべき。テスト隔離はテスト側で管理する方が責務分離として正しい。

### 理由：

1. **ライブラリ関数として適切** - 提供側は本番シングルプロセスを想定
2. **本番環境への影響ゼロ** - app.py では setup_logging() は1回のみ呼び出し
3. **テストの責務** - テストが自身の隔離を管理するのが基本原則

## オプション2：ガード機構の改善（非採択）

```python
# ハンドラーの存在チェックだけでなく、
# 別のハンドラー再設定に対応する
```

**判断：** ❌ 非推奨。本番環境で誤ってログ設定を複数回呼び出した時、ハンドラーが重複する可能性。

## オプション3：グローバルフラグ（初期採択→後で廃止）

```python
_LOGGING_INITIALIZED = False

def setup_logging(..., force: bool = False) -> None:
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED and not force:
        return
```

**判断：** ⚠️ 一見良さそうだが、後で重大な問題が判明。

---

# conftest.py の導入

## conftest.py とは

`conftest.py` は **pytest が自動的に認識する共有設定ファイル** です。このファイルのフィクスチャは、同じディレクトリ以下の全テストで自動的に使用可能になります。

## ファイル構造

```
tests/
├─ conftest.py  ← pytest が自動認識（ファイル名は正確に）
└─ test_logconfig.py
```

## 初期実装（グローバルフラグを使用）

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def reset_root_logger():
    """各テスト実行前後でルートロガーをリセット"""
    import pokecode.logconfig

    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level

    for h in original_handlers:
        root.removeHandler(h)
        h.close()

    root.setLevel(logging.NOTSET)
    pokecode.logconfig._LOGGING_INITIALIZED = False  # ← グローバルフラグをリセット

    yield

    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()

    for h in original_handlers:
        root.addHandler(h)

    root.setLevel(original_level)
    pokecode.logconfig._LOGGING_INITIALIZED = False
```

### この時点でのテスト結果

```
✓ 2 passed in 0.03s
```

テストは通りました。しかし、この実装には隠れた問題が...

---

# グローバルフラグの問題

## ユーザーからの指摘

> 「その書き方は『一見もっともらしいが、実務的には避けるべき』です。理由は**管理対象が間違っている**点です。」

## グローバルフラグ実装の問題点

### 1. 仮想的な状態管理

```
問題：「初期化済みか」という仮想的な状態をフラグで追跡
└─ フラグと実体（ハンドラー）の不整合の可能性
```

### 2. 隠れたバグの例

conftest で `_LOGGING_INITIALIZED = False` のリセットを忘れた場合：

```python
# 不完全な conftest
@pytest.fixture(autouse=True)
def reset_root_logger():
    root = logging.getLogger()

    # ハンドラーはリセット
    for h in root.handlers[:]:
        root.removeHandler(h)

    # グローバルフラグのリセットを忘れた！
    # pokecode.logconfig._LOGGING_INITIALIZED = False  ← 実装漏れ

    yield

結果：
テスト2で setup_logging() が呼ばれる
  ↓
グローバルフラグが True のまま
  ↓
早期リターン（ハンドラー追加されない）
  ↓
テスト失敗（原因が分かりにくい）
```

### 3. 密結合

conftest が `logconfig._LOGGING_INITIALIZED` に依存

```python
pokecode.logconfig._LOGGING_INITIALIZED = False
                    ↑
        モジュール内部に直接アクセス
```

logconfig の内部実装が変更されると conftest も修正が必要。

### 4. pytest 非互換

pytest が追加する 4 つのハンドラーとの区別が困難

```
pytest handlers: [_LiveLoggingNullHandler, _FileHandler, LogCaptureHandler, ...]
pokecode handlers: [StreamHandler, TimedRotatingFileHandler]

グローバルフラグだけでは「どの」ハンドラーが対象か不明確
```

---

# 最終的な実装

## デバッグプロセス

テストがまだ失敗している状態から、原因を追跡しました：

```
[conftest] Initial state - handlers: 4
  Handler 0: <_LiveLoggingNullHandler>
  Handler 1: <_FileHandler /dev/null>
  Handler 2: <LogCaptureHandler>
  Handler 3: <LogCaptureHandler>

[conftest] After cleanup - handlers: 0, level: 0

[test] Before setup_logging - tmp_path: /tmp/pytest-of-tani09/...

[logconfig] setup_logging called, root.handlers: 2
[logconfig] Early return due to handlers  ← pytest がハンドラーを再度追加！
```

**発見：** pytest は conftest cleanup 後に再びハンドラーを追加していた！

## 改善：管理対象を「物理的実体」に変更

### logconfig.py（最終版）

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
                return  # 既に同じファイルパスのハンドラーがあれば何もしない

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

### conftest.py（最終版）

```python
from logging.handlers import TimedRotatingFileHandler

@pytest.fixture(autouse=True)
def reset_root_logger():
    """テスト隔離用ロガーリセット（pokecode の TimedRotatingFileHandler のみ）"""
    root = logging.getLogger()

    # TimedRotatingFileHandler のみを選別（pytest のハンドラーは触らない）
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

## 改善のポイント

### 1. グローバルフラグの廃止

```
❌ 改善前：_LOGGING_INITIALIZED = True  （仮想的な状態）
✓ 改善後：root.handlers に TimedRotatingFileHandler が存在  （物理的な事実）
```

### 2. 密結合の排除

```
❌ 改善前：pokecode.logconfig._LOGGING_INITIALIZED
✓ 改善後：isinstance(handler, TimedRotatingFileHandler)
         （標準ライブラリのみ依存）
```

### 3. pytest 互換性

```
❌ 改善前：全ハンドラーをリセット＆グローバルフラグで判定
✓ 改善後：TimedRotatingFileHandler だけを選別削除
         （pytest のハンドラーは残る）
```

## 最終テスト結果

```
================================================ test session starts =================================================
tests/test_logconfig.py::test_setup_logging_smoke PASSED                                                       [ 50%]
tests/test_logconfig.py::test_setup_logging_creates_file PASSED                                                [100%]

================================================= 2 passed in 0.02s ==================================================
```

✅ **完全成功**

---

# 設計原則

## 「管理対象が間違っている」の意味

### ❌ グローバルフラグで管理

```
管理対象 = 「初期化済みか」という仮想的な状態
    ↓
フラグは嘘をつく可能性がある
    ↓
ハンドラー実体 ≠ フラグの状態
    ↓
予期しない動作・隠れたバグ
```

### ✓ ハンドラー実体で管理

```
管理対象 = 「TimedRotatingFileHandler が存在するか」という物理的事実
    ↓
ハンドラーそのものが「存在する」ことを証明
    ↓
ハンドラー実体 = 論理的状態（必ず一致）
    ↓
堅牢で保守性が高い
```

## 実務での判断基準

### グローバルフラグが正当な場合

実務ではほぼない。以下は稀：

- **確実に単一インスタンス化が必要** → ただし設計の方が悪い兆候
- **パフォーマンス最適化** → コストが本当に大きい場合のみ（ただし構造を見直すべき）

### ハンドラー（実体）で管理すべき場合

実務の大部分：

- **logging のような状態管理** → 既に handlers リストで状態が管理されている
- **リソースの可視性** → 何が追加されているか物理的に確認可能
- **テスト隔離** → 実体を削除すれば conftest の管理が完結
- **疎結合性** → モジュール間の依存が最小化される

---

# 開発教訓

> **「一見もっともらしい抽象化（グローバルフラグ）より、物理的な実体（ハンドラー）を直接見る方が、堅牢で保守性が高い」**

設計時に自問すべき4つの質問：

1. **管理対象は何か？**
   - ハンドラー（実体）か、フラグ（抽象化）か

2. **外部から見えるか？**
   - デバッグ時に状態を確認できるか

3. **密結合していないか？**
   - モジュール内部に依存していないか

4. **テスト性は高いか？**
   - 仮想的な状態操作が必要ないか

**これらを満たすなら、その設計は実務的に堅牢です。**

---

# タイムライン

| 時刻 | イベント | 状態 |
|------|---------|------|
| T1 | テスト失敗を発見 | ❌ 2 failed |
| T2 | root.handlers チェックによる早期リターンが原因と特定 | 🔍 分析中 |
| T3 | オプション1（conftest でハンドラー削除）を選択 | ✓ 採択 |
| T4 | conftest.py にグローバルフラグリセットを追加 | ✓ 2 passed |
| T5 | ユーザーから「グローバルフラグは避けるべき」の指摘 | ⚠️ 警告 |
| T6 | pytest 内部ハンドラーとの衝突を発見 | 🔍 再分析 |
| T7 | 管理対象を「物理的実体」に変更 | ✓ 改善 |
| T8 | TimedRotatingFileHandler 型チェックに変更 | ✓ 2 passed |
| T9 | ドキュメント整備 | ✅ 完了 |

---

# 参考資料

- [logconfig.py](/src/pokecode/logconfig.py) - ロギング設定
- [conftest.py](/tests/conftest.py) - テスト隔離フィクスチャ
- [test_logconfig.py](/tests/test_logconfig.py) - テストファイル
- [conftest_guide.md](/docs/conftest_guide.md) - conftest.py の詳細ガイド
- [why_global_flags_are_bad.md](/docs/why_global_flags_are_bad.md) - グローバルフラグの問題
