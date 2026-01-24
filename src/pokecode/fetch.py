# pokecode/fetch.py
"""
HTTP リクエスト処理モジュール

このモジュールは HTTP GET リクエストを実行し、レスポンステキストを取得します。

主な機能:
1. リトライ機能付きの堅牢なHTTP GET
   - ネットワーク障害や一時的なサーバーエラーに対してリトライ
   - 指数バックオフでリトライ間隔を調整
2. タイムアウト制御
   - 長時間の待機を防ぎ、レスポンシブな動作を保証
3. 詳細なロギング
   - 各リクエストの開始、成功、失敗を記録
   - パフォーマンスメトリクス（経過時間、バイト数）を記録

設計方針:
- requests ライブラリを使用（HTTP/HTTPS、プロキシ、認証等の標準機能を活用）
- エラーは FetchError にラップして上位に通知（スタックトレースは内部でログ記録）
- リトライ中の一時的エラーは WARNING、最終失敗は ERROR としてログ出力
"""

import logging
import time
from dataclasses import dataclass

import requests


logger = logging.getLogger(__name__)


# ============================================================
# カスタム例外: FetchError
# ============================================================
@dataclass(frozen=True)
class FetchError(RuntimeError):
    """HTTP取得時のエラーを表す例外

    Attributes:
        url: エラーが発生したURL
        detail: エラーの詳細情報（例外メッセージ、ステータスコード等）

    Note:
        frozen=True により immutable なデータクラスとして定義
        これにより、エラー情報が変更されないことを保証
    """

    url: str
    detail: str

    def __str__(self) -> str:
        """エラーメッセージを整形して返す

        ログ出力時やデバッグ時に見やすい形式で表示されます。
        """
        return f"FetchError url={self.url} detail={self.detail}"


