"""国名翻訳のデバッグスクリプト"""

import json
import logging

from pokecode.translation import TranslationService
from pokecode.logconfig import setup_logging
from pokecode.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def main():
    """result01.jsonの国名を翻訳してcountry_ja.jsonに保存する"""
    # ロギング設定
    setup_logging(logger=logger, level="INFO")

    # ファイルパス設定
    dirpath = PROJECT_ROOT / "output"
    dirpath.mkdir(exist_ok=True)
    input_file = dirpath / "country_en.json"
    output_file = dirpath / "country_ja.json"

    logger.info(f"入力ファイル: {input_file}")
    logger.info(f"出力ファイル: {output_file}")

    # JSONファイルを読み込む
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            countries = json.load(f)
        logger.info(f"読み込み完了: {len(countries)}件")
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {input_file}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"JSONの解析に失敗: {e!r}")
        return

    # 翻訳サービスを初期化
    service = TranslationService()

    # 翻訳実行
    logger.info("翻訳を開始します...")
    translated = service.translate_countries_batch(countries, batch_size=10)
    logger.info("翻訳完了")

    # JSONファイルに保存
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)
        logger.info(f"結果を保存: {output_file}")
    except Exception as e:
        logger.error(f"ファイルの保存に失敗: {e!r}")
        return

    # 統計情報を表示
    logger.info("=== 翻訳統計 ===")
    logger.info(f"総国数: {len(translated)}")
    translated_count = sum(
        1 for c in translated if c.get("country_name") != c.get("country_name_ja")
    )
    logger.info(f"翻訳された国: {translated_count}")


if __name__ == "__main__":
    main()
