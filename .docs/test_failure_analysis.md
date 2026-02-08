# テスト失敗の分析レポート

## テスト実行結果

```
FAILED tests/test_logconfig.py::test_setup_logging_smoke - AssertionError: assert False
FAILED tests/test_logconfig.py::test_setup_logging_creates_file - AssertionError: assert False
```

## 失敗の概要

両テストともログファイルが作成されていない。
- `test_setup_logging_smoke`: `setup_logging()` 実行後、ログファイルが存在しない
- `test_setup_logging_creates_file`: ログ出力後もファイルが存在しない

## 根本原因

`setup_logging()` 関数の**二重初期化防止ガード機構**が、テスト隔離の面で問題を引き起こしている。

### 現在のコード（logconfig.py）

```python
def setup_logging(...) -> None:
    root = logging.getLogger()

    if root.handlers:
        return  # ← 問題箇所

    # 以下の処理は実行されない
    logdir: Path = Path(logdir)
    logdir.mkdir(exist_ok=True)
    filepath = logdir / logname

    fileh = TimedRotatingFileHandler(...)
    root.addHandler(stream)
    root.addHandler(fileh)
```

### 問題の詳細

1. **最初のテスト実行時**
   - `root.handlers` が空 → ガード機構をスキップ
   - ハンドラーが正常に追加される
   - ログファイルが作成される ✓

2. **次のテスト実行時**（pytest で `test_setup_logging_creates_file` が実行される）
   - 前回の実行からルートロガーが生きている
   - `root.handlers` に前回のハンドラーが残存している
   - **ガード機構により早期リターン**
   - 新しいログファイル（`test2.log`）のハンドラーが追加されない
   - ファイルが作成されない ✗

### 検証実験

連続で2回 `setup_logging()` を呼び出した結果：

```
First call - Temp dir: /tmp/tmpmcu7uhqq
First call - Root handlers: 2

Second call - Temp dir: /tmp/tmpdh0w74ji
Second call - Root handlers: 2
Second call - File exists: False  ← ファイルが作成されない
```

## 解決方法

### オプション1: テストでロガーを初期化（現在のコードで対応）

テストファイルで各テスト前にハンドラーをクリア：

```python
@pytest.fixture(autouse=True)
def reset_logging():
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    yield
```

### オプション2: ガード機構の改善（推奨）

現在のガード機構を改善して、複数の異なるログディレクトリに対応：

```python
def setup_logging(...) -> None:
    root = logging.getLogger()

    # ← 現在：全体的に二重初期化を防ぐ
    # if root.handlers:
    #     return

    # 改善案：既に設定済みの場合のみ終了
    # または、各ハンドラーを管理してハンドラーの再設定を可能に
```

### オプション3: 設定フラグの使用

```python
_LOGGING_INITIALIZED = False

def setup_logging(...) -> None:
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED:
        return

    # ... setup処理 ...

    _LOGGING_INITIALIZED = True
```

## 実務的な最適解：オプション1（テスト側でハンドラーをクリア）

### 推奨理由

1. **ライブラリ関数として適切**
   - `setup_logging()` は提供側のライブラリとして設計
   - 呼び出し側（テスト側）で隔離を管理するのが責務分離として正しい
   - ライブラリ側は「単一プロセスでの複数初期化」に対応しなくてよい

2. **本番環境への影響がゼロ**
   - 本番コード（app.py等）では `setup_logging()` は1回だけ呼ぶ
   - ガード機構は本番環境で有効に機能（意図通り）
   - テスト専用の fixture で対応するため、本番ロジックに手を入れない

3. **テストの責務として明確**
   - テストが自身の隔離性を管理するのが基本原則
   - pytest fixture で「テスト前にロガーをリセット」という意図が明示的
   - 将来のメンテナンス時に何をしているか理解しやすい

4. **実装コストが最小**
   - ライブラリコード（logconfig.py）への変更なし
   - テストファイルに5行程度の fixture 追加のみ

### 実装例

```python
# tests/conftest.py (新規作成、または既存に追加)

import logging
import pytest

@pytest.fixture(autouse=True)
def reset_logging():
    """各テスト実行前にルートロガーをリセット"""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    yield
    # テスト後もクリア（オプション）
    for handler in root.handlers[:]:
        root.removeHandler(handler)
```

これでテスト実行時にはハンドラーが毎回初期化された状態でスタート。

---

## 非推奨な選択肢

### オプション2（ガード機構の改善）が非推奨な理由

```python
# 改善案として考えた内容
if root.handlers:
    return  # ← これを削除する
```

- **本番環境で問題発生のリスク**
  - `main()` を誤って複数回呼んだ時、ハンドラーが重複追加される
  - ログが2倍、3倍出力される（同じメッセージが複数ハンドラーから出力）
  - 本番でのバグ報告につながる可能性

- **設計意図が曖昧になる**
  - ガード機構を削除すると「複数回初期化に対応する」という新しい要件が発生
  - 各ハンドラーを追跡・管理する複雑さが増す

### オプション3（グローバルフラグ）が非推奨な理由

```python
_LOGGING_INITIALIZED = False

def setup_logging(...) -> None:
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return
    # ...
```

- **本質的な問題は解決していない**
  - オプション2と同じく、複数回初期化を禁止するだけ
  - テストの隔離性問題は残存

- **テスト難易度が上がる**
  - グローバルフラグをリセットするために、`importlib.reload()` や `sys.modules` 操作が必要
  - テストコードが複雑になり、脆弱性が増す

---

## 結論

現在の実装では、**単一の長期間実行プロセス**（アプリケーション本体）での使用を想定しており、複数回の初期化を想定していない。これは正しい設計。

テスト隔離を実現するには **pytest の conftest.py に fixture を追加** するのが、実務的・保守的に最適な解決策。