# ============================================================
# メイン関数: fetch_text
# ============================================================
def fetch_text(
    url: str,
    *,
    timeout: float = 10.0,
    retries: int = 2,
    backoff: float = 0.5,
) -> str:
    """
    HTTP GET でHTMLなどのテキストを取得します（リトライ機能付き）

    Args:
        url: 取得対象のURL（http:// または https://）
        timeout: 1回のリクエストのタイムアウト秒数（デフォルト: 10.0秒）
                 サーバーからのレスポンスがこの時間内に開始されない場合はタイムアウト
        retries: リトライ回数（デフォルト: 2回）
                 初回 + retries 回の試行を行う（retries=2 なら最大3回試行）
        backoff: リトライ間隔の基本値（秒）（デフォルト: 0.5秒）
                 実際の待機時間は backoff * attempt で計算（指数バックオフ）
                 例: 1回目失敗 → 0.5秒待機、2回目失敗 → 1.0秒待機

    Returns:
        str: レスポンスボディのテキスト（通常はHTML）

    Raises:
        ValueError: retries が負の値の場合
        FetchError: HTTP取得に失敗した場合（全リトライが失敗後）

    ログ出力方針:
        INFO: リクエスト開始時、成功時（ステータスコード、経過時間、バイト数を記録）
        WARNING: リトライ発生時（何回目の試行か、エラー内容を記録）
        ERROR: 全リトライ失敗時（最終的なエラー内容を記録）

    Examples:
        >>> # 基本的な使用例
        >>> html = fetch_text("https://example.com")
        >>>
        >>> # タイムアウトを短く、リトライを増やす場合
        >>> html = fetch_text("https://slow-server.com", timeout=5.0, retries=5)

    Note:
        - requests.get() を使用しているため、プロキシや認証等の設定も可能
        - 一時的なネットワーク障害（DNS解決失敗、接続タイムアウト等）には
          リトライで対応できる可能性が高い
        - 4xx エラー（404等）もリトライするが、通常は改善しない
          （用途に応じてリトライ条件のカスタマイズを検討）
    """
    if retries < 0:
        raise ValueError("retries must be >= 0")

    logger.info("fetch start url=%s timeout=%.1fs retries=%d", url, timeout, retries)

    # 最後に発生した例外を保持（デバッグ用）
    last_exc: Exception | None = None

    # ============================================================
    # リトライループ（初回 + retries 回の試行）
    # ============================================================
    # 例: retries=2 の場合、range(1, 4) → 1, 2, 3 の3回試行
    for attempt in range(1, retries + 2):
        # パフォーマンス計測開始（perf_counter は高精度タイマー）
        # time.time() よりも精度が高く、システムクロックの調整の影響を受けない
        t0 = time.perf_counter()

        try:
            # ============================================================
            # HTTP GET リクエストを実行
            # ============================================================
            # timeout: connect timeout + read timeout の合計
            # requests.get() は以下の処理を実行:
            #   1. DNS解決
            #   2. TCP接続確立
            #   3. HTTPリクエスト送信
            #   4. HTTPレスポンス受信（ヘッダー + ボディ）
            res = requests.get(url, timeout=timeout)

            # ステータスコードのチェック
            # 4xx（クライアントエラー）、5xx（サーバーエラー）の場合は例外を発生
            # 200番台、300番台は正常として扱われる
            res.raise_for_status()

            # レスポンスボディをテキストとして取得
            # requests は Content-Type ヘッダーや chardet ライブラリを使って
            # 自動的に適切なエンコーディングを推測して decode する
            text = res.text

            # ============================================================
            # 成功時の処理
            # ============================================================
            # 経過時間を計算（ミリ秒精度）
            elapsed = time.perf_counter() - t0

            # 成功ログを出力（運用監視やパフォーマンス分析に有用）
            # status=%d: HTTPステータスコード（通常は200）
            # elapsed=%.3fs: リクエストの経過時間（ネットワーク遅延の監視に使用）
            # bytes=%d: レスポンスのバイト数（UTF-8エンコード後）
            #           データ転送量の監視や、異常な大きさのレスポンスの検出に使用
            logger.info(
                "fetch ok url=%s status=%d elapsed=%.3fs bytes=%d",
                url,
                res.status_code,
                elapsed,
                len(text.encode("utf-8", errors="ignore")),
            )
            # 取得したテキストを返して正常終了
            return text

        except requests.RequestException as e:
            # ============================================================
            # エラー発生時の処理
            # ============================================================
            # requests.RequestException: requests ライブラリの全エラーの基底クラス
            # 以下のようなエラーを包括的にキャッチ:
            #   - ConnectionError: ネットワーク接続失敗（DNS解決失敗、接続拒否等）
            #   - Timeout: タイムアウト
            #   - HTTPError: 4xx, 5xx ステータスコード（raise_for_status() により発生）
            #   - TooManyRedirects: リダイレクトが多すぎる

            # 失敗時も経過時間を記録（どの段階で失敗したかの分析に使用）
            elapsed = time.perf_counter() - t0
            # 最後に発生した例外を保持（万が一ループを抜けた場合のフォールバック用）
            last_exc = e

            # ============================================================
            # リトライ判定
            # ============================================================
            # まだリトライ可能な回数が残っている場合
            if attempt <= retries + 1 and attempt <= retries + 1:
                # WARNING レベルでリトライログを出力
                # ここでは logger.exception() を使わない理由:
                #   - スタックトレースを出すと冗長になる
                #   - リトライで成功する可能性があるため、まだエラー確定ではない
                #   - 最終失敗時に ERROR レベルで記録する
                logger.warning(
                    "fetch retry url=%s attempt=%d/%d elapsed=%.3fs err=%s",
                    url,
                    attempt,  # 現在の試行回数
                    retries + 1,  # 最大試行回数
                    elapsed,
                    e,  # エラー内容（型や簡潔なメッセージ）
                )

                # 次のリトライまで待機（指数バックオフ）
                # 理由: サーバー側の一時的な過負荷の場合、時間をおくことで回復する可能性
                # 計算例（backoff=0.5の場合）:
                #   attempt=1: 0.5秒待機
                #   attempt=2: 1.0秒待機
                #   attempt=3: 1.5秒待機
                if attempt <= retries:
                    time.sleep(backoff * attempt)
                # continue でループの先頭に戻り、再試行
                continue

            # ============================================================
            # 最終失敗（全リトライが失敗）
            # ============================================================
            # ERROR レベルで最終失敗を記録
            logger.error(
                "fetch failed url=%s attempts=%d elapsed=%.3fs err=%s",
                url,
                retries + 1,  # 実際に試行した回数
                elapsed,  # 最後の試行の経過時間
                e,
            )
            # FetchError にラップして上位に例外を伝播
            # from e により例外チェーンを保持（デバッグ時に元の例外を追跡可能）
            raise FetchError(url=url, detail=str(e)) from e

    # ここに来るのは想定外
    raise FetchError(url=url, detail=str(last_exc) if last_exc else "unknown error")
