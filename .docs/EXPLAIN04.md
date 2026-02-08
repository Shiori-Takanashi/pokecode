# EXPLAIN04：conftest.py を導入する

**時刻：T4 | 状態：✓ 2 passed**

---

## conftest.py とは

```
tests/
├─ conftest.py  ← pytest が自動認識
└─ test_logconfig.py
```

### 特徴

- **pytest が自動的に認識する** ファイル名（正確に `conftest.py`）
- ここで定義した **fixture は全テストで使用可能**
- `autouse=True` にするとテスト実行前後で **自動実行**

## なぜ conftest が必要か

「テスト側でハンドラーをクリア」するなら、毎回こう書く必要があります：

```python
# 各テストで毎回...
def test_setup_logging_smoke(tmp_path):
    # テスト前の準備
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # テスト本体
    setup_logging(logdir=tmp_path, logname="test.log")
    assert log_file.exists()

    # テスト後の片付け
    for handler in root.handlers[:]:
        root.removeHandler(handler)
```

**同じコードが何度も書かれる** = 悪い設計

conftest を使えば、一度だけ書いて全テストに適用できます。

## fixture の仕組み

### 基本形

```python
@pytest.fixture(autouse=True)
def fixture_name():
    # セットアップ（テスト前）
    print("Before test")

    yield  # ← ここでテストが実行される

    # クリーンアップ（テスト後）
    print("After test")
```

### 実行フロー

```
pytest 開始
    ↓
fixture: Before test  （セットアップ）
    ↓
test_foo() 実行  （テスト本体）
    ↓
fixture: After test  （クリーンアップ）
    ↓
test_bar() へ移動
```

## 実装版 conftest.py（グローバルフラグ使用版）

```python
# tests/conftest.py
import logging
import pytest

@pytest.fixture(autouse=True)
def reset_root_logger():
    """各テスト実行前後でルートロガーをリセット"""
    import pokecode.logconfig

    root = logging.getLogger()

    # ========== セットアップ（テスト前） ==========
    original_handlers = root.handlers[:]  # 元の状態を保存
    original_level = root.level

    # ハンドラーを削除
    for h in original_handlers:
        root.removeHandler(h)
        h.close()  # ファイルディスクリプタをクローズ

    # ロガーをリセット
    root.setLevel(logging.NOTSET)

    # グローバルフラグもリセット
    pokecode.logconfig._LOGGING_INITIALIZED = False

    # ========== テスト実行 ==========
    yield

    # ========== クリーンアップ（テスト後） ==========
    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()

    # 元の状態に復旧
    for h in original_handlers:
        root.addHandler(h)

    root.setLevel(original_level)
    pokecode.logconfig._LOGGING_INITIALIZED = False
```

## テスト側は シンプルに

conftest のおかげで、テストは単純になります：

```python
def test_setup_logging_smoke(tmp_path):
    from pokecode.logconfig import setup_logging

    # conftest の fixture が自動的に実行される
    # セットアップは完了している

    setup_logging(logdir=tmp_path, logname="test.log")

    log_file = tmp_path / "test.log"
    assert log_file.exists()

    # テスト終了時、fixture がクリーンアップを実行
```

## テスト結果

```
================================================ test session starts =================================================
tests/test_logconfig.py::test_setup_logging_smoke PASSED                                                       [ 50%]
tests/test_logconfig.py::test_setup_logging_creates_file PASSED                                                [100%]

================================================= 2 passed in 0.03s ==================================================
```

✅ **成功！**

---

## この時点での課題（後で判明）

conftest の実装には `pokecode.logconfig._LOGGING_INITIALIZED = False` が含まれています。

```python
pokecode.logconfig._LOGGING_INITIALIZED = False
                    ↑
            モジュール内部をアクセス
```

### 問題点

1. **conftest が logconfig の内部実装に依存** → 密結合
2. **グローバルフラグを外部から操作** → カプセル化違反
3. **リセットを忘れるとバグに** → 脆弱性

これらの問題は、後でユーザーの指摘により明らかになります。

→ [EXPLAIN05：グローバルフラグの問題に気づく](EXPLAIN05.md)
