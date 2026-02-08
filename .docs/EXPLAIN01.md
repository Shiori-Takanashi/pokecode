# EXPLAIN01：テスト失敗を発見する

**時刻：T1 | 状態：❌ 2 failed**

---

## 状況の説明

ログ設定のテストが失敗しました。

```
FAILED tests/test_logconfig.py::test_setup_logging_smoke - AssertionError: assert False
FAILED tests/test_logconfig.py::test_setup_logging_creates_file - AssertionError: assert False
```

## テストの中身を見る

### テスト1：基本的なセットアップ

```python
def test_setup_logging_smoke(tmp_path):
    from pokecode.logconfig import setup_logging

    setup_logging(logdir=tmp_path, logname="test.log")

    log_file = tmp_path / "test.log"
    assert log_file.exists()  # ← ここで失敗
```

**期待：** `setup_logging()` を呼び出したら、指定のディレクトリにログファイルが作成される

**実際：** ログファイルが作成されていない

### テスト2：ログ出力後のファイル確認

```python
def test_setup_logging_creates_file(tmp_path):
    from pokecode.logconfig import setup_logging
    import logging

    setup_logging(logdir=tmp_path, logname="test.log")

    logging.getLogger(__name__).info("hello")  # ← ログメッセージを出力

    assert (tmp_path / "test.log").exists()  # ← ここで失敗
```

**期待：** ログを出力したら、ファイルが作成される

**実際：** ファイルが作成されていない

## 当時の setup_logging() のコード

```python
def setup_logging(
    *,
    level: str = "INFO",
    logdir: Path | str = "logs",
    logname: str = "app.log",
) -> None:
    root = logging.getLogger()

    if root.handlers:
        return  # ← ここがポイント

    # 以下の処理は実行されない場合がある
    logdir: Path = Path(logdir)
    logdir.mkdir(exist_ok=True)
    filepath = logdir / logname

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
```

## ここから何を学ぶべきか

1. **テストが失敗するのは理由がある** - 単なる環境問題ではなく、設計の問題の可能性がある
2. **条件分岐を疑う** - `if root.handlers:` という条件が怪しい
3. **プロセス共有状態を考慮する** - Python のロギングはプロセス全体で共有される

## 次のステップ

このテスト失敗の原因を深掘りしていく必要があります。

→ [EXPLAIN02：根本原因を分析する](EXPLAIN02.md)
