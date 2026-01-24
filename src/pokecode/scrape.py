# pokecode/scrape.py
"""
HTML スクレイピングモジュール

このモジュールはHTMLテキストから必要な情報を抽出します。

主な機能:
1. HTMLパース
   - BeautifulSoup を使用した安全なHTMLパース
   - 不正なHTMLでも柔軟にパース可能
2. lang属性の抽出
   - <html lang="..."> からlang属性を取得
   - strict モードで厳格なバリデーション
3. 正規化
   - 抽出した値を標準形式に正規化（小文字化、トリム）

設計方針:
- BeautifulSoup の html.parser を使用（標準ライブラリで軽量）
- strict/non-strict モードで動作を切り替え可能
- エラーは ScrapeError にラップして上位に通知
- ログレベルで問題の深刻度を区別（ERROR/WARNING）
"""

import logging
from dataclasses import dataclass

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


# ============================================================
# カスタム例外: ScrapeError
# ============================================================
@dataclass(frozen=True)
class ScrapeError(RuntimeError):
    """HTMLスクレイピング時のエラーを表す例外

    Attributes:
        detail: エラーの詳細情報（何が見つからなかったか、何が不正だったか等）

    Note:
        frozen=True により immutable なデータクラスとして定義
        エラー情報の改ざんを防ぎ、安全性を確保
    """

    detail: str

    def __str__(self) -> str:
        """エラーメッセージを整形して返す

        ログ出力やデバッグ時に見やすい形式で表示されます。
        """
        return f"ScrapeError detail={self.detail}"


# ============================================================
# メイン関数: scrape_lang
# ============================================================
def scrape_lang(html: str, *, strict: bool = True) -> str:
    """
    HTMLから <html lang="..."> の lang 属性を抽出します。

    Args:
        html: パース対象のHTML文字列（通常は fetch_text の戻り値）
        strict: 厳格モード（デフォルト: True）
                True: lang属性が見つからない/不正な場合は ScrapeError を発生
                False: lang属性が見つからない/不正な場合は "unknown" を返す

    Returns:
        str: 正規化されたlang属性値（小文字、トリム済み）
             例: "en", "ja", "en-US", "zh-CN"
             strict=False の場合は "unknown" の可能性あり

    Raises:
        TypeError: html が str 型でない場合
        ScrapeError: strict=True でlang属性が見つからない、または不正な場合

    ログ出力方針:
        INFO: 処理開始時（HTMLサイズ）、成功時（取得したlang値）
        WARNING: strict=False でのlang属性欠損/不正
        ERROR: strict=True でのlang属性欠損/不正、パースエラー

    Examples:
        >>> html = '<html lang="en-US"><body>Hello</body></html>'
        >>> scrape_lang(html)
        'en-us'  # 小文字に正規化される
        >>>
        >>> html = '<html><body>No lang</body></html>'
        >>> scrape_lang(html, strict=False)
        'unknown'  # strict=False の場合
        >>> scrape_lang(html, strict=True)
        ScrapeError: ...  # strict=True の場合は例外

    Note:
        - lang属性は HTML5 で推奨される属性で、ページの主要言語を示す
        - SEO、アクセシビリティ、ブラウザの翻訳機能等で使用される
        - 形式は BCP 47 言語タグ（例: "en", "ja", "en-US", "zh-Hans-CN"）
    """
    # ============================================================
    # 入力バリデーション
    # ============================================================
    # 型チェック: html が str であることを保証
    # 理由: BeautifulSoup は bytes も受け付けるが、ここでは str に統一
    #       fetch_text が str を返すため、整合性を保つ
    if not isinstance(html, str):
        raise TypeError("html must be str")

    # 処理開始ログ（HTMLサイズを記録し、異常に大きい/小さいHTMLの検出に使用）
    logger.info("scrape_lang start html_len=%d", len(html))

    # ============================================================
    # BeautifulSoup でHTMLをパース
    # ============================================================
    # html.parser: Python標準ライブラリのパーサー（追加インストール不要）
    # 他の選択肢:
    #   - lxml: 高速だが別途インストールが必要
    #   - html5lib: HTML5準拠だが遅い
    # html.parser は標準的で十分な性能があるため採用
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        # パースエラー（非常に珍しいが、メモリ不足等で発生する可能性）
        # BeautifulSoup は非常に寛容なので、通常はエラーにならない
        logger.error("scrape_lang parse_failed err=%s", e)
        raise ScrapeError(detail=f"parse_failed: {e}") from e

    # ============================================================
    # <html> タグを検索
    # ============================================================
    # soup.find("html"): 最初の <html> タグを取得
    # 通常のHTMLでは <html> は必ず存在するが、以下の場合は None になる:
    #   - HTMLフラグメント（<html>タグがない部分的なHTML）
    #   - 非常に不正なHTML
    #   - 空文字列
    tag = soup.find("html")
    if tag is None:
        msg = "html tag not found"
        # strict モードによる処理の分岐
        if strict:
            # strict=True: エラーとして扱い、例外を発生
            # 用途: 正しいHTMLを期待している場合
            logger.error("scrape_lang %s", msg)
            raise ScrapeError(detail=msg)
        # strict=False: 警告を出して "unknown" を返す
        # 用途: HTMLフラグメントも許容する柔軟な処理
        logger.warning("scrape_lang %s", msg)
        return "unknown"

    # ============================================================
    # lang 属性を取得
    # ============================================================
    # tag.get("lang"): <html> タグの lang 属性値を取得
    # 戻り値:
    #   - 属性が存在する場合: 文字列（例: "en", "ja", "en-US"）
    #   - 属性が存在しない場合: None
    #   - 属性が空の場合: 空文字列 "" （例: <html lang="">）
    lang = tag.get("lang")

    # lang 属性が存在しないか空の場合のチェック
    # not lang: None または空文字列 "" の場合に True
    # not str(lang).strip(): 空白のみの場合に True（例: "   "）
    if not lang or not str(lang).strip():
        msg = "lang attribute not found or empty"
        # strict モードによる処理の分岐
        if strict:
            # strict=True: lang属性は必須として扱い、例外を発生
            # 用途: SEO分析等、lang属性が必ず必要な場合
            logger.error("scrape_lang %s", msg)
            raise ScrapeError(detail=msg)
        # strict=False: 警告を出して "unknown" を返す
        # 用途: lang属性がなくても処理を継続したい場合
        logger.warning("scrape_lang %s", msg)
        return "unknown"

    # ============================================================
    # lang 属性を正規化
    # ============================================================
    # 正規化の理由:
    #   1. 大文字小文字の統一（"EN" → "en", "Ja" → "ja"）
    #   2. 前後の空白除去（" en " → "en"）
    # こうすることで、後続の処理で比較や集計がしやすくなる
    #
    # str(lang): 万が一 lang が str 以外の型の場合も文字列化
    # .strip(): 前後の空白を除去
    # .lower(): 小文字に変換（BCP 47では大文字小文字は区別しない）
    lang_norm = str(lang).strip().lower()

    # 成功ログを出力（取得したlang値を記録）
    logger.info("scrape_lang ok lang=%s", lang_norm)
    return lang_norm
