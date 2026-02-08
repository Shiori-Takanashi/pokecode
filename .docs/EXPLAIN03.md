# EXPLAIN03：解決策を検討する

**時刻：T3 | 状態：✓ 採択**

---

## 3つの解決策を検討

根本原因が判明したので、3つの選択肢を考えます。

## 選択肢1：テスト側でハンドラーをクリアする（✅ 採択）

### アイデア

pytest で各テスト実行前にハンドラーを削除する。

```python
@pytest.fixture(autouse=True)
def reset_logging():
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    yield
```

### メリット

```
✓ logconfig.py は本番要件に応じた設計を保持
✓ テストは自身の隔離を自分で管理
✓ 責務分離が明確
✓ モジュール間の密結合がない
```

### デメリット

```
✗ テスト側で手作業が必要
✗ 忘れると問題が発生（実装がない場合）
```

### 選択理由

**「ライブラリ関数は本番環境の要件で設計する」という原則に従う**

```
本番環境：
  main.py の最初で setup_logging() を1回呼ぶ
    ↓
  その後、何度も呼ぶことはない
    ↓
  if root.handlers: return は、誤った2回目呼び出しを防ぐ
    ↓
  正しい設計

テスト環境：
  各テストが独立した環境で実行する必要がある
    ↓
  テスト側でハンドラーをリセットする
    ↓
  これはテストの責務
    ↓
  logconfig.py が関知する必要なし
```

---

## 選択肢2：ガード機構を改善する（❌ 非採択）

### アイデア

「複数のログディレクトリに対応」する設計に変更

```python
def setup_logging(...) -> None:
    # 改善案1：ハンドラーを再設定可能にする
    # if root.handlers:
    #     return

    # 改善案2：force パラメータを追加
    # if _LOGGING_INITIALIZED and not force:
    #     return
```

### メリット

```
✓ logconfig.py 内で完結する解決
✓ テスト側が何もしなくてもいい
```

### デメリット

```
❌ 本番環境で誤った複数回呼び出しが発生した時
   ハンドラーが重複される

例：
main.py で誤ってこう書いた場合
    setup_logging()  # 呼び出し1
    do_something()
    setup_logging()  # 呼び出し2（誤りだが、条件により実行）

結果：
    root.handlers = [
        StreamHandler,      # 1回目
        TimedRotatingFileHandler,
        StreamHandler,      # 2回目（重複！）
        TimedRotatingFileHandler,
    ]

    ↓

ログが2倍出力される（同じメッセージが複数ハンドラーから）
    ↓
    本番バグ（デバッグが難しい）
```

### 選択しない理由

**「本番環境の安全性を損なう」ため**

---

## 選択肢3：グローバルフラグを使う（⚠️ 初期採択 → T5で廃止）

### アイデア

グローバルフラグで「初期化済み」を追跡

```python
_LOGGING_INITIALIZED = False

def setup_logging(..., force: bool = False) -> None:
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED and not force:
        return

    # ... セットアップ処理 ...

    _LOGGING_INITIALIZED = True
```

### 当初の評価

```
✓ 一見、良さそう
✓ ハンドラー削除と独立した状態管理
✓ テスト側では、フラグをリセットすれば良い
```

### conftest での使用方法

```python
# conftest.py
@pytest.fixture(autouse=True)
def reset_logging():
    import pokecode.logconfig

    root = logging.getLogger()

    # ハンドラーをリセット
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # グローバルフラグもリセット
    pokecode.logconfig._LOGGING_INITIALIZED = False

    yield
```

### この時点でのテスト結果

```
✓ 2 passed
```

「成功したから OK」と思いました。しかし...

→ [EXPLAIN04：conftest.py を導入する](EXPLAIN04.md)
