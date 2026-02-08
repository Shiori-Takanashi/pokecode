# EXPLAIN02：根本原因を分析する

**時刻：T2 | 状態：🔍 分析中**

---

## 「なぜ root.handlers をチェックするのか」の背景

最初に `setup_logging()` が作られた時、設計者の思考は以下のようでした：

```
「ロギングの初期化は1回だけで十分」
    ↓
「2回目以降の呼び出しは何もしない」
    ↓
「ハンドラーが既にあれば、初期化済み」
    ↓
if root.handlers: return
```

これは **本番アプリケーション（単一プロセス）** では完全に正しい設計です。

```
main.py
    ↓
setup_logging()  ← 1回だけ呼ぶ
    ↓
if root.handlers:
    return  ← ハンドラーが既にあれば、スキップ

（以後、ハンドラーは変わらない）
```

## しかし、pytest は違う環境

pytest ではテストが複数実行されます：

```
pytest 実行開始
    ↓
━━━ テスト1 ━━━
├─ setup_logging(logdir=tmp_path1, logname="test.log") 呼び出し
├─ if root.handlers: → False（最初は空）
├─ ハンドラー追加される ✓
└─ ログファイル作成される ✓

→ テスト1終了、ロガーはそのまま
（ハンドラーは削除されない！）

━━━ テスト2 ━━━
├─ setup_logging(logdir=tmp_path2, logname="test.log") 呼び出し
├─ if root.handlers: → True（テスト1のハンドラーが残っている）
├─ 早期リターン ✗
├─ ハンドラーが追加されない ✗
└─ 別のディレクトリへログファイルが作成されない ✗

→ テスト2終了
```

## 実験で確認してみた

Python シェルで2回連続呼び出し：

```python
from pathlib import Path
import tempfile
from pokecode.logconfig import setup_logging
import logging

# テスト1
with tempfile.TemporaryDirectory() as tmp1:
    tmp_path1 = Path(tmp1)
    setup_logging(logdir=tmp_path1, logname='test1.log')

    root = logging.getLogger()
    print(f'After test1: handlers={len(root.handlers)}')
    # 出力：handlers=2（StreamHandlerと TimedRotatingFileHandler）

# テスト2（別のディレクトリ）
with tempfile.TemporaryDirectory() as tmp2:
    tmp_path2 = Path(tmp2)
    setup_logging(logdir=tmp_path2, logname='test2.log')

    root = logging.getLogger()
    print(f'After test2: handlers={len(root.handlers)}')
    # 出力：handlers=2（テスト1のハンドラーがまだある）

    print(f'File exists: {(tmp_path2 / "test2.log").exists()}')
    # 出力：File exists: False  ← ファイルが作成されない！
```

## 問題の本質

| 項目 | 本番環境 | pytest |
|------|--------|-------|
| **実行形態** | 単一プロセス | 複数テストが同じプロセス内で実行 |
| **setup_logging() 呼び出し** | 1回（app起動時） | 各テストで複数回 |
| **ロギングの共有** | プロセス全体で共有 | テスト間でハンドラーが残存 |
| **if root.handlers の効果** | ✓ 意図通り（スキップ） | ✗ 副作用（後続テスト失敗） |

## まとめ

**「ハンドラーが存在する = 初期化済み」という仮定は、テスト環境では通用しない。**

```
テスト1のハンドラー + テスト2のハンドラー要件 ≠ 一致
```

次に、この問題をどう解決するかを検討します。

→ [EXPLAIN03：解決策を検討する](EXPLAIN03.md)
