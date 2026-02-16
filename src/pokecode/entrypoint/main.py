# pokecode/main.py


def main() -> None:
    pass


if __name__ == "__main__":
    main()


# import logging
# import sys
# import json
# from pathlib import Path

# from pokecode.scraping import (
#     make_soup,
#     scrape_html,
#     scrape_cards_from_html,
#     scrape_correct_card,
#     # scrape_trainers,
#     # scrape_code,
#     scrape_selection,
#     scrape_options,
#     scrape_country,
#     get_country_without_extra_chars,
#     scrape_trainers,
#     scrape_friend_code_from_trainer,
# )
# from pokecode.request_html import request_html
# from pokecode.logconfig import setup_logging

# # from pokecode.loading import load_config
# from pokecode.url_builder import (
#     build_url_with_code,
# )
# from pokecode.config.env import ConfigGetter

# # from pokecode.paths import PYPROJECT
# from pokecode.io_writing import save_json
# from pokecode.translate_service import (
#     TranslationService,
# )


# def main() -> None:
#     """ポケモンGOフレンドコード収集のメイン処理。

#     この関数は以下の処理フローを実行する：

#     1. ロガーのセットアップとアプリケーション開始ログの出力

#     2. 設定ファイル (pyproject.toml) の読み込みと ConfigGetter の初期化

#     3. ドメインのトップページから国コードのリストを取得
#        - HTMLをリクエストしてBeautifulSoupでパース
#        - "🔍 Filter Friend Codes" カードからselectタグを探索
#        - optionタグから国名とISO Alpha-3コードを抽出
#        - 余分な文字（絵文字など）を除去して正規化

#     4. 英語の国コードリストを country_en.json として保存

#     5. 翻訳処理
#        - TranslationService を使用して国名を日本語に翻訳
#        - バッチサイズ10でキャッシュを利用しながら翻訳
#        - 英語の国名キーを削除して country_ja.json として保存

#     6. 日本固有のデータ処理
#        - all_process() で日本のフレンドコードデータを処理
#        - japanese.json として保存

#     7. 各国のフレンドコードページURLの生成
#        - ISO Alpha-3コードを使用してURLを構築
#        - urls.json として保存

#     8. 各国のフレンドコード収集（現在は最初のURLのみ実行してbreak）
#        - 各URLにアクセスして "📱 Friend Codes" カードを取得
#        - トレーナー情報からフレンドコードを抽出
#        - 空文字列でないコードのみをフィルタリング
#        - URLの末尾3文字（国コード）をファイル名として保存

#     エラー処理：
#     - すべての例外を catch して logger.exception でログ出力
#     - sys.exit(1) でエラー終了

#     Raises:
#         ValueError: URLの末尾が3文字でない場合（国コード取得失敗）
#         その他、各関数内で発生する可能性のある例外
#             - RuntimeError: HTMLパース失敗
#             - TypeError: 期待する要素の型が不正
#             - 各種HTTPエラーやネットワークエラー

#     Note:
#         現在はフレンドコード収集ループの最初でbreakしているため、
#         実際には1つの国のデータのみを取得している。
#         全国のデータを取得する場合はbreakを削除する必要がある。
#     """
#     logger = logging.getLogger("pokecode")
#     setup_logging(logger=logger, level="DEBUG")

#     logger.info("Application Start.")

#     try:
#         # load_config(PYPROJECT)
#         cget = ConfigGetter()
#         domain = cget.get_domain()

#         html = request_html(url=domain)
#         logger.info(
#             "HTML retrieved: %d characters",
#             len(html),
#         )
#         soup = make_soup(html)
#         html_element = scrape_html(soup)
#         cards = scrape_cards_from_html(html_element)
#         card_of_filter = scrape_correct_card(cards, "🔍 Filter Friend Codes")
#         select = scrape_selection(card_of_filter)
#         options = scrape_options(select)
#         countires = [scrape_country(option) for option in options]
#         countires_without_extra_chars = [
#             result
#             for country in countires
#             if (result := get_country_without_extra_chars(country)) is not None
#         ]

#         codes_in_iso_alpha3 = [
#             cs.get("iso_alpha3", None) for cs in countires_without_extra_chars
#         ]

#         logger.debug(f"code_in_iso_alpha3: {len(codes_in_iso_alpha3)}")

#         # コードを保存
#         country_path: Path = cget.get_output_file("country_en", "json")
#         save_json(
#             countires_without_extra_chars,
#             country_path,
#         )
#         logger.info("Codes saved to: %s", country_path)

#         with open(country_path, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         ts = TranslationService()

#         translated = ts.translate_countries_batch(
#             countries=data,
#             ignore_cache=False,
#             batch_size=10,
#         )
#         for elm in translated:
#             elm.pop("country_en", None)

#         translated_path: Path = cget.get_output_file("country_ja", "json")

#         save_json(translated, translated_path)
#         logger.info(
#             "Translated result saved to: %s",
#             translated_path,
#         )


#         save_json(result_of_jp, cget.get_output_file("japanese", "json"))

#         urls_with_code = [
#             build_url_with_code(code=c)
#             for c in codes_in_iso_alpha3
#             if c is not None
#         ]

#         save_json(
#             urls_with_code,
#             cget.get_output_file("urls", "json"),
#         )

#         for url in urls_with_code:
#             res = request_html(url)
#             soup = make_soup(res)
#             html_element = scrape_html(soup)
#             cards = scrape_cards_from_html(html_element)
#             card = scrape_correct_card(cards, "📱 Friend Codes")
#             trainers = scrape_trainers(card)
#             friends_codes = [
#                 scrape_friend_code_from_trainer(trainer)
#                 for trainer in trainers
#                 if scrape_friend_code_from_trainer(trainer) != ""
#             ]
#             try:
#                 code = url[-3:]
#             except Exception:
#                 raise ValueError("codeが3文字ではない。")
#             save_json(
#                 friends_codes,
#                 cget.get_output_file(f"{code}", "json"),
#             )
#             break

#     except Exception:
#         logger.exception("Unhandled exception")
#         sys.exit(1)

#     finally:
#         logger.info("Application End.")
