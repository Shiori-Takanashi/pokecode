# conftest.py ガイド

## conftest とは

`conftest.py` は **pytest が自動的に認識する共有設定ファイル** です。このファイルに定義したフィクスチャは、同じディレクトリ以下の全テストで使用可能になります。

## ファイルの位置

```
tests/
  conftest.py  ← pytest が自動認識
  test_logconfig.py
```

## 当プロジェクトでの実装内容

### 目的

ロギングのテスト隔離を実現すること。複数のテストが互いに影響しないように、テスト実行前後でロガーの状態をリセットします。

### コード解説

```python
@pytest.fixture(autouse=True)
def reset_root_logger():
    """各テスト実行前後でルートロガーをリセット"""
    import pokecode.logconfig

    root = logging.getLogger()

    # ========== セットアップ（テスト前） ==========
    original_handlers = root.handlers[:]  # 元のハンドラーを保存
    original_level = root.level           # 元のレベルを保存

    # ハンドラーを削除
    for h in original_handlers:
        root.removeHandler(h)
        h.close()  # リソースクローズ

    # ロガーをリセット
    root.setLevel(logging.NOTSET)
    pokecode.logconfig._LOGGING_INITIALIZED = False  # ← 重要

    # ========== テスト実行 ==========
    yield  # ここでテスト関数が実行される

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

## 主要な概念

### 1. `@pytest.fixture(autouse=True)` の意味

| 属性 | 説明 |
|------|------|
| `autouse=True` | 各テスト関数を実行する前後に**自動実行** |
| `autouse=False` | テスト関数で明示的に引数として指定した時のみ実行 |

```python
# 例1: autouse=True （推奨：全テストで自動的に実行）
@pytest.fixture(autouse=True)
def reset_root_logger():
    yield

# テスト側で何も指定しなくても自動実行
def test_foo():
    setup_logging(...)  # reset_root_logger が自動的に前後で実行される
    assert log_file.exists()

# 例2: autouse=False （手動：テストごとに指定が必要）
@pytest.fixture
def my_fixture():
    yield

def test_bar(my_fixture):  # ← 明示的に指定
    assert True
```

### 2. `yield` で setup と teardown を分離

```python
def fixture_function():
    # ここから yield まで：テスト前の準備（setup）
    original_value = logger.level
    logger.setLevel(logging.NOTSET)

    yield  # ← テストがここで実行される

    # yield から終了まで：テスト後の復旧（teardown）
    logger.setLevel(original_value)
```

### 3. グローバルフラグのリセット

当プロジェクトで重要な点：

```python
pokecode.logconfig._LOGGING_INITIALIZED = False
```

logconfig.py は二重初期化防止のため `_LOGGING_INITIALIZED` フラグを使用：

```python
# logconfig.py より
_LOGGING_INITIALIZED = False

def setup_logging(..., force: bool = False) -> None:
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED and not force:
        return  # ← 既に初期化済みなら何もしない
```

**conftest で何もしない場合の問題：**
- テスト1実行 → `setup_logging()` が実行される → `_LOGGING_INITIALIZED = True`
- テスト2実行 → `setup_logging()` 呼び出し → フラグが `True` なので早期リターン
- テスト2のログファイルが作成されない ✗

**conftest でリセットする場合：**
- テスト1実行 → `reset_root_logger()` で `_LOGGING_INITIALIZED = False` にリセット
- テスト1テスト → `setup_logging()` 実行可能 ✓
- テスト2実行 → `reset_root_logger()` で `_LOGGING_INITIALIZED = False` にリセット
- テスト2テスト → `setup_logging()` 実行可能 ✓

## 実行フロー図

```
pytest 実行開始
    ↓
━━━━ テスト1 ━━━━
    ↓
conftest.reset_root_logger() の setup 部分
    - ハンドラー削除
    - フラグをリセット
    ↓
test_setup_logging_smoke() 実行
    - setup_logging() 呼び出し
    - ファイル作成確認
    ↓
conftest.reset_root_logger() の teardown 部分
    - ハンドラー削除
    - フラグをリセット
    ↓
━━━━ テスト2 ━━━━
    ↓
conftest.reset_root_logger() の setup 部分
    - ハンドラー削除
    - フラグをリセット
    ↓
test_setup_logging_creates_file() 実行
    - setup_logging() 呼び出し
    - ログメッセージ出力
    - ファイル存在確認
    ↓
conftest.reset_root_logger() の teardown 部分
    ↓
テスト完了
```

## conftest.py が必要な理由

### 問題パターン

| 場面 | 問題内容 |
|------|--------|
| conftest なし | テスト2以降でハンドラーが重複→ログが2重出力される |
| conftest なし | グローバルフラグがリセットされない→ `setup_logging()` が再実行されない |
| テスト内でリセット | 各テストが長くなる・重複コード増加 |

### conftest.py のメリット

```
✓ 全テストで自動的にテスト隔離が保証される
✓ テストコードから細かいセットアップ処理が隠蔽される
✓ 新規テスト追加時に conftest を意識せず書ける
✓ ロギングのリセット処理が一箇所に集約される
✓ 保守性が向上（仕様変更時の影響範囲が限定される）
```

## 実装時の注意点

### 必ずしておくこと

1. **ファイル名は `conftest.py`（正確に）**
   - ❌ `confest.py` （t が1個）→ pytest が認識しない
   - ✓ `conftest.py` （t が2個）→ pytest が自動認識

2. **各テスト前後でハンドラーをクローズ**
   ```python
   h.close()  # 重要：ファイルディスクリプタをリリース
   ```

3. **グローバルフラグをリセット**
   ```python
   pokecode.logconfig._LOGGING_INITIALIZED = False
   ```

### テストとの分離

conftest.py で定義したフィクスチャは、テスト側で何もしなくても自動実行されます：

```python
# tests/test_logconfig.py
def test_setup_logging_smoke(tmp_path):
    from pokecode.logconfig import setup_logging

    setup_logging(logdir=tmp_path, logname="test.log")
    # ↑ conftest の reset_root_logger が自動的に
    #   テスト前後で実行されている

    log_file = tmp_path / "test.log"
    assert log_file.exists()
```

## 応用：他のテストでの conftest 活用

conftest.py は以下のような用途でも使用できます：

```python
# テストデータベースのセットアップ
@pytest.fixture(autouse=True)
def setup_database():
    db = setup_test_db()
    yield
    teardown_test_db(db)

# 環境変数の一時設定
@pytest.fixture(autouse=True)
def set_test_env():
    original_env = os.environ.copy()
    os.environ['TEST_MODE'] = '1'
    yield
    os.environ.clear()
    os.environ.update(original_env)

# API モックサーバーの起動
@pytest.fixture(autouse=True)
def mock_api():
    server = start_mock_server()
    yield
    server.stop()
```

全てのテストで自動的に共通セットアップが実行されるため、テストコードがシンプルになります。

## まとめ

- **conftest.py** = pytest の共有設定ファイル
- **autouse=True** = 全テストで自動実行
- **yield** = テスト前後を `yield` で分離
- **ロガー隔離** = テスト間の干渉を防止
- **グローバルフラグ** = 重要な状態もリセット必須
