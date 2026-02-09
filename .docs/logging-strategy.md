# ログ戦略: 日付ベースのファイル名を使用

## 概要

このプロジェクトでは、非常駐プロセス（短時間で終了するスクリプト）向けのログ戦略として、**日付ベースのファイル名 + FileHandler** を採用しています。

## 背景

### 従来の問題（TimedRotatingFileHandler）

`TimedRotatingFileHandler` は常駐プロセス向けに設計されており、非常駐プロセスでは以下の問題があります：

```
2/2: 実行 → app.log に記録
2/3: 実行なし → ローテーションされない
2/4: 実行なし → ローテーションされない
2/5: 実行 → app.log には 2/2 と 2/5 の内容が混在
         → ローテーション時に app.log.2026-02-05 にリネーム
```

**問題点**:
- 異なる日付のログが同じファイルに混在する
- 実行しない日のログファイルが作られない（これは仕方ない）
- ファイル名と内容の日付が一致しない可能性がある

## 採用した解決策

### 日付ベースのファイル名 + FileHandler

実行時に実行日の日付をファイル名に含めることで、確実に日付ごとにログファイルを分離します。

```python
from datetime import datetime
from logging import FileHandler

def setup_logging(
    *,
    logger: Logger,
    level: str = "INFO",
    logdir_name: str = "logs",
    logname: str = "app",
) -> None:
    """
    logger をセットアップ

    実行日ごとに自動的に別ファイルにログを記録
    例: app.log.2026-02-06
    """
    # 実行日の日付を含むファイル名を生成
    logname = f"{logname}.log.{datetime.now():%Y-%m-%d}"
    filepath = _resolve_logfile(logdir_name=logdir_name, logname=logname)

    # ...フォーマッター設定など...

    # FileHandler（シンプルなファイル出力）
    fh = FileHandler(filepath, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
```

### メリット

1. **確実な日付分離**: 実行日ごとに必ず別ファイルが作られる
2. **シンプル**: ローテーション処理が不要
3. **予測可能**: ファイル名と内容の日付が必ず一致
4. **トラブルシューティングが容易**: 特定の日のログを確実に見つけられる

### ファイル例

```
logs/
  app.log.2026-02-03
  app.log.2026-02-05
  app.log.2026-02-06
```

各ファイルにはその日に実行したログのみが含まれます。

## 古いログファイルの管理

ログファイルは無制限に増え続けるため、定期的なクリーンアップが必要です。

### 手動削除

```bash
# 30日より古いログを削除
find logs/ -name "app.log.*" -mtime +30 -delete
```

### cronで自動削除

```cron
# 毎日午前3時に古いログを削除
0 3 * * * find /path/to/pokecode/logs/ -name "app.log.*" -mtime +30 -delete
```

### Python スクリプトで削除

```python
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_old_logs(logdir: Path, days: int = 30):
    """指定日数より古いログファイルを削除"""
    cutoff = datetime.now() - timedelta(days=days)

    for logfile in logdir.glob("app.log.*"):
        if logfile.stat().st_mtime < cutoff.timestamp():
            logfile.unlink()
            print(f"Deleted: {logfile}")
```

## 注意事項

- 1日に複数回実行しても同じファイルに追記される（append モード）
- 日をまたいで実行すると、0時以降のログは新しいファイルに記録される
- ログファイル名の日付はスクリプト起動時の日付（ログ出力時刻ではない）

## 代替案との比較

| 方式 | 日付分離 | シンプルさ | 適用場面 |
|------|---------|-----------|---------|
| 日付ベースファイル名 + FileHandler | ✅ 確実 | ✅ 非常にシンプル | 非常駐プロセス（推奨） |
| TimedRotatingFileHandler | ⚠️ 不確実 | △ ローテーション処理あり | 常駐プロセス |
| RotatingFileHandler | ❌ サイズベース | △ ローテーション処理あり | サイズ制限が必要な場合 |

## まとめ

非常駐プロセスでは、日付ベースのファイル名を使用することで、シンプルかつ確実にログを日付ごとに分離できます。古いログファイルの管理は別途実装する必要がありますが、全体として保守性の高い設計となります。
