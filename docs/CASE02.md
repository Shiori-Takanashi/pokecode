# CASE02：StreamHandler 増殖の根本原因と修正

**目的：Case01で発見したStreamHandler増殖問題の根本原因を特定し、修正方法を詳細に解説**

---

## 問題の背景

Case01で確認したように、テスト実行ごとに StreamHandler が増殖する現象が発生していました。
しかし、実装されていた`logconfig.py`にはすでに**早期リターンチェック**が存在していました。

```python
# logconfig.py の既存実装（問題あり）
for handler in root.handlers:
    if isinstance(handler, TimedRotatingFileHandler):
        if Path(handler.baseFilename) == filepath:
            return  # ← ここで関数を終了するはず
```

なぜこのチェックが機能していなかったのか？

---

## 根本原因：パス比較の失敗

### 問題のあるコード

```python
filepath = logdir / logname  # 例：Path("logs") / "app.log" = Path("logs/app.log")
# ...
if Path(handler.baseFilename) == filepath:
    return
```

### 何が起こっていたか

#### シナリオ 1：相対パスと絶対パスの混在

| 項目 | 値 | 説明 |
|------|-----|------|
| `filepath` | `logs/app.log` | **相対パス** |
| `handler.baseFilename` | `/home/tani09/snk-projects/pokecode/logs/app.log` | **絶対パス** |
| 比較結果 | **False** ❌ | 見た目は同じでも型が違う |

```python
>>> Path("logs/app.log") == Path("/home/tani09/snk-projects/pokecode/logs/app.log")
False  # ← 比較失敗！
```

#### シナリオ 2：実際の実行結果

```
[Before setup_logging] All handlers: 4
[After 1st setup_logging] All handlers: 6      ← StreamHandler + TimedRotatingFileHandler が追加
[After 2nd setup_logging] All handlers: 8      ← さらに追加される！（チェックが機能していない）
```

ハンドラー数が増え続けるのは、**パス比較が常に False で、early return が実行されないため**です。

---

## 修正方法

### 修正前のコード

```python
for handler in root.handlers:
    if isinstance(handler, TimedRotatingFileHandler):
        if Path(handler.baseFilename) == filepath:  # ❌ 相対/絶対パスの比較が失敗
            return
```

### 修正後のコード

```python
# 既に同じファイルパスのハンドラーが存在するかチェック
for handler in root.handlers:
    if isinstance(handler, TimedRotatingFileHandler):
        if Path(handler.baseFilename).resolve() == filepath.resolve():  # ✅ 両方を絶対パスに統一
            return
```

### 何が変わったか

| 方式 | コード | 結果 |
|------|--------|------|
| **修正前** | `Path("logs/app.log") == Path("/home/.../logs/app.log")` | **False** ❌ |
| **修正後** | `Path("logs/app.log").resolve() == Path("logs/app.log").resolve()` | **True** ✅ |

`.resolve()` メソッドの効果：

```python
>>> Path("logs/app.log").resolve()
PosixPath('/home/tani09/snk-projects/pokecode/logs/app.log')

>>> Path("/home/tani09/snk-projects/pokecode/logs/app.log").resolve()
PosixPath('/home/tani09/snk-projects/pokecode/logs/app.log')

>>> Path("logs/app.log").resolve() == Path("/home/tani09/snk-projects/pokecode/logs/app.log").resolve()
True  # ✅ 一致する！
```

---

## 修正後の動作

### テスト実行結果

修正後、同じテストを実行すると：

```
[Before setup_logging] All handlers: 4
[After 1st setup_logging] All handlers: 6      ← StreamHandler + TimedRotatingFileHandler が追加
[After 2nd setup_logging] All handlers: 6      ← ✅ ハンドラーが追加されない（重複防止）
MSG出力時：1回表示  ✅ StreamHandlerが1つのみ
```

重要なポイント：

| 実行順序 | ハンドラー数 | StreamHandler 出力 | 説明 |
|---------|-----------|------------------|------|
| 1回目 setup | 6 | 1回 | StreamHandler を1つ追加 |
| 2回目 setup | **6** ✅ | 1回 ✅ | 既存を検出して追加しない |
| 3回目 setup | **6** ✅ | 1回 ✅ | 既存を検出して追加しない |

---

## なぜこの修正が必要だったのか

### Python の Path オブジェクトの動作

```python
from pathlib import Path

# 相対パスのまま比較
p1 = Path("logs/app.log")
p2 = Path("/home/tani09/snk-projects/pokecode/logs/app.log")
print(p1 == p2)  # False - 絶対パス・相対パスが混在している

# 両方を絶対パスに統一
p1_resolved = p1.resolve()
p2_resolved = p2.resolve()
print(p1_resolved == p2_resolved)  # True ✅
```

### 実務での教訓

ファイルパスの比較を行う際は：

1. **常に絶対パスに統一する** (`.resolve()` を使用)
2. **相対パスと絶対パスの混在を避ける**
3. **symlinks や .. などのパス正規化を考慮する** (`.resolve()` が自動処理)

---

## 修正の影響範囲

### logconfig.py での変更

```python
def setup_logging(
    *,
    level: str = "INFO",
    logdir: Path | str = "logs",
    logname: str = "app.log",
) -> None:
    root = logging.getLogger()
    logdir: Path = Path(logdir)
    filepath = logdir / logname

    # 既に同じファイルパスのハンドラーが存在するかチェック
    for handler in root.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            if Path(handler.baseFilename).resolve() == filepath.resolve():  # ← 修正
                return

    # ... 以降のコードは変わらない
```

### 動作の変化

修正により、以下の問題が解決されました：

| 問題 | 原因 | 修正後 |
|------|------|--------|
| StreamHandler の増殖 | パス比較失敗で early return 不実行 | パス比較が正しく動作 |
| ログの重複出力 | ハンドラーの重複 | ハンドラーの重複がない |
| テストの信頼性低下 | 実行ごとに異なる動作 | 安定した動作 |

---

## まとめ

**根本原因**
- `Path("相対パス") == Path("絶対パス")` は常に False になる
- early return チェックが機能せず、ハンドラーが重複追加される

**修正方法**
- `.resolve()` メソッドで両方を絶対パスに統一してから比較

**結果**
- StreamHandler の増殖が完全に防止される
- テストの実行結果が安定する
- ハンドラーの重複が発生しない
