# pokecode/main.py
import logging
import sys

from pokecode.scraping import (
    make_soup,
    scrape_tag_of_html,
    scrape_cards_from_html,
    scrape_correct_card,
    # scrape_trainers,
    # scrape_code,
    scrape_selection,
    scrape_options,
    scrape_country,
    get_country_without_extra_chars,
)
from pokecode.request_html import request_html
from pokecode.logconfig import setup_logging
from pokecode.loading import load_config
from pokecode import config
from pokecode.paths import PYPROJECT
from pokecode.io_writing import save_json


def main() -> None:
    logger = logging.getLogger("pokecode")
    setup_logging(logger=logger, level="INFO")

    logger.info("Application Start.")

    try:
        load_config(PYPROJECT)
        url = config.get_url()

        html = request_html(url=url)
        logger.info("HTML retrieved: %d characters", len(html))
        soup = make_soup(html)
        html = scrape_tag_of_html(soup)
        cards = scrape_cards_from_html(html)
        card_of_filter = scrape_correct_card(cards, "🔍 Filter Friend Codes")
        selection = scrape_selection(card_of_filter)
        options = scrape_options(selection)
        countires = [scrape_country(option) for option in options]
        countires_without_extra_chars = [
            result
            for country in countires
            if (result := get_country_without_extra_chars(country)) is not None
        ]

        # card_of_qr = scrape_correct_card(cards, "📱 Friend Codes")
        # trainers = scrape_trainers(card_of_qr)
        # codes = [scrape_code(trainer) for trainer in trainers]

        # コードを保存
        output_file = config.get_output_file(suffix="02")
        save_json(countires_without_extra_chars, output_file)
        logger.info("Codes saved to: %s", output_file)

    except Exception:
        logger.exception("Unhandled exception")
        sys.exit(1)

    finally:
        logger.info("Application End.")


if __name__ == "__main__":
    main()
