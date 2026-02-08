# pokecode/main.py
import logging
import sys
import json
from pathlib import Path

from pokecode.scraping import (
    make_soup,
    scrape_html,
    scrape_cards_from_html,
    scrape_correct_card,
    # scrape_trainers,
    # scrape_code,
    scrape_selection,
    scrape_options,
    scrape_country,
    get_country_without_extra_chars,
    scrape_trainers,
    scrape_friend_code_from_trainer,
)
from pokecode.request_html import request_html
from pokecode.logconfig import setup_logging
from pokecode.loading import load_config
from pokecode.url_builder import (
    build_url_with_code,
)
from pokecode.config import ConfigGetter
from pokecode.paths import PYPROJECT
from pokecode.io_writing import save_json
from pokecode.translation import (
    TranslationService,
)
from pokecode.transfer_json import all_process


def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="DEBUG")

    logger.info("Application Start.")

    try:
        load_config(PYPROJECT)
        cget = ConfigGetter()
        domain = cget.get_domain()

        html = request_html(url=domain)
        logger.info(
            "HTML retrieved: %d characters",
            len(html),
        )
        soup = make_soup(html)
        html = scrape_html(soup)
        cards = scrape_cards_from_html(html)
        card_of_filter = scrape_correct_card(cards, "🔍 Filter Friend Codes")
        select = scrape_selection(card_of_filter)
        options = scrape_options(select)
        countires = [scrape_country(option) for option in options]
        countires_without_extra_chars = [
            result
            for country in countires
            if (result := get_country_without_extra_chars(country)) is not None
        ]

        codes_in_iso_alpha3 = [
            cs.get("iso_alpha3", None) for cs in countires_without_extra_chars
        ]

        logger.debug(f"code_in_iso_alpha3: {len(codes_in_iso_alpha3)}")

        # コードを保存
        country_path: Path = cget.get_output_file("country_en")
        save_json(
            countires_without_extra_chars,
            country_path,
        )
        logger.info("Codes saved to: %s", country_path)

        with open(country_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        ts = TranslationService()

        translated = ts.translate_countries_batch(
            countries=data,
            ignore_cache=False,
            batch_size=10,
        )
        for elm in translated:
            elm.pop("country_en", None)

        translated_path: Path = cget.get_output_file("country_ja")

        save_json(translated, translated_path)
        logger.info(
            "Translated result saved to: %s",
            translated_path,
        )

        result_of_jp = all_process()
        save_json(result_of_jp, cget.get_output_file("japanese"))

        urls_with_code = [
            build_url_with_code(code=c)
            for c in codes_in_iso_alpha3
            if c is not None
        ]

        # for u in urls_with_code:
        #     logger.debug(u)

        save_json(
            urls_with_code,
            cget.get_output_file("urls"),
        )

        for url in urls_with_code:
            res = request_html(url)
            soup = make_soup(res)
            html = scrape_html(soup)
            cards = scrape_cards_from_html(html)
            card = scrape_correct_card(cards, "📱 Friend Codes")
            trainers = scrape_trainers(card)
            friends_codes = [
                scrape_friend_code_from_trainer(trainer)
                for trainer in trainers
                if scrape_friend_code_from_trainer(trainer) != ""
            ]
            try:
                code = url[-3:]
            except Exception:
                raise ValueError("codeが3文字ではない。")
            save_json(
                friends_codes,
                cget.get_output_file(f"{code}"),
            )
            break

    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)

    finally:
        logger.info("Application End.")


if __name__ == "__main__":
    main()
