# EXPLAIN05：グローバルフラグの問題に気づく

**時刻：T5 | 状態：⚠️ 警告**

---

## ユーザーからの指摘

実装後、ユーザーから以下の指摘を受けました：

> 「その書き方は『一見もっともらしいが、実務的には避けるべき』です。
>
> 理由は **管理対象が間違っている** 点です。」

---

## 「管理対象が間違っている」とは

### ❌ グローバルフラグで管理している現状

```python
# logconfig.py
_LOGGING_INITIALIZED = False  ← グローバルフラグ

def setup_logging(...) -> None:
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED and not force:
        return
    # ... セットアップ ...
    _LOGGING_INITIALIZED = True

# conftest.py
pokecode.logconfig._LOGGING_INITIALIZED = False  ← 外部から操作
```

### 管理対象は何か？

```
_LOGGING_INITIALIZED の値 = 「初期化済みか」という仮想的な状態
```

### 問題

```
仮想的な状態（フラグ） ≠ 物理的な事実（ハンドラーの存在）
```

---

## 具体例：隠れたバグシナリオ

### 不完全な conftest の場合

```python
# conftest.py（バグ版）
@pytest.fixture(autouse=True)
def reset_root_logger():
    import pokecode.logconfig

    root = logging.getLogger()

    # ハンドラーはリセットする
    for h in root.handlers[:]:
        root.removeHandler(h)

    # グローバルフラグのリセットを忘れた！
    # pokecode.logconfig._LOGGING_INITIALIZED = False  ← 実装漏れ

    yield
```

### 実行時に何が起こるか

```
テスト1 実行
├─ ハンドラー削除される
├─ _LOGGING_INITIALIZED は True のまま
├─ setup_logging() 呼び出し
├─ if _LOGGING_INITIALIZED and not force: → True
├─ 早期リターン（ハンドラー追加されない）
└─ ✗ テスト1失敗

理由：物理的には正しい（ハンドラーが空）
      だが、フラグが嘘をついている（True）
```

### 原因の追跡が難しい

```
開発者の視点：
「conftest でハンドラーをリセットしているのに、
 なぜ setup_logging() が実行されないんだ？」

バグ：実はフラグをリセットするのを忘れていた
      でも、ハンドラーをリセットしているから
      その関連箇所を見ない可能性
```

---

## グローバルフラグの本質的な問題

### 1. 二重管理

```
管理対象1：_LOGGING_INITIALIZED フラグ
管理対象2：root.handlers（実際のハンドラー）

この2つを同期させる必要がある
    ↓
複雑性が増す
    ↓
不整合のリスク
```

### 2. 密結合

```
logconfig.py 内部
├─ _LOGGING_INITIALIZED
└─ 非公開（本来）

conftest.py が外部からアクセス
    ↓
logconfig の実装変更が conftest に波及
```

### 3. 可視化が難しい

```
デバッグ時：
「_LOGGING_INITIALIZED は True だが、
 root.handlers は空。
 どっちが本当の状態？」
```

### 4. pytest 非互換（後で判明）

```
pytest 内部ハンドラー：
├─ _LiveLoggingNullHandler
├─ _FileHandler /dev/null
├─ LogCaptureHandler (x2)

pokecode ハンドラー：
├─ StreamHandler
└─ TimedRotatingFileHandler

フラグだけでは「どの」ハンドラーが対象か不明確
```

---

## 比較：物理的実体を直接見る

### ✓ ハンドラー（実体）で管理した場合

```python
# 管理対象 = ハンドラーの物理的存在
for handler in root.handlers:
    if isinstance(handler, TimedRotatingFileHandler):
        if Path(handler.baseFilename) == filepath:
            return  # 既に存在 → スキップ
```

### メリット

```
✓ グローバルフラグなし
✓ フラグと実体の同期不要
✓ デバッグが簡単（ハンドラーを見れば分かる）
✓ conftest が logconfig 内部に依存しない
✓ pytest のハンドラーと区別可能
```

---

## 実務での判断基準

### グローバルフラグが必要な場面

実務ではほぼない。以下は稀：

```
❌ 確実に単一インスタンス化が必要
   → ただし設計の方が悪い兆候

❌ パフォーマンス最適化が絶対
   → コストが本当に大きい場合のみ（でも構造を見直すべき）
```

### ハンドラー（実体）で十分な場面

実務の大部分：

```
✓ logging のような既存フレームワーク
  → 既に handlers リストで状態管理

✓ リソース管理全般
  → オブジェクトの存在を直接確認可能

✓ テスト隔離
  → 実体を削除すれば conftest 完結
```

---

## 教訓

> **「一見もっともらしい抽象化（グローバルフラグ）より、
> 物理的な実体（ハンドラー）を直接見る方が、
> 堅牢で保守性が高い」**

設計時に問う4つの質問：

1. **管理対象は何か？**
   - ハンドラー（実体）か、フラグ（抽象化）か

2. **外部から見えるか？**
   - デバッグ時に状態を確認できるか

3. **密結合していないか？**
   - モジュール内部に依存していないか

4. **テスト性は高いか？**
   - 仮想的な状態操作が必要ないか

→ [EXPLAIN06：pytest 内部ハンドラーの衝突を発見する](EXPLAIN06.md)
