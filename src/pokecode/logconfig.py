# pokecode/logconfig.py
"""
ロギング設定モジュール

このモジュールはアプリケーション全体のロギング設定を一元管理します。

主な機能:
1. ルートロガーの初期化
   - ログレベルの設定
   - ログフォーマットの統一
2. マルチハンドラー設定
   - コンソール出力（開発時のリアルタイム確認用）
   - ファイル出力（運用時の記録保管用、ローテーション付き）
3. 外部ライブラリのログ制御
   - requests, urllib3 等の冗長なログを抑制

設計方針:
- setup_logging() はアプリケーション起動時に1回だけ呼ぶ
- 二重初期化を防ぐガード機構を実装
- 全モジュールで統一されたログフォーマットを使用
- ログローテーションでディスク容量を管理

ログレベルの使い分け:
- DEBUG: 詳細なデバッグ情報（開発時のみ有効化）
- INFO: 通常の処理フロー（開始、成功、主要なステップ）
- WARNING: 警告（リトライ、非推奨機能の使用等）
- ERROR: エラー（処理失敗、例外発生）
- CRITICAL: 致命的エラー（アプリケーション全体に影響）
"""

import logging
import sys
from pathlib import Path
import shutil
import tomllib
from logging.handlers import RotatingFileHandler

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def convert_str_to_path_under_project_root(name: str) -> Path:
    if "/" or r"\\" in name:
        raise ValueError("arg is invalid.")
    cwd: Path = Path(__file__)
    project_root: Path = cwd.parents[2]
    return project_root / name


def define_path_of_logfile(logdir: str, basename: str) -> Path:
    if "/" in basename:
        raise ValueError("basename is invalid.")
    if r"\\" in basename:
        raise ValueError("basename is invalid.")

    project = Path(__file__).parents[2]
    dirpath = project / logdir
    if not dirpath.exists():
        raise NotADirectoryError("directory is not found.")
    for p in dirpath.glob("app*.log"):
        suffix = p.stem.removeprefix("app")
        if suffix.isdigit():
            pass
    return


def convert_str_to_path_from_project_root(name: str) -> Path:
    project_root = Path(__file__).parents[2].resolve(strict=True)
    return project_root / name


def mklogdir(dirpath: str) -> None:
    """_summary_
    引数の名前通りのディレクトリを、project_rootに作成する。

    Args:
        logdir (str): logを格納するディレクトリ名。../などを含む、エラー対応は未実装。
    """
    if dirpath.exists():
        shutil.rmtree(dirpath)
    dirpath.mkdir(parents=True, exist_ok=False)


def loading_config() -> dict:
    pyproject = Path("pyptoject.toml")
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return data["tool"]["pokecode"]


# ============================================================
# メイン関数: setup_logging
# ============================================================
def setup_logging(
    *, level: str = "INFO", logdirname: str = "logs", logfilename: str = "app.log"
) -> None:
    """
    アプリケーション全体のロギング設定を初期化します。

    Args:
        level: ログレベル文字列（デフォルト: "INFO"）
               "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" から選択
               大文字小文字は区別しない（内部で .upper() される）
        logfile: ログファイルのパス（デフォルト: "app.log"）
                 相対パスの場合はカレントディレクトリに作成
                 絶対パスも指定可能

    Returns:
        None

    Note:
        - この関数はアプリケーション起動時（main関数の最初）に1回だけ呼ぶこと
        - 複数回呼ばれても二重初期化は発生しない（ガード機構あり）
        - ログファイルは RotatingFileHandler により自動的にローテーションされる

    Examples:
        >>> # 基本的な使用例（INFO レベル、app.log に出力）
        >>> setup_logging()
        >>>
        >>> # デバッグモード（DEBUG レベル、debug.log に出力）
        >>> setup_logging(level="DEBUG", logfile="debug.log")
        >>>
        >>> # 本番環境（WARNING レベル以上のみ記録）
        >>> setup_logging(level="WARNING", logfile="/var/log/app/app.log")
    """
    # ============================================================
    # ルートロガーの取得と二重初期化防止
    # ============================================================
    # logging.getLogger(): 引数なしで呼ぶとルートロガーを取得
    # ルートロガー: 全てのロガーの親であり、全モジュールのログを統括
    root = logging.getLogger()

    # 二重初期化防止ガード
    # 理由: setup_logging() が複数回呼ばれると、ハンドラーが重複して追加され、
    #       同じログが複数回出力される問題が発生
    # hasHandlers() ではなく handlers を直接チェックする理由:
    #   - hasHandlers() は親ロガーのハンドラーもチェックするため
    #   - ここでは「このルートロガー自身」にハンドラーがあるかだけを確認したい
    if root.handlers:
        # 既にハンドラーが設定済みなら何もせず終了
        return

    # ============================================================
    # ログレベルの設定
    # ============================================================
    # 文字列からログレベル定数に変換
    # level="INFO" → logging.INFO (= 20)
    # getattr() を使用する理由:
    #   - 動的に属性を取得できる
    #   - 不正な文字列が渡された場合もデフォルト値（logging.INFO）で安全に動作
    # 例: getattr(logging, "DEBUG", logging.INFO) → logging.DEBUG
    #     getattr(logging, "INVALID", logging.INFO) → logging.INFO
    resolved_level = getattr(logging, level.upper(), logging.INFO)

    # ルートロガーのレベルを設定
    # これにより、このレベル以上のログのみが処理される
    # 例: INFO に設定すると、DEBUG ログは無視される
    root.setLevel(resolved_level)

    # ============================================================
    # ログフォーマットの定義
    # ============================================================
    # 統一されたフォーマットにより、ログの可読性と解析性を向上
    #
    # フォーマット文字列の各要素:
    #   %(asctime)s: ログ出力時刻（例: 2026-01-23 10:30:45）
    #   %(levelname)-5s: ログレベル（左寄せ5文字、例: "INFO ", "ERROR"）
    #                    -5s により "INFO" と "ERROR" が桁揃えされる
    #   %(name)s: ロガー名（通常はモジュール名、例: "pokecode.fetch"）
    #   %(funcName)s: ログを出力した関数名（例: "fetch_text"）
    #   %(lineno)d: ログを出力した行番号（例: 42）
    #   %(message)s: ログメッセージ本体
    #
    # 出力例:
    #   2026-01-23 10:30:45 [INFO ] pokecode.fetch fetch_text:42: fetch start url=...
    fmt = "%(asctime)s [%(levelname)-5s] %(name)s %(funcName)s:%(lineno)d: %(message)s"

    # 日時フォーマット（ISO 8601形式の簡略版）
    # %Y: 4桁の年、%m: 2桁の月、%d: 2桁の日
    # %H: 2桁の時、%M: 2桁の分、%S: 2桁の秒
    datefmt = "%Y-%m-%d %H:%M:%S"

    # フォーマッターオブジェクトを作成
    # 全てのハンドラーで同じフォーマッターを使用することで、
    # コンソールとファイルで一貫したログ形式を維持
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # ============================================================
    # ハンドラー1: 標準出力（コンソール）
    # ============================================================
    # StreamHandler: ログをストリーム（ファイルライクオブジェクト）に出力
    # sys.stdout: 標準出力（コンソール）
    #
    # 用途:
    #   - 開発時: リアルタイムでログを確認
    #   - 本番環境: systemd や Docker のログ収集機構に連携
    #
    # Note: sys.stderr を使う選択肢もあるが、stdout の方が
    #       パイプやリダイレクトで扱いやすいため stdout を採用
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)

    # ============================================================
    # ハンドラー2: ファイル出力（ローテーション付き）
    # ============================================================
    # RotatingFileHandler: ファイルサイズに基づいて自動ローテーション
    #
    # パラメータ:
    #   logfile: ログファイルのパス（例: "app.log"）
    #   maxBytes: ローテーションのしきい値（2_000_000 = 2MB）
    #             ファイルサイズがこの値を超えると新しいファイルに切り替わる
    #   backupCount: 保持する世代数（3世代）
    #                app.log, app.log.1, app.log.2, app.log.3 が保持される
    #                最古のファイル（app.log.3）は削除される
    #   encoding: ファイルのエンコーディング（"utf-8"）
    #             日本語等のマルチバイト文字を正しく記録
    #
    # ローテーションの動作:
    #   1. app.log が 2MB を超える
    #   2. app.log → app.log.1 にリネーム
    #   3. app.log.1 → app.log.2 にリネーム
    #   4. app.log.2 → app.log.3 にリネーム
    #   5. app.log.3 は削除される
    #   6. 新しい app.log が作成される
    #
    # メリット:
    #   - ディスク容量の管理（最大 2MB × 4ファイル = 8MB に制限）
    #   - 古いログは自動削除（手動メンテナンス不要）
    #   - ログファイルが巨大化してエディタで開けなくなる問題を回避

    # try:
    #     parts = logfile.split(".")
    # except Exception as e:
    #     raise RuntimeError(f"logfile is invalid: {e}")
    # if len(parts) != 2:
    #     raise RuntimeError(f"logfile is invalid: '.' is {len(parts)}, but must 1.")

    # name, extension = parts

    # dirpath = convert_str_to_path_from_project_root(logdirname)
    # if dirpath.exists():
    #     shutil.rmtree(dirpath)
    # filepath = convert_str_to_path_from_project_root(f"{logdirname}/{logfilename}")

    fileh = RotatingFileHandler(
        filepath,
        maxBytes=2_000_000,
        backupCount=99,
        encoding="utf-8",
    )
    fileh.setFormatter(formatter)

    # ============================================================
    # ハンドラーの登録
    # ============================================================
    # ルートロガーに両方のハンドラーを追加
    # これにより、全てのログが:
    #   1. コンソールに出力される
    #   2. ファイルに記録される
    # という二重出力が実現される
    root.addHandler(stream)
    root.addHandler(fileh)

    # ============================================================
    # 外部ライブラリのログレベル調整
    # ============================================================
    # 問題: requests や urllib3 は DEBUG レベルで非常に冗長なログを出力
    #       - 全HTTPリクエストの詳細（ヘッダー、ボディ等）
    #       - 接続プールの状態
    #       - SSL/TLS ハンドシェイク情報
    #
    # 対策: これらのライブラリのログレベルを WARNING に引き上げ
    #       これにより、重要な警告やエラーのみが出力される
    #
    # Note: アプリケーション全体が DEBUG レベルでも、
    #       これらのライブラリは WARNING 以上のみ出力される
    #
    # カスタマイズ:
    #   - HTTP通信のデバッグが必要な場合は logging.DEBUG に変更
    #   - 他のライブラリ（bs4等）も騒がしい場合は同様に設定を追加
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
